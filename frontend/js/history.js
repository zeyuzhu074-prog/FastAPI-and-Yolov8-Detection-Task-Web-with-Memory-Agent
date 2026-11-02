/* ============================================================
   历史记录页逻辑：列表、筛选、分页、详情
   ============================================================ */
(function () {
    "use strict";

    const user = App.init({
        active: "history",
        title: "历史记录",
        subtitle: "历史检测任务查询"
    });
    if (!user) return;

    const uid = user.user_id;
    const state = { page: 1, pageSize: 10, taskType: "", pages: 1, total: 0 };

    const el = {
        body: document.getElementById("historyBody"),
        empty: document.getElementById("historyEmpty"),
        countBadge: document.getElementById("countBadge"),
        pagerInfo: document.getElementById("pagerInfo"),
        prevBtn: document.getElementById("prevBtn"),
        nextBtn: document.getElementById("nextBtn"),
        refreshBtn: document.getElementById("refreshBtn"),
        historySub: document.getElementById("historySub")
    };

    function pick(res) {
        return res && res.data !== undefined ? res.data : res;
    }

    const STATUS = {
        completed: { cls: "badge--ok", text: "已完成" },
        processing: { cls: "badge--warn", text: "处理中" },
        failed: { cls: "badge--err", text: "失败" }
    };

    function typeBadge(type) {
        if (type === "video") {
            return '<span class="badge badge--video"><i data-lucide="video"></i>视频</span>';
        }
        return '<span class="badge badge--image"><i data-lucide="image"></i>图片</span>';
    }

    function statusBadge(status) {
        const s = STATUS[status] || { cls: "", text: status || "-" };
        return '<span class="badge ' + s.cls + '">' + App.escapeHtml(s.text) + "</span>";
    }

    function renderRows(items) {
        if (!items.length) {
            el.body.innerHTML = "";
            document.querySelector("#historyBody").closest(".table-wrap").classList.add("hidden");
            el.empty.classList.remove("hidden");
            App.icons();
            return;
        }
        document.querySelector("#historyBody").closest(".table-wrap").classList.remove("hidden");
        el.empty.classList.add("hidden");

        el.body.innerHTML = items.map(function (r) {
            return (
                "<tr>" +
                '<td class="num">' + r.id + "</td>" +
                "<td>" + typeBadge(r.task_type) + "</td>" +
                '<td class="name" title="' + App.escapeHtml(r.original_name) + '">' +
                App.escapeHtml(r.original_name) + "</td>" +
                '<td class="muted">' + App.escapeHtml(r.model_name || "-") + "</td>" +
                "<td>" + statusBadge(r.status) + "</td>" +
                '<td class="num">' + App.formatNumber(r.object_count || 0) + "</td>" +
                '<td class="num">' + App.formatSeconds(r.inference_time) + "</td>" +
                '<td class="muted">' + App.formatDateTime(r.created_at) + "</td>" +
                '<td><div class="table__actions">' +
                '<button class="btn btn--sm" type="button" data-detail="' + r.id + '">' +
                '<i data-lucide="eye"></i>详情</button>' +
                '<button class="btn btn--sm" type="button" data-download="' + r.id + '">' +
                '<i data-lucide="download"></i></button>' +
                "</div></td></tr>"
            );
        }).join("");
        App.icons();
    }

    function renderPager() {
        el.pagerInfo.textContent = "第 " + state.page + " / " + state.pages +
            " 页 · 共 " + state.total + " 条记录";
        el.countBadge.textContent = "共 " + state.total + " 条";
        el.prevBtn.disabled = state.page <= 1;
        el.nextBtn.disabled = state.page >= state.pages;
    }

    async function load() {
        el.historySub.textContent = "正在加载历史记录…";
        try {
            const res = await App.api("/api/history", {
                query: {
                    user_id: uid,
                    page: state.page,
                    page_size: state.pageSize,
                    task_type: state.taskType
                }
            });
            const data = pick(res) || {};
            const items = data.items || [];
            state.total = data.total || 0;
            state.pages = Math.max(1, data.pages || 1);
            state.page = data.page || state.page;
            renderRows(items);
            renderPager();
            el.historySub.textContent = "查看历史检测任务与结果明细";
        } catch (err) {
            App.toast(err.message, "err");
            el.historySub.textContent = "历史记录加载失败";
            renderRows([]);
            renderPager();
        }
    }

    /* ---------- 详情弹窗 ---------- */

    let detailUrl = null;

    function buildModal() {
        let modal = document.getElementById("detailModal");
        if (modal) return modal;
        modal = document.createElement("div");
        modal.id = "detailModal";
        modal.className = "modal";
        modal.innerHTML =
            '<div class="modal__card modal__card--wide">' +
            '<div class="modal__head"><div class="modal__title" id="detailTitle">记录详情</div>' +
            '<button class="modal__close" type="button" data-close><i data-lucide="x"></i></button></div>' +
            '<div class="modal__body" id="detailBody"></div>' +
            '<div class="modal__foot">' +
            '<button class="btn" type="button" data-close>关闭</button>' +
            '<button class="btn btn--primary" type="button" id="detailDownload">' +
            '<i data-lucide="download"></i>下载结果文件</button></div></div>';
        document.body.appendChild(modal);
        modal.addEventListener("click", function (e) {
            if (e.target === modal || e.target.closest("[data-close]")) closeModal();
        });
        return modal;
    }

    function closeModal() {
        const modal = document.getElementById("detailModal");
        if (modal) modal.classList.remove("is-open");
        if (detailUrl) {
            URL.revokeObjectURL(detailUrl);
            detailUrl = null;
        }
    }

    function normaliseClasses(classStatistics) {
        return (classStatistics || []).slice().sort(function (a, b) {
            return (b.count || 0) - (a.count || 0);
        });
    }

    async function openDetail(id) {
        const modal = buildModal();
        const body = document.getElementById("detailBody");
        document.getElementById("detailTitle").textContent = "记录详情 #" + id;
        body.innerHTML = '<div class="loading"><span class="spinner spinner--dark"></span>正在加载详情…</div>';
        modal.classList.add("is-open");
        App.icons();

        try {
            const res = await App.api("/api/history/" + id, { query: { user_id: uid } });
            const d = pick(res) || {};
            const isVideo = d.task_type === "video";

            const fields = [
                ["原始文件", d.original_name],
                ["任务类型", isVideo ? "视频检测" : "图片检测"],
                ["检测模型", d.model_name],
                ["状态", (STATUS[d.status] || {}).text || d.status],
                ["检测目标总数", App.formatNumber(d.object_count || 0)],
                ["推理耗时", App.formatSeconds(d.inference_time)],
                ["媒体尺寸", (d.width || "-") + " × " + (d.height || "-")],
                ["帧数", d.frame_count ? App.formatNumber(d.frame_count) : "-"],
                ["帧率", d.fps ? d.fps + " FPS" : "-"],
                ["单帧最多目标", d.max_objects === null || d.max_objects === undefined ? "-" : App.formatNumber(d.max_objects)],
                ["创建时间", App.formatDateTime(d.created_at)],
                ["记录 ID", "#" + d.id]
            ];

            body.innerHTML =
                '<div class="preview mb-16" id="detailPreview" style="max-height:380px">' +
                '<div class="preview__placeholder"><span class="spinner spinner--dark"></span><span>正在载入结果文件…</span></div></div>' +
                '<div class="dl mb-16">' + fields.map(function (f) {
                    return '<div class="dl__item"><div class="dl__k">' + App.escapeHtml(f[0]) +
                        '</div><div class="dl__v">' + App.escapeHtml(f[1] === undefined ? "-" : f[1]) + "</div></div>";
                }).join("") + "</div>" +
                '<div class="card__title" style="font-size:13.5px;margin-bottom:12px">类别统计</div>' +
                '<div class="classbar" id="detailClasses"></div>';

            // 类别统计
            const classes = normaliseClasses(d.class_statistics);
            const classBox = document.getElementById("detailClasses");
            if (!classes.length) {
                classBox.innerHTML = '<div class="muted">本次检测未记录类别统计</div>';
            } else {
                const max = classes[0].count || 1;
                classBox.innerHTML = classes.map(function (c, i) {
                    const pct = Math.max(2, Math.round((c.count / max) * 100));
                    const color = App.CHART_COLORS[i % App.CHART_COLORS.length];
                    return '<div class="classbar__row"><div class="classbar__name">' +
                        App.escapeHtml(c.class_name) + "</div>" +
                        '<div class="classbar__track"><div class="classbar__fill" style="width:' + pct +
                        "%;background:" + color + '"></div></div>' +
                        '<div class="classbar__value">' + App.formatNumber(c.count) + "</div></div>";
                }).join("");
            }

            // 结果文件预览
            const previewBox = document.getElementById("detailPreview");
            if (d.result_path) {
                try {
                    const fileRes = await fetch(App.downloadUrl(d.id, uid));
                    const blob = await fileRes.blob();
                    const typed = new Blob([blob], { type: isVideo ? "video/mp4" : "image/jpeg" });
                    detailUrl = URL.createObjectURL(typed);
                    previewBox.innerHTML = "";
                    const node = document.createElement(isVideo ? "video" : "img");
                    node.src = detailUrl;
                    if (isVideo) { node.controls = true; node.playsInline = true; }
                    previewBox.appendChild(node);
                } catch (e) {
                    previewBox.innerHTML = '<div class="preview__placeholder"><i data-lucide="alert-circle"></i><span>结果文件加载失败</span></div>';
                }
            } else {
                previewBox.innerHTML = '<div class="preview__placeholder"><i data-lucide="file-x"></i><span>该记录没有结果文件</span></div>';
            }

            const dl = document.getElementById("detailDownload");
            dl.onclick = function () { window.open(App.downloadUrl(d.id, uid), "_blank"); };
            dl.disabled = !d.result_path;

            App.icons();
        } catch (err) {
            body.innerHTML = '<div class="empty"><i data-lucide="alert-triangle"></i>' +
                '<div class="empty__title">' + App.escapeHtml(err.message) + "</div></div>";
            App.icons();
        }
    }

    /* ---------- 事件 ---------- */

    document.querySelectorAll("#typeFilter .segmented__item").forEach(function (btn) {
        btn.addEventListener("click", function () {
            document.querySelectorAll("#typeFilter .segmented__item").forEach(function (b) {
                b.classList.remove("is-active");
            });
            btn.classList.add("is-active");
            state.taskType = btn.getAttribute("data-type");
            state.page = 1;
            load();
        });
    });

    el.prevBtn.addEventListener("click", function () {
        if (state.page > 1) { state.page--; load(); }
    });
    el.nextBtn.addEventListener("click", function () {
        if (state.page < state.pages) { state.page++; load(); }
    });
    el.refreshBtn.addEventListener("click", load);

    document.addEventListener("click", function (e) {
        const detail = e.target.closest("[data-detail]");
        if (detail) { openDetail(detail.getAttribute("data-detail")); return; }
        const download = e.target.closest("[data-download]");
        if (download) {
            window.open(App.downloadUrl(download.getAttribute("data-download"), uid), "_blank");
        }
    });

    load();
})();
