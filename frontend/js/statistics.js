/* ============================================================
   统计分析页：概览卡片 + 饼图 + 条形图 + 每日走势 + 类别走势
   ============================================================ */
(function () {
    "use strict";

    const user = App.init({
        active: "statistics",
        title: "统计分析",
        subtitle: "检测数据总览与趋势"
    });
    if (!user) return;

    const uid = user.user_id;
    const charts = {};

    function pick(res) {
        return res && res.data !== undefined ? res.data : res;
    }

    function getChart(id) {
        if (!charts[id]) {
            const el = document.getElementById(id);
            charts[id] = window.echarts.init(el);
        }
        return charts[id];
    }

    function toggleEmpty(chartId, emptyId, isEmpty) {
        document.getElementById(chartId).classList.toggle("hidden", isEmpty);
        document.getElementById(emptyId).classList.toggle("hidden", !isEmpty);
    }

    function shortDate(value) {
        const s = String(value || "");
        return s.length >= 10 ? s.slice(5, 10) : s;
    }

    function setStat(name, value, foot) {
        const el = document.querySelector('[data-stat="' + name + '"]');
        const ft = document.querySelector('[data-foot="' + name + '"]');
        if (el) el.textContent = value;
        if (ft) ft.innerHTML = foot || "&nbsp;";
    }

    function renderStats(overview, trend, today) {
        const totalTasks = overview ? overview.total_tasks || 0 : 0;
        const totalObjects = overview ? overview.total_objects || 0 : 0;
        const imageTasks = overview ? overview.image_tasks || 0 : 0;
        const videoTasks = overview ? overview.video_tasks || 0 : 0;
        const avgTime = overview ? overview.average_inference_time : 0;

        let todayTasks = 0;
        let todayObjects = 0;
        if (Array.isArray(trend)) {
            const row = trend.find(function (item) { return String(item.date) === today; });
            if (row) {
                todayTasks = row.task_count || 0;
                todayObjects = row.object_count || 0;
            }
        }

        setStat("todayTasks", App.formatNumber(todayTasks), "统计日期 " + today);
        setStat("todayObjects", App.formatNumber(todayObjects), "今日累计识别目标数");
        setStat("totalTasks", App.formatNumber(totalTasks),
            "图片 " + App.formatNumber(imageTasks) + " · 视频 " + App.formatNumber(videoTasks));
        setStat("totalObjects", App.formatNumber(totalObjects),
            "平均推理 " + App.formatSeconds(avgTime));
    }

    function todayClassData(classTrend, today) {
        const result = [];
        if (!classTrend || !Array.isArray(classTrend.dates)) return result;
        const index = classTrend.dates.indexOf(today);
        if (index < 0) return result;
        const series = classTrend.series || {};
        Object.keys(series).forEach(function (name) {
            const value = (series[name] || [])[index] || 0;
            if (value > 0) result.push({ name: name, value: value });
        });
        result.sort(function (a, b) { return b.value - a.value; });
        return result;
    }

    function renderPie(data) {
        const isEmpty = data.length === 0;
        toggleEmpty("pieChart", "pieEmpty", isEmpty);
        const total = data.reduce(function (s, d) { return s + d.value; }, 0);
        document.getElementById("pieSub").textContent = isEmpty
            ? "按目标类别统计"
            : "共 " + total + " 个目标 · " + data.length + " 个类别";
        if (isEmpty) return;

        const chart = getChart("pieChart");
        chart.setOption(Object.assign(App.chartBase(), {
            tooltip: Object.assign(App.chartBase().tooltip, {
                trigger: "item",
                formatter: "{b}<br/>{c} 个（{d}%）"
            }),
            legend: {
                type: "scroll",
                bottom: 0,
                icon: "circle",
                itemWidth: 9,
                itemHeight: 9,
                itemGap: 14,
                textStyle: { color: "#6b7280", fontSize: 12 }
            },
            graphic: [
                {
                    type: "text", left: "center", top: "34%",
                    style: { text: String(total), fontSize: 26, fontWeight: 700, fill: "#14161a", textAlign: "center" }
                },
                {
                    type: "text", left: "center", top: "45%",
                    style: { text: "今日目标总数", fontSize: 12, fill: "#9aa1ad", textAlign: "center" }
                }
            ],
            series: [{
                type: "pie",
                radius: ["54%", "76%"],
                center: ["50%", "42%"],
                avoidLabelOverlap: true,
                itemStyle: { borderColor: "#fff", borderWidth: 2, borderRadius: 4 },
                label: { show: false },
                labelLine: { show: false },
                emphasis: {
                    scale: true,
                    scaleSize: 6,
                    label: { show: true, fontSize: 13, fontWeight: 600, formatter: "{b}\n{d}%" }
                },
                data: data.map(function (d) { return { name: d.name, value: d.value }; })
            }]
        }), true);
    }

    function renderBar(data) {
        const isEmpty = data.length === 0;
        toggleEmpty("barChart", "barEmpty", isEmpty);
        document.getElementById("barSub").textContent = isEmpty
            ? "各类别目标检出数量"
            : "共 " + data.reduce(function (s, d) { return s + d.value; }, 0) + " 个目标";
        if (isEmpty) return;

        const names = data.map(function (d) { return d.name; });
        const values = data.map(function (d) { return d.value; });

        const chart = getChart("barChart");
        chart.setOption(Object.assign(App.chartBase(), {
            grid: { left: 8, right: 46, top: 12, bottom: 8, containLabel: true },
            tooltip: Object.assign(App.chartBase().tooltip, {
                trigger: "axis",
                axisPointer: { type: "shadow" },
                formatter: "{b}<br/>{c} 个"
            }),
            xAxis: {
                type: "value",
                splitLine: { lineStyle: { color: "#eef0f3" } },
                axisLabel: { color: "#9aa1ad", fontSize: 11 },
                axisLine: { show: false },
                axisTick: { show: false }
            },
            yAxis: {
                type: "category",
                inverse: true,
                data: names,
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: "#3d4451", fontSize: 12 }
            },
            series: [{
                type: "bar",
                data: values.map(function (v, i) {
                    return {
                        value: v,
                        itemStyle: {
                            color: App.CHART_COLORS[i % App.CHART_COLORS.length],
                            borderRadius: [0, 4, 4, 0]
                        }
                    };
                }),
                barWidth: "52%",
                label: {
                    show: true,
                    position: "right",
                    color: "#6b7280",
                    fontSize: 12
                }
            }]
        }), true);
    }

    function renderTrend(trend) {
        const rows = Array.isArray(trend) ? trend : [];
        const isEmpty = rows.length === 0;
        toggleEmpty("trendChart", "trendEmpty", isEmpty);
        document.getElementById("trendBadge").textContent = isEmpty ? "暂无数据" : "共 " + rows.length + " 天";
        if (isEmpty) return;

        const dates = rows.map(function (r) { return shortDate(r.date); });
        const objects = rows.map(function (r) { return r.object_count || 0; });
        const tasks = rows.map(function (r) { return r.task_count || 0; });
        const windowDays = 14;
        const needZoom = rows.length > windowDays;
        const startPct = needZoom ? Math.max(0, Math.round(100 - (windowDays / rows.length) * 100)) : 0;

        const chart = getChart("trendChart");
        chart.setOption(Object.assign(App.chartBase(), {
            grid: { left: 10, right: 16, top: 44, bottom: needZoom ? 46 : 8, containLabel: true },
            legend: {
                top: 4, right: 4, icon: "roundRect",
                itemWidth: 12, itemHeight: 8, itemGap: 16,
                textStyle: { color: "#6b7280", fontSize: 12 }
            },
            tooltip: Object.assign(App.chartBase().tooltip, { trigger: "axis" }),
            xAxis: {
                type: "category",
                boundaryGap: true,
                data: dates,
                axisLine: { lineStyle: { color: "#e6e8ec" } },
                axisTick: { show: false },
                axisLabel: { color: "#9aa1ad", fontSize: 11 }
            },
            yAxis: [
                {
                    type: "value", name: "目标数",
                    nameTextStyle: { color: "#9aa1ad", fontSize: 11 },
                    splitLine: { lineStyle: { color: "#eef0f3" } },
                    axisLabel: { color: "#9aa1ad", fontSize: 11 }
                },
                {
                    type: "value", name: "检测次数",
                    nameTextStyle: { color: "#9aa1ad", fontSize: 11 },
                    splitLine: { show: false },
                    axisLabel: { color: "#9aa1ad", fontSize: 11 }
                }
            ],
            dataZoom: needZoom ? [
                { type: "inside", start: startPct, end: 100 },
                { type: "slider", height: 16, bottom: 10, start: startPct, end: 100, borderColor: "transparent", fillerColor: "rgba(18,179,162,.14)", handleStyle: { color: "#12b3a2" } }
            ] : [],
            series: [
                {
                    name: "检测次数",
                    type: "bar",
                    yAxisIndex: 1,
                    data: tasks,
                    barWidth: "38%",
                    itemStyle: { color: "rgba(224,166,60,.55)", borderRadius: [3, 3, 0, 0] }
                },
                {
                    name: "目标总数",
                    type: "line",
                    smooth: true,
                    symbol: "circle",
                    symbolSize: 6,
                    data: objects,
                    lineStyle: { width: 2.6, color: "#12b3a2" },
                    itemStyle: { color: "#12b3a2", borderColor: "#fff", borderWidth: 1.5 },
                    areaStyle: {
                        color: {
                            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
                            colorStops: [
                                { offset: 0, color: "rgba(18,179,162,.26)" },
                                { offset: 1, color: "rgba(18,179,162,.02)" }
                            ]
                        }
                    }
                }
            ]
        }), true);
    }

    function renderClassTrend(classTrend) {
        const dates = (classTrend && classTrend.dates) || [];
        const series = (classTrend && classTrend.series) || {};
        const names = Object.keys(series);
        const isEmpty = dates.length === 0 || names.length === 0;
        toggleEmpty("classChart", "classEmpty", isEmpty);
        document.getElementById("classBadge").textContent = isEmpty ? "暂无数据" : names.length + " 个类别";
        if (isEmpty) return;

        const chart = getChart("classChart");
        chart.setOption(Object.assign(App.chartBase(), {
            grid: { left: 10, right: 18, top: 52, bottom: dates.length > 12 ? 44 : 8, containLabel: true },
            legend: {
                type: "scroll", top: 4, left: 0, right: 0,
                icon: "roundRect", itemWidth: 12, itemHeight: 8, itemGap: 14,
                textStyle: { color: "#6b7280", fontSize: 12 }
            },
            tooltip: Object.assign(App.chartBase().tooltip, { trigger: "axis" }),
            xAxis: {
                type: "category",
                boundaryGap: false,
                data: dates.map(shortDate),
                axisLine: { lineStyle: { color: "#e6e8ec" } },
                axisTick: { show: false },
                axisLabel: { color: "#9aa1ad", fontSize: 11 }
            },
            yAxis: {
                type: "value",
                splitLine: { lineStyle: { color: "#eef0f3" } },
                axisLabel: { color: "#9aa1ad", fontSize: 11 }
            },
            dataZoom: dates.length > 14 ? [
                { type: "inside", start: 50, end: 100 },
                { type: "slider", height: 16, bottom: 8, start: 50, end: 100, borderColor: "transparent", fillerColor: "rgba(18,179,162,.14)", handleStyle: { color: "#12b3a2" } }
            ] : [],
            series: names.map(function (name, i) {
                const color = App.CHART_COLORS[i % App.CHART_COLORS.length];
                return {
                    name: name,
                    type: "line",
                    smooth: true,
                    symbol: "circle",
                    symbolSize: 5,
                    data: series[name] || [],
                    lineStyle: { width: 2, color: color },
                    itemStyle: { color: color },
                    emphasis: { focus: "series" }
                };
            })
        }), true);
    }

    function stampTime() {
        const d = new Date();
        const pad = function (x) { return String(x).padStart(2, "0"); };
        document.getElementById("overviewSub").textContent =
            "数据更新于 " + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
    }

    async function load() {
        const today = App.todayKey();
        document.getElementById("todayBadge").textContent = "今日 " + today;
        document.getElementById("overviewSub").textContent = "正在加载统计数据…";

        const query = { user_id: uid };
        const results = await Promise.allSettled([
            App.api("/api/statistics/overview", { query: query }),
            App.api("/api/statistics/trend", { query: query }),
            App.api("/api/statistics/class-trend", { query: query })
        ]);

        const overview = results[0].status === "fulfilled" ? pick(results[0].value) : null;
        const trend = results[1].status === "fulfilled" ? pick(results[1].value) : [];
        const classTrend = results[2].status === "fulfilled" ? pick(results[2].value) : null;

        if (results.every(function (r) { return r.status === "rejected"; })) {
            App.toast(results[0].reason ? results[0].reason.message : "统计数据加载失败", "err");
        }

        renderStats(overview, trend, today);
        const todayData = todayClassData(classTrend, today);
        renderPie(todayData);
        renderBar(todayData);
        renderTrend(trend);
        renderClassTrend(classTrend);
        stampTime();
    }

    const refreshBtn = document.getElementById("refreshBtn");
    refreshBtn.addEventListener("click", async function () {
        const original = refreshBtn.innerHTML;
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<span class="spinner spinner--dark"></span>刷新中';
        await load();
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = original;
        App.icons();
    });

    window.addEventListener("resize", function () {
        Object.keys(charts).forEach(function (k) { charts[k].resize(); });
    });

    load();
})();
