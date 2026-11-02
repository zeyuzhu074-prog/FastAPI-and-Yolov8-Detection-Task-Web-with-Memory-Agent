/* ============================================================
   登录 / 注册页逻辑
   ============================================================ */
(function () {
    "use strict";

    App.icons();

    // 已登录则直接进入控制台
    if (App.getSession()) {
        location.replace("statistics.html");
        return;
    }

    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const formTitle = document.getElementById("formTitle");
    const formSub = document.getElementById("formSub");
    const footHint = document.getElementById("footHint");
    const tabs = document.querySelectorAll(".login__tab");

    function switchTab(name) {
        tabs.forEach(function (t) {
            t.classList.toggle("is-active", t.getAttribute("data-tab") === name);
        });
        const isLogin = name === "login";
        loginForm.classList.toggle("hidden", !isLogin);
        registerForm.classList.toggle("hidden", isLogin);
        formTitle.textContent = isLogin ? "欢迎回来" : "创建账号";
        formSub.textContent = isLogin
            ? "请登录以进入巡检与检测控制台"
            : "注册后即可使用检测与统计分析功能";
        footHint.textContent = isLogin
            ? "默认管理员账号：admin / 123456"
            : "用户名需 3 - 50 位，密码不少于 6 位";
        App.icons();
    }

    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            switchTab(tab.getAttribute("data-tab"));
        });
    });

    // 密码显隐
    document.querySelectorAll("[data-toggle-pwd]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const input = btn.parentElement.querySelector("input");
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            btn.innerHTML = '<i data-lucide="' + (show ? "eye-off" : "eye") + '"></i>';
            App.icons();
        });
    });

    function setLoading(btn, loading, text) {
        if (loading) {
            btn.dataset.original = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>' + text;
        } else {
            btn.disabled = false;
            if (btn.dataset.original) btn.innerHTML = btn.dataset.original;
            App.icons();
        }
    }

    // 登录
    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const btn = loginForm.querySelector('button[type="submit"]');
        const username = loginForm.username.value.trim();
        const password = loginForm.password.value;

        if (!username || !password) {
            App.toast("请输入用户名和密码", "warn");
            return;
        }

        setLoading(btn, true, "登录中");
        try {
            const res = await App.api("/api/auth/login", {
                method: "POST",
                body: { username: username, password: password }
            });
            const user = res.data || res;
            App.setSession({
                user_id: user.user_id,
                username: user.username,
                role: user.role
            });
            App.toast("登录成功，正在进入控制台", "ok");
            setTimeout(function () {
                location.replace("statistics.html");
            }, 500);
        } catch (err) {
            App.toast(err.message, "err");
            setLoading(btn, false);
        }
    });

    // 注册
    registerForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const btn = registerForm.querySelector('button[type="submit"]');
        const username = registerForm.username.value.trim();
        const password = registerForm.password.value;
        const confirm = registerForm.confirm.value;

        if (username.length < 3) {
            App.toast("用户名长度不能少于 3 位", "warn");
            return;
        }
        if (password.length < 6) {
            App.toast("密码长度不能少于 6 位", "warn");
            return;
        }
        if (password !== confirm) {
            App.toast("两次输入的密码不一致", "warn");
            return;
        }

        setLoading(btn, true, "注册中");
        try {
            await App.api("/api/auth/register", {
                method: "POST",
                body: { username: username, password: password }
            });
            App.toast("注册成功，请使用新账号登录", "ok");
            registerForm.reset();
            switchTab("login");
            loginForm.username.value = username;
            loginForm.password.focus();
        } catch (err) {
            App.toast(err.message, "err");
        } finally {
            setLoading(btn, false);
        }
    });
})();
