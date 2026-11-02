/* ============================================================
   共享脚本：会话、JWT、API、布局外壳、改密、提示
   ============================================================ */
window.App = (function () {
    "use strict";

    const API_BASE = "http://127.0.0.1:8000";
    const SESSION_KEY = "uav.session";

    const NAV_MAIN = [
        { key: "statistics", label: "统计分析", icon: "chart-pie", href: "statistics.html" },
        { key: "image", label: "图片检测", icon: "image", href: "detection.html?mode=image" },
        { key: "video", label: "视频检测", icon: "video", href: "detection.html?mode=video" },
        { key: "history", label: "历史记录", icon: "history", href: "history.html" }
    ];

    const NAV_ADMIN = [
        { key: "admin", label: "管理员后台", icon: "shield-check", href: "admin.html" }
    ];

    /* ---------------- 会话 ---------------- */

    function getSession() {
        try {
            const raw = localStorage.getItem(SESSION_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function setSession(user) {
        localStorage.setItem(SESSION_KEY, JSON.stringify(user));
    }

    function updateSession(patch) {
        const current = getSession() || {};
        setSession(Object.assign({}, current, patch));
    }

    function clearSession() {
        localStorage.removeItem(SESSION_KEY);
    }

    function getToken() {
        const user = getSession();
        return user && user.access_token ? user.access_token : null;
    }

    function isAdmin() {
        const user = getSession();
        return !!user && user.role === "admin";
    }

    function requireAuth() {
        const user = getSession();

        if (!user || !user.user_id || !user.access_token) {
            location.replace("login.html");
            return null;
        }

        return user;
    }

    function authHeaders() {
        const token = getToken();
        return token ? { Authorization: "Bearer " + token } : {};
    }

    /* ---------------- 图标 ---------------- */

    function icons() {
        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }
    }

    /* ---------------- API ---------------- */

    function buildUrl(path, query) {
        let url = API_BASE + path;
        if (query) {
            const params = new URLSearchParams();
            Object.keys(query).forEach(function (k) {
                const v = query[k];
                if (v !== undefined && v !== null && v !== "") {
                    params.append(k, v);
                }
            });
            const qs = params.toString();
            if (qs) url += "?" + qs;
        }
        return url;
    }

    async function api(path, options) {
        options = options || {};
        const url = buildUrl(path, options.query);
        const token = getToken();
        const init = {
            method: options.method || "GET",
            headers: Object.assign({}, authHeaders(), options.headers || {})
        };

        if (options.body instanceof FormData) {
            init.body = options.body;
        } else if (options.body !== undefined) {
            init.headers["Content-Type"] = "application/json";
            init.body = JSON.stringify(options.body);
        }

        let res;
        try {
            res = await fetch(url, init);
        } catch (e) {
            throw new Error("无法连接后端服务，请确认已启动 http://127.0.0.1:8000");
        }

        if (res.status === 401 && token) {
            clearSession();
            if (!/login\.html$/.test(location.pathname)) {
                location.replace("login.html");
            }
            throw new Error("登录状态已失效，请重新登录");
        }

        if (options.raw) return res;

        let data = null;
        try {
            data = await res.json();
        } catch (e) {
            data = null;
        }

        if (!res.ok) {
            const detail = data && (data.detail || data.message);
            throw new Error(detail || ("请求失败（" + res.status + "）"));
        }
        return data;
    }

    async function fetchResultBlob(recordId) {
        const res = await api(
            "/api/detection/download/" + recordId,
            { raw: true }
        );

        if (!res.ok) {
            let detail = null;
            try {
                const data = await res.json();
                detail = data && data.detail;
            } catch (e) { /* 忽略 */ }
            throw new Error(detail || "结果文件获取失败");
        }

        return res.blob();
    }

    function filenameFromDisposition(header, fallback) {
        if (!header) return fallback;

        const match = header.match(
            /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i
        );

        if (!match) return fallback;

        try {
            return decodeURIComponent(match[1]);
        } catch (e) {
            return match[1];
        }
    }

    async function downloadFile(recordId) {
        const res = await api(
            "/api/detection/download/" + recordId,
            { raw: true }
        );

        if (!res.ok) {
            let detail = null;
            try {
                const data = await res.json();
                detail = data && data.detail;
            } catch (e) { /* 忽略 */ }
            throw new Error(detail || "结果文件下载失败");
        }

        const blob = await res.blob();
        const filename = filenameFromDisposition(
            res.headers.get("Content-Disposition"),
            "detection_result"
        );

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();

        setTimeout(function () {
            URL.revokeObjectURL(url);
        }, 1600);

        return filename;
    }

    function avatarUrl(user) {
        const target = user || getSession();

        if (!target || !target.avatar_url) return null;

        if (/^https?:\/\//i.test(target.avatar_url)) {
            return target.avatar_url;
        }

        return API_BASE + target.avatar_url;
    }

    /* ---------------- 工具 ---------------- */

    function escapeHtml(value) {
        if (value === null || value === undefined) return "";
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatNumber(value) {
        const n = Number(value || 0);
        return n.toLocaleString("zh-CN");
    }

    function formatSeconds(value) {
        if (value === null || value === undefined || value === "") return "-";
        const n = Number(value);
        if (isNaN(n)) return "-";
        if (n < 1) return (n * 1000).toFixed(0) + " ms";
        return n.toFixed(2) + " s";
    }

    function formatDateTime(value) {
        if (!value) return "-";
        const d = new Date(value);
        if (isNaN(d.getTime())) return String(value);
        const pad = function (x) { return String(x).padStart(2, "0"); };
        return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) +
            " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
    }

    function todayKey() {
        return new Date().toISOString().slice(0, 10);
    }

    function bytes(bytesValue) {
        const units = ["B", "KB", "MB", "GB"];
        let n = Number(bytesValue || 0);
        let i = 0;
        while (n >= 1024 && i < units.length - 1) {
            n /= 1024;
            i++;
        }
        return (i === 0 ? n : n.toFixed(1)) + " " + units[i];
    }

    /* ---------------- Toast ---------------- */

    function toastRoot() {
        let root = document.getElementById("toastRoot");
        if (!root) {
            root = document.createElement("div");
            root.id = "toastRoot";
            root.className = "toast-root";
            document.body.appendChild(root);
        }
        return root;
    }

    const TOAST_ICON = {
        ok: "check-circle-2",
        err: "x-circle",
        warn: "alert-triangle",
        info: "info"
    };

    function toast(message, type) {
        type = type || "info";
        const el = document.createElement("div");
        el.className = "toast toast--" + type;
        el.innerHTML =
            '<i data-lucide="' + (TOAST_ICON[type] || "info") + '"></i><span>' +
            escapeHtml(message) + "</span>";
        toastRoot().appendChild(el);
        icons();

        setTimeout(function () {
            el.classList.add("is-out");
            setTimeout(function () {
                if (el.parentNode) el.parentNode.removeChild(el);
            }, 220);
        }, 3200);
    }

    /* ---------------- 侧边栏 / 顶栏 ---------------- */

    function brandMark() {
        return (
            '<span class="brand__mark"><i data-lucide="radar"></i></span>'
        );
    }

    function navItem(item, active) {
        const isActive = item.key === active ? " is-active" : "";
        return (
            '<a class="nav-item' + isActive + '" href="' + item.href + '">' +
            '<i data-lucide="' + item.icon + '"></i>' +
            "<span>" + item.label + "</span></a>"
        );
    }

    function sidebarHtml(active, user) {
        const mainItems = NAV_MAIN.map(function (item) {
            return navItem(item, active);
        }).join("");

        const adminItems = user && user.role === "admin"
            ? NAV_ADMIN.map(function (item) {
                return navItem(item, active);
            }).join("")
            : "";

        return (
            '<div class="sidebar__brand">' + brandMark() +
            '<div class="brand__text">' +
            '<div class="brand__name">无人机智能巡检系统</div>' +
            '<div class="brand__sub">UAV INSPECTION</div>' +
            "</div></div>" +
            '<nav class="sidebar__nav">' +
            '<div class="nav__label">功能菜单</div>' +
            mainItems +
            (adminItems
                ? '<div class="nav__label" style="margin-top:14px">管理</div>' + adminItems
                : "") +
            "</nav>" +
            '<div class="sidebar__bottom">' +
            '<div class="sidebar__sep"></div>' +
            '<a class="nav-item' + (active === "profile" ? " is-active" : "") +
            '" href="profile.html"><i data-lucide="user-round"></i><span>个人中心</span></a>' +
            '<a class="nav-item" href="#" data-action="password">' +
            '<i data-lucide="key-round"></i><span>密码修改</span></a>' +
            '<a class="nav-item" href="#" data-action="logout">' +
            '<i data-lucide="log-out"></i><span>退出登录</span></a>' +
            "</div>"
        );
    }

    function avatarHtml(user, className) {
        const url = avatarUrl(user);

        if (url) {
            return '<span class="' + className + '">' +
                '<img src="' + escapeHtml(url) + '" alt="avatar">' +
                "</span>";
        }

        const initial = (user.username || "U").trim().charAt(0) || "U";

        return '<span class="' + className + '">' +
            escapeHtml(initial.toUpperCase()) +
            "</span>";
    }

    function topbarHtml(opts, user) {
        const roleText = user.role === "admin" ? "管理员" : "普通用户";
        return (
            '<button class="topbar__burger" type="button" data-action="toggle-nav">' +
            '<i data-lucide="menu"></i></button>' +
            '<div class="topbar__heading">' +
            '<div class="topbar__title">' + escapeHtml(opts.title || "") + "</div>" +
            (opts.subtitle ? '<div class="topbar__crumb">' + escapeHtml(opts.subtitle) + "</div>" : "") +
            "</div>" +
            '<div class="topbar__spacer"></div>' +
            '<div class="topbar__clock" id="topbarClock"></div>' +
            '<div class="user">' +
            '<button class="user__btn" type="button" data-action="toggle-user">' +
            avatarHtml(user, "user__avatar") +
            '<span class="user__name">' + escapeHtml(user.username || "") + "</span>" +
            '<i data-lucide="chevron-down"></i></button>' +
            '<div class="dropdown" id="userDropdown">' +
            '<div class="dropdown__head">' +
            '<div class="dropdown__name">' + escapeHtml(user.username || "") + "</div>" +
            '<div class="dropdown__role">' + roleText +
            (user.email ? " · " + escapeHtml(user.email) : "") + "</div>" +
            "</div>" +
            '<a class="dropdown__item" href="profile.html">' +
            '<i data-lucide="user-round"></i>个人中心</a>' +
            '<button class="dropdown__item" type="button" data-action="password">' +
            '<i data-lucide="key-round"></i>修改密码</button>' +
            '<button class="dropdown__item is-danger" type="button" data-action="logout">' +
            '<i data-lucide="log-out"></i>退出登录</button>' +
            "</div></div>"
        );
    }

    function startClock() {
        const el = document.getElementById("topbarClock");
        if (!el) return;
        const week = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
        function tick() {
            const d = new Date();
            const pad = function (x) { return String(x).padStart(2, "0"); };
            el.textContent =
                d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) +
                " " + week[d.getDay()] + " " + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
        }
        tick();
        setInterval(tick, 1000);
    }

    function bindShell() {
        const app = document.getElementById("app");

        document.addEventListener("click", function (e) {
            const actionEl = e.target.closest("[data-action]");
            const dropdown = document.getElementById("userDropdown");

            if (actionEl) {
                const action = actionEl.getAttribute("data-action");
                if (action === "logout" || action === "password" ||
                    action === "toggle-nav" || action === "toggle-user") {
                    e.preventDefault();
                }
                if (action === "logout") { logout(); return; }
                if (action === "password") { openPassword(); return; }
                if (action === "toggle-nav") { app.classList.toggle("nav-open"); return; }
                if (action === "toggle-user") { dropdown.classList.toggle("is-open"); return; }
            }

            if (dropdown && !e.target.closest(".user")) {
                dropdown.classList.remove("is-open");
            }
        });

        const backdrop = document.getElementById("sidebarBackdrop");
        if (backdrop) {
            backdrop.addEventListener("click", function () {
                app.classList.remove("nav-open");
            });
        }
    }

    /* ---------------- 修改密码 ---------------- */

    const PASSWORD_HTML =
        '<div class="modal" id="passwordModal">' +
        '<div class="modal__card">' +
        '<div class="modal__head"><div class="modal__title">修改密码</div>' +
        '<button class="modal__close" type="button" data-close><i data-lucide="x"></i></button></div>' +
        '<form id="passwordForm" novalidate><div class="modal__body">' +
        '<div class="field"><label class="field__label">当前密码</label>' +
        '<div class="input-affix"><i data-lucide="lock"></i>' +
        '<input class="input" type="password" name="old_password" placeholder="请输入当前密码" autocomplete="current-password"></div></div>' +
        '<div class="field"><label class="field__label">新密码</label>' +
        '<div class="input-affix"><i data-lucide="shield-check"></i>' +
        '<input class="input" type="password" name="new_password" placeholder="至少 6 位" autocomplete="new-password"></div>' +
        '<div class="field__hint">新密码长度不少于 6 位，且不能与当前密码相同。</div></div>' +
        '<div class="field"><label class="field__label">确认新密码</label>' +
        '<div class="input-affix"><i data-lucide="shield-check"></i>' +
        '<input class="input" type="password" name="two_new_password" placeholder="请再次输入新密码" autocomplete="new-password"></div></div>' +
        "</div>" +
        '<div class="modal__foot">' +
        '<button class="btn" type="button" data-close>取消</button>' +
        '<button class="btn btn--primary" type="submit"><i data-lucide="check"></i>确认修改</button>' +
        "</div></form></div></div>";

    function mountPassword() {
        if (document.getElementById("passwordModal")) return;
        const wrap = document.createElement("div");
        wrap.innerHTML = PASSWORD_HTML;
        document.body.appendChild(wrap.firstChild);
        icons();

        const modal = document.getElementById("passwordModal");
        const form = document.getElementById("passwordForm");

        modal.addEventListener("click", function (e) {
            if (e.target === modal || e.target.closest("[data-close]")) {
                closePassword();
            }
        });

        form.addEventListener("submit", async function (e) {
            e.preventDefault();
            const user = getSession();
            if (!user) return;

            const oldPwd = form.old_password.value.trim();
            const newPwd = form.new_password.value.trim();
            const confirmPwd = form.two_new_password.value.trim();
            const btn = form.querySelector('button[type="submit"]');

            if (!oldPwd || !newPwd || !confirmPwd) {
                toast("请填写完整的密码信息", "warn");
                return;
            }
            if (newPwd.length < 6) {
                toast("新密码长度不能少于 6 位", "warn");
                return;
            }
            if (newPwd !== confirmPwd) {
                toast("两次输入的新密码不一致", "warn");
                return;
            }

            btn.disabled = true;
            const original = btn.innerHTML;
            btn.innerHTML = '<span class="spinner"></span>提交中';

            try {
                await api("/api/auth/change-password", {
                    method: "POST",
                    body: {
                        old_password: oldPwd,
                        new_password: newPwd,
                        two_new_password: confirmPwd
                    }
                });
                toast("密码修改成功，请重新登录", "ok");
                closePassword();
                setTimeout(logout, 900);
            } catch (err) {
                toast(err.message, "err");
                btn.disabled = false;
                btn.innerHTML = original;
                icons();
            }
        });
    }

    function openPassword() {
        mountPassword();
        const modal = document.getElementById("passwordModal");
        const form = document.getElementById("passwordForm");
        form.reset();
        modal.classList.add("is-open");
        setTimeout(function () {
            const first = form.querySelector('input[name="old_password"]');
            if (first) first.focus();
        }, 60);
    }

    function closePassword() {
        const modal = document.getElementById("passwordModal");
        if (modal) modal.classList.remove("is-open");
    }

    /* ---------------- 退出 ---------------- */

    function logout() {
        clearSession();
        location.replace("login.html");
    }

    /* ---------------- 初始化 ---------------- */

    function init(opts) {
        opts = opts || {};
        const user = requireAuth();
        if (!user) return null;

        if (opts.active === "admin" && user.role !== "admin") {
            toast("需要管理员权限", "err");
            setTimeout(function () {
                location.replace("statistics.html");
            }, 600);
            return null;
        }

        const sidebar = document.getElementById("sidebar");
        const topbar = document.getElementById("topbar");
        if (sidebar) sidebar.innerHTML = sidebarHtml(opts.active, user);
        if (topbar) topbar.innerHTML = topbarHtml(opts, user);

        bindShell();
        startClock();
        icons();
        return user;
    }

    /* ---------------- 图表主题 ---------------- */

    const CHART_COLORS = [
        "#12b3a2", "#e0a63c", "#4f9dd4", "#e2647a",
        "#8672c9", "#7aab53", "#c98a5e", "#3f8f8a"
    ];

    function chartBase() {
        return {
            color: CHART_COLORS,
            textStyle: {
                fontFamily: '"PingFang SC","Microsoft YaHei","Segoe UI",system-ui,sans-serif',
                color: "#3d4451"
            },
            tooltip: {
                backgroundColor: "rgba(20,22,26,.94)",
                borderWidth: 0,
                padding: [10, 12],
                textStyle: { color: "#fff", fontSize: 12 },
                extraCssText: "border-radius:8px;box-shadow:0 12px 30px -12px rgba(0,0,0,.5)"
            }
        };
    }

    return {
        API_BASE: API_BASE,
        CHART_COLORS: CHART_COLORS,
        getSession: getSession,
        setSession: setSession,
        updateSession: updateSession,
        clearSession: clearSession,
        getToken: getToken,
        isAdmin: isAdmin,
        requireAuth: requireAuth,
        api: api,
        fetchResultBlob: fetchResultBlob,
        downloadFile: downloadFile,
        avatarUrl: avatarUrl,
        icons: icons,
        toast: toast,
        escapeHtml: escapeHtml,
        formatNumber: formatNumber,
        formatSeconds: formatSeconds,
        formatDateTime: formatDateTime,
        todayKey: todayKey,
        bytes: bytes,
        init: init,
        openPassword: openPassword,
        logout: logout,
        chartBase: chartBase
    };
})();
