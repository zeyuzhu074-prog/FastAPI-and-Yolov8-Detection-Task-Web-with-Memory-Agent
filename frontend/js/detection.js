/* ============================================================
   图片 / 视频检测页逻辑
   ============================================================ */
(function () {
    "use strict";

    const params = new URLSearchParams(location.search);
    let mode = params.get("mode") === "video" ? "video" : "image";

    const CONFIG = {
        image: {
            title: "图片检测",
            sub: "上传航拍图片，自动识别并标注目标",
            hint: "支持 JPG / JPEG / PNG，最大 500 MB",
            exts: [".jpg", ".jpeg", ".png"],
            accept: ".jpg,.jpeg,.png",
            media: "image",
            endpoint: "/api/detection/image",
            icon: "image"
        },
        video: {
            title: "视频检测",
            sub: "上传航拍视频，逐帧识别并生成标注视频",
            hint: "支持 MP4 / AVI / MOV / MKV，最大 500 MB",
            exts: [".mp4", ".avi", ".mov", ".mkv"],
            accept: ".mp4,.avi,.mov,.mkv",
            media: "video",
            endpoint: "/api/detection/video",
            icon: "video"
        }
    };

    const MAX_MB = 500;
    const user = App.init({
        active: mode,
        title: CONFIG[mode].title,
        subtitle: "目标检测工作台"
    });
    if (!user) return;

    const uid = user.user_id;

    const el = {
        pageTitle: document.getElementById("pageTitle"),
        pageSub: document.getElementById("pageSub"),
        uploadSub: document.getElementById("uploadSub"),
        dropHint: document.getElementById("dropHint"),
        dropzone: document.getElementById("dropzone"),
        fileInput: document.getElementById("fileInput"),
        fileRow: document.getElementById("fileRow"),
        fileTypeBadge: document.getElementById("fileTypeBadge"),
        fileName: document.getElementById("fileName"),
        fileSize: document.getElementById("fileSize"),
        clearBtn: document.getElementById("clearBtn"),
        detectBtn: document.getElementById("detectBtn"),
        progressBox: document.getElementById("progressBox"),
        progressText: document.getElementById("progressText"),
        progressBar: document.getElementById("progressBar"),
        progressTime: document.getElementById("progressTime"),
        previewBox: document.getElementById("previewBox"),
        previewSub: document.getElementById("previewSub"),
        downloadBtn: document.getElementById("downloadBtn"),
        metrics: document.getElementById("metrics"),
        classPanel: document.getElementById("classPanel"),
        classBars: document.getElementById("classBars"),
        classMeta: document.getElementById("classMeta"),
        detectionPanel: document.getElementById("detectionPanel"),
        detectionBody: document.getElementById("detectionBody"),
        detectionMeta: document.getElementById("detectionMeta"),
        resultSub: document.getElementById("resultSub"),
        recordBadge: document.getElementById("recordBadge")
    };

    let selectedFile = null;
    let localUrl = null;
    let resultUrl = null;
    let currentRecordId = null;
    let timerHandle = null;

    function revoke(url) {
        if (url) URL.revokeObjectURL(url);
    }

    function applyMode() {
        const cfg = CONFIG[mode];
        el.pageTitle.textContent = cfg.title;
        el.pageSub.textContent = cfg.sub;
        el.uploadSub.textContent = cfg.hint;
        el.dropHint.textContent = cfg.hint;
        el.fileInput.setAttribute("accept", cfg.accept);
        document.querySelectorAll("#modeSwitch .segmented__item").forEach(function (b) {
            b.classList.toggle("is-active", b.getAttribute("data-mode") === mode);
        });
    }

    function setPlaceholder(icon, text) {
        el.previewBox.innerHTML =
            '<div class="preview__placeholder"><i data-lucide="' + icon + '"></i>' +
            "<span>" + App.escapeHtml(text) + "</span></div>";
        App.icons();
    }

    function setPreviewMedia(url, kind) {
        el.previewBox.innerHTML = "";
        const node = document.createElement(kind === "video" ? "video" : "img");
        node.src = url;
        if (kind === "video") {
            node.controls = true;
            node.playsInline = true;
        } else {
            node.alt = "检测结果";
        }
        el.previewBox.appendChild(node);
    }

    function resetResult() {
        revoke(resultUrl);
        resultUrl = null;
        currentRecordId = null;
        el.downloadBtn.disabled = true;
        el.recordBadge.classList.add("hidden");
        el.resultSub.textContent = "完成一次检测后展示统计信息";
        el.metrics.innerHTML =
            '<div class="empty" style="grid-column:1/-1">' +
            '<i data-lucide="scan-search"></i>' +
            '<div class="empty__title">暂无检测结果</div>' +
            '<div class="empty__hint">上传文件并开始检测后，这里会显示目标数量与类别分布</div></div>';
        el.classPanel.classList.add("hidden");
        el.detectionPanel.classList.add("hidden");
        el.classBars.innerHTML = "";
        el.detectionBody.innerHTML = "";
        App.icons();
    }

    function pickFile(file) {
        const cfg = CONFIG[mode];
        const lower = (file.name || "").toLowerCase();
        const okExt = cfg.exts.some(function (e) { return lower.endsWith(e); });
        if (!okExt) {
            App.toast("不支持的格式，仅支持：" + cfg.exts.join(" / "), "warn");
            return;
        }
        if (file.size > MAX_MB * 1024 * 1024) {
            App.toast("文件大小不能超过 " + MAX_MB + " MB", "warn");
            return;
        }

        selectedFile = file;
        revoke(localUrl);
        localUrl = URL.createObjectURL(file);

        el.fileName.textContent = file.name;
        el.fileSize.textContent = App.bytes(file.size);
        el.fileTypeBadge.innerHTML =
            '<i data-lucide="' + cfg.icon + '"></i>' + (mode === "image" ? "图片" : "视频");
        el.fileRow.classList.remove("hidden");
        el.detectBtn.disabled = false;

        resetResult();
        setPreviewMedia(localUrl, cfg.media);
        el.previewSub.textContent = "已选择文件，点击「开始检测」执行推理";
        App.icons();
    }

    function clearFile() {
        selectedFile = null;
        revoke(localUrl);
        localUrl = null;
        el.fileInput.value = "";
        el.fileRow.classList.add("hidden");
        el.detectBtn.disabled = true;
        el.progressBox.classList.add("hidden");
        resetResult();
        setPlaceholder(CONFIG[mode].media === "video" ? "video" : "image", "暂无预览内容");
        el.previewSub.textContent = "检测完成后在此查看标注结果";
    }

    /* ---------- 交互绑定 ---------- */

    document.querySelectorAll("#modeSwitch .segmented__item").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const target = btn.getAttribute("data-mode");
            if (target === mode) return;
            location.href = "detection.html?mode=" + target;
        });
    });

    el.dropzone.addEventListener("click", function () { el.fileInput.click(); });
    el.fileInput.addEventListener("change", function () {
        if (el.fileInput.files && el.fileInput.files[0]) pickFile(el.fileInput.files[0]);
    });
    el.clearBtn.addEventListener("click", clearFile);

    ["dragenter", "dragover"].forEach(function (evt) {
        el.dropzone.addEventListener(evt, function (e) {
            e.preventDefault();
            el.dropzone.classList.add("is-over");
        });
    });
    ["dragleave", "drop"].forEach(function (evt) {
        el.dropzone.addEventListener(evt, function (e) {
            e.preventDefault();
            el.dropzone.classList.remove("is-over");
        });
    });
    el.dropzone.addEventListener("drop", function (e) {
        const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
        if (file) pickFile(file);
    });

    /* ---------- 结果渲染 ---------- */

    function normaliseClasses(classStatistics) {
        if (!classStatistics) return [];
        return Object.keys(classStatistics).map(function (key) {
            const item = classStatistics[key] || {};
            return { class_name: item.class_name || key, count: item.count || 0 };
        }).sort(function (a, b) { return b.count - a.count; });
    }

    function renderMetrics(items) {
        el.metrics.innerHTML = items.map(function (m) {
            return (
                '<div class="metric"><div class="metric__label">' + App.escapeHtml(m.label) +
                '</div><div class="metric__value">' + App.escapeHtml(m.value) + "</div></div>"
            );
        }).join("");
    }

    function renderClasses(list) {
        if (!list.length) {
            el.classPanel.classList.add("hidden");
            return;
        }
        el.classPanel.classList.remove("hidden");
        const total = list.reduce(function (s, c) { return s + c.count; }, 0);
        const max = list[0].count || 1;
        el.classMeta.textContent = "共 " + list.length + " 类 · " + total + " 个目标";
        el.classBars.innerHTML = list.map(function (c, i) {
            const pct = Math.max(2, Math.round((c.count / max) * 100));
            const color = App.CHART_COLORS[i % App.CHART_COLORS.length];
            return (
                '<div class="classbar__row">' +
                '<div class="classbar__name" title="' + App.escapeHtml(c.class_name) + '">' +
                App.escapeHtml(c.class_name) + "</div>" +
                '<div class="classbar__track"><div class="classbar__fill" style="width:' + pct +
                "%;background:" + color + '"></div></div>' +
                '<div class="classbar__value">' + App.formatNumber(c.count) + "</div></div>"
            );
        }).join("");
    }

    function renderDetections(detections) {
        if (!Array.isArray(detections) || !detections.length) {
            el.detectionPanel.classList.add("hidden");
            return;
        }
        el.detectionPanel.classList.remove("hidden");
        el.detectionMeta.textContent = "共 " + detections.length + " 个目标";
        const limit = 300;
        el.detectionBody.innerHTML = detections.slice(0, limit).map(function (d, i) {
            const b = d.bbox || {};
            const coord = [b.x1, b.y1, b.x2, b.y2].map(function (v) {
                return v === undefined ? "-" : v;
            }).join(", ");
            const conf = typeof d.confidence === "number" ? d.confidence.toFixed(3) : d.confidence;
            return (
                "<tr><td class='num'>" + (i + 1) + "</td>" +
                "<td>" + App.escapeHtml(d.class_name) + "</td>" +
                "<td class='num'>" + App.escapeHtml(conf) + "</td>" +
                "<td class='mono' style='color:var(--ink-3)'>" + App.escapeHtml(coord) + "</td></tr>"
            );
        }).join("") + (detections.length > limit
            ? '<tr><td colspan="4" class="muted">仅展示前 ' + limit + " 个目标，完整数据请下载结果文件</td></tr>"
            : "");
    }

    async function loadResultMedia(recordId, mediaKind) {
        const res = await fetch(App.downloadUrl(recordId, uid));
        if (!res.ok) throw new Error("结果文件获取失败");
        const blob = await res.blob();
        const typed = new Blob([blob], {
            type: mediaKind === "video" ? "video/mp4" : "image/jpeg"
        });
        return URL.createObjectURL(typed);
    }

    /* ---------- 进度 ---------- */

    function startProgress(label) {
        const start = Date.now();
        el.progressBox.classList.remove("hidden");
        el.progressText.innerHTML = '<span class="spinner spinner--dark"></span>' + App.escapeHtml(label);
        el.progressBar.style.width = "8%";
        let pct = 8;
        timerHandle = setInterval(function () {
            const secs = Math.round((Date.now() - start) / 1000);
            el.progressTime.textContent = secs + "s";
            if (pct < 92) {
                pct += Math.max(0.4, (92 - pct) * 0.03);
                el.progressBar.style.width = pct.toFixed(1) + "%";
            }
        }, 220);
    }

    function stopProgress(done) {
        clearInterval(timerHandle);
        timerHandle = null;
        el.progressBar.style.width = "100%";
        if (done) {
            setTimeout(function () { el.progressBox.classList.add("hidden"); }, 500);
        }
    }

    function setBusy(busy) {
        el.detectBtn.disabled = busy || !selectedFile;
        el.clearBtn.disabled = busy;
        el.dropzone.style.pointerEvents = busy ? "none" : "";
        el.dropzone.style.opacity = busy ? ".6" : "";
    }

    /* ---------- 检测 ---------- */

    el.detectBtn.addEventListener("click", async function () {
        if (!selectedFile) return;
        const cfg = CONFIG[mode];

        resetResult();
        setBusy(true);
        setPreviewMedia(localUrl, cfg.media);
        el.previewSub.textContent = "推理中，请稍候…";
        startProgress(mode === "image" ? "正在执行图片推理" : "正在逐帧处理视频，请耐心等待");

        const form = new FormData();
        form.append("file", selectedFile, selectedFile.name);

        try {
            const res = await App.api(cfg.endpoint, {
                method: "POST",
                query: { user_id: uid },
                body: form
            });
            const data = res.data || res;
            currentRecordId = data.record_id;

            stopProgress(true);

            // 载入标注结果
            resultUrl = await loadResultMedia(currentRecordId, cfg.media);
            setPreviewMedia(resultUrl, cfg.media);
            el.previewSub.textContent = mode === "image"
                ? "标注结果已生成"
                : "标注视频已生成，可播放查看";

            // 统计信息
            if (mode === "image") {
                renderMetrics([
                    { label: "检测目标", value: App.formatNumber(data.objects) },
                    { label: "推理耗时", value: App.formatSeconds(data.inference_time) },
                    { label: "图片尺寸", value: (data.width || "-") + " × " + (data.height || "-") },
                    { label: "类别数量", value: App.formatNumber(Object.keys(data.class_statistics || {}).length) }
                ]);
            } else {
                renderMetrics([
                    { label: "检测目标", value: App.formatNumber(data.object_count) },
                    { label: "处理帧数", value: App.formatNumber(data.frame_count) },
                    { label: "单帧最多", value: App.formatNumber(data.max_objects_in_frame) },
                    { label: "平均每帧", value: data.average_objects_per_frame },
                    { label: "推理耗时", value: App.formatSeconds(data.inference_time) },
                    { label: "视频尺寸", value: (data.width || "-") + " × " + (data.height || "-") },
                    { label: "帧率", value: (data.fps || "-") + " FPS" }
                ]);
            }

            renderClasses(normaliseClasses(data.class_statistics));
            if (mode === "image") renderDetections(data.detections);

            el.recordBadge.textContent = "记录 #" + currentRecordId;
            el.recordBadge.classList.remove("hidden");
            el.resultSub.textContent = "检测完成 · " + App.formatDateTime(new Date().toISOString());
            el.downloadBtn.disabled = false;
            App.toast(mode === "image" ? "图片检测完成" : "视频检测完成", "ok");
        } catch (err) {
            stopProgress(false);
            el.progressBox.classList.add("hidden");
            el.previewSub.textContent = "检测失败";
            App.toast(err.message, "err");
        } finally {
            setBusy(false);
        }
    });

    el.downloadBtn.addEventListener("click", function () {
        if (currentRecordId) {
            window.open(App.downloadUrl(currentRecordId, uid), "_blank");
        }
    });

    applyMode();
    resetResult();
    App.icons();
})();
