/* ============================================================
   个人中心：资料、头像、密码
   ============================================================ */
(function () {
    "use strict";

    const user = App.init({
        active: "profile",
        title: "个人中心",
        subtitle: "账号资料与安全设置"
    });
    if (!user) return;

    const el = {
        avatar: document.getElementById("profileAvatar"),
        name: document.getElementById("profileName"),
        role: document.getElementById("profileRole"),
        email: document.getElementById("profileEmail"),
        created: document.getElementById("profileCreated"),
        form: document.getElementById("profileForm"),
        avatarInput: document.getElementById("avatarInput"),
        uploadBtn: document.getElementById("uploadAvatarBtn"),
        deleteBtn: document.getElementById("deleteAvatarBtn"),
        changePwdBtn: document.getElementById("changePwdBtn"),
        infoId: document.getElementById("infoId"),
        infoRole: document.getElementById("infoRole"),
        infoStatus: document.getElementById("infoStatus"),
        infoUpdated: document.getElementById("infoUpdated")
    };

    let profile = null;

    function pick(res) {
        return res && res.data !== undefined ? res.data : res;
    }

    function renderAvatar(data) {
        const url = App.avatarUrl(data);

        if (url) {
            el.avatar.innerHTML =
                '<img src="' + App.escapeHtml(url) + '" alt="avatar">';
        } else {
            el.avatar.textContent =
                (data.username || "U").trim().charAt(0).toUpperCase() || "U";
        }
    }

    function render(data) {
        profile = data;

        el.name.textContent = data.username || "-";
        el.role.textContent = data.role === "admin" ? "管理员" : "普通用户";
        el.email.textContent = data.email || "未设置";
        el.created.textContent = App.formatDateTime(data.created_at);

        el.form.username.value = data.username || "";
        el.form.email.value = data.email || "";

        el.infoId.textContent = "#" + data.user_id;
        el.infoRole.textContent = data.role === "admin" ? "管理员" : "普通用户";
        el.infoStatus.textContent = data.status === 1 ? "正常" : "已禁用";
        el.infoUpdated.textContent = App.formatDateTime(data.updated_at);

        el.deleteBtn.disabled = !data.avatar_url;

        renderAvatar(data);
        App.icons();
    }

    async function load() {
        try {
            const res = await App.api("/api/profile/me");
            const data = pick(res);
            render(data);
            App.updateSession({
                username: data.username,
                email: data.email,
                avatar_url: data.avatar_url,
                role: data.role
            });
        } catch (err) {
            App.toast(err.message, "err");
        }
    }

    el.form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const username = el.form.username.value.trim();
        const email = el.form.email.value.trim();
        const btn = el.form.querySelector('button[type="submit"]');

        if (username.length < 3) {
            App.toast("用户名长度不能少于 3 位", "warn");
            return;
        }

        btn.disabled = true;
        const original = btn.innerHTML;
        btn.innerHTML = '<span class="spinner spinner--dark"></span>保存中';

        try {
            const res = await App.api("/api/profile/me", {
                method: "PUT",
                body: { username: username, email: email }
            });
            const data = pick(res);
            render(data);
            App.updateSession({
                username: data.username,
                email: data.email
            });
            App.toast("个人资料已保存", "ok");
        } catch (err) {
            App.toast(err.message, "err");
        } finally {
            btn.disabled = false;
            btn.innerHTML = original;
            App.icons();
        }
    });

    el.uploadBtn.addEventListener("click", function () {
        el.avatarInput.click();
    });

    el.avatarInput.addEventListener("change", async function () {
        const file = el.avatarInput.files && el.avatarInput.files[0];
        if (!file) return;

        if (file.size > 2 * 1024 * 1024) {
            App.toast("头像大小不能超过 2 MB", "warn");
            el.avatarInput.value = "";
            return;
        }

        const form = new FormData();
        form.append("file", file, file.name);

        el.uploadBtn.disabled = true;

        try {
            const res = await App.api("/api/profile/avatar", {
                method: "POST",
                body: form
            });
            const data = pick(res);
            render(data);
            App.updateSession({ avatar_url: data.avatar_url });
            App.toast("头像已更新", "ok");
        } catch (err) {
            App.toast(err.message, "err");
        } finally {
            el.uploadBtn.disabled = false;
            el.avatarInput.value = "";
        }
    });

    el.deleteBtn.addEventListener("click", async function () {
        if (!confirm("确定删除当前头像吗？")) return;

        try {
            const res = await App.api("/api/profile/avatar", {
                method: "DELETE"
            });
            const data = pick(res);
            render(data);
            App.updateSession({ avatar_url: null });
            App.toast("头像已删除", "ok");
        } catch (err) {
            App.toast(err.message, "err");
        }
    });

    el.changePwdBtn.addEventListener("click", function () {
        App.openPassword();
    });

    load();
})();
