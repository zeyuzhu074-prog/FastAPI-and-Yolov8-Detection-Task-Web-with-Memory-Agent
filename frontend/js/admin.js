/* ============================================================
   管理员后台：用户管理 + 检测记录管理
   ============================================================ */
(function () {
    "use strict";

    const admin = App.init({
        active: "admin",
        title: "管理员后台",
        subtitle: "用户与检测记录管理"
    });
    if (!admin) return;

    const state = {
        tab: "users",
        users: {
            page: 1,
            pageSize: 10,
            keyword: "",
            status: "",
            role: "",
            total: 0,
            pages: 0
        },
        records: {
            page: 1,
            pageSize: 10,
            username: "",
            filename: "",
            start: "",
            end: "",
            type: "",
            status: "",
            total: 0,
            pages: 0
        },
        userMap: {},
        recordMap: {}
    };

    const el = {
        usersPanel: document.getElementById("usersPanel"),
        recordsPanel: document.getElementById("recordsPanel"),
        usersBody: document.getElementById("usersBody"),
        usersEmpty: document.getElementById("usersEmpty"),
        usersTableWrap: document.querySelector("#usersPanel .table-wrap"),
        userCountBadge: document.getElementById("userCountBadge"),
        usersPagerInfo: document.getElementById("usersPagerInfo"),
        usersPrevBtn: document.getElementById("usersPrevBtn"),
        usersNextBtn: document.getElementById("usersNextBtn"),
        userKeyword: document.getElementById("userKeyword"),
        userStatusFilter: document.getElementById("userStatusFilter"),
        userRoleFilter: document.getElementById("userRoleFilter"),
        recordsBody: document.getElementById("recordsBody"),
        recordsEmpty: document.getElementById("recordsEmpty"),
        recordsTableWrap: document.querySelector("#recordsPanel .table-wrap"),
        recordCountBadge: document.getElementById("recordCountBadge"),
        recordsPagerInfo: document.getElementById("recordsPagerInfo"),
        recordsPrevBtn: document.getElementById("recordsPrevBtn"),
        recordsNextBtn: document.getElementById("recordsNextBtn"),
        recordUsername: document.getElementById("recordUsername"),
        recordFilename: document.getElementById("recordFilename"),
        recordStart: document.getElementById("recordStart"),
        recordEnd: document.getElementById("recordEnd"),
        recordType: document.getElementById("recordType"),
        recordStatus: document.getElementById("recordStatus"),
        userModal: document.getElementById("userModal"),
        userForm: document.getElementById("userForm"),
        userModalTitle: document.getElementById("userModalTitle"),
        userPasswordField: document.getElementById("userPasswordField"),
        userStatusField: document.getElementById("userStatusField"),
        resetPwdModal: document.getElementById("resetPwdModal"),
        resetPwdForm: document.getElementById("resetPwdForm"),
        resetPwdTitle: document.getElementById("resetPwdTitle"),
        recordModal: document.getElementById("recordModal"),
        recordForm: document.getElementById("recordForm"),
        recordModalTitle: document.getElementById("recordModalTitle")
    };

    function pick(res) {
        return res && res.data !== undefined ? res.data : res;
    }

    function openModal(modal) {
        modal.classList.add("is-open");
    }

    function closeModal(modal) {
        modal.classList.remove("is-open");
    }

    function typeBadge(type) {
        if (type === "video") {
            return '<span class="badge badge--video"><i data-lucide="video"></i>视频</span>';
        }
        return '<span class="badge badge--image"><i data-lucide="image"></i>图片</span>';
    }

    const STATUS = {
        completed: { cls: "badge--ok", text: "已完成" },
        processing: { cls: "badge--warn", text: "处理中" },
        failed: { cls: "badge--err", text: "失败" }
    };

    function statusBadge(status) {
        const s = STATUS[status] || { cls: "", text: status || "-" };
        return '<span class="badge ' + s.cls + '">' + App.escapeHtml(s.text) + "</span>";
    }

    function roleBadge(role) {
        if (role === "admin") {
            return '<span class="badge badge--ok">管理员</span>';
        }
        return '<span class="badge">普通用户</span>';
    }

    function userStatusBadge(status) {
        if (status === 1) {
            return '<span class="badge badge--ok">正常</span>';
        }
        return '<span class="badge badge--err">已禁用</span>';
    }

    /* ---------------- 用户管理 ---------------- */

    function renderUsers(data) {
        const items = data.items || [];

        state.users.total = data.total || 0;
        state.users.pages = Math.max(1, data.pages || 1);
        state.users.page = data.page || 1;

        state.userMap = {};
        items.forEach(function (item) {
            state.userMap[item.user_id] = item;
        });

        el.usersTableWrap.classList.toggle("hidden", items.length === 0);
        el.usersEmpty.classList.toggle("hidden", items.length > 0);

        el.usersBody.innerHTML = items.map(function (u) {
            const nextStatus = u.status === 1 ? 0 : 1;
            const toggleText = u.status === 1 ? "禁用" : "启用";
            const toggleClass = u.status === 1 ? "btn--danger" : "";

            return (
                "<tr>" +
                '<td class="num">' + u.user_id + "</td>" +
                '<td class="name">' + App.escapeHtml(u.username) + "</td>" +
                '<td class="muted">' + App.escapeHtml(u.email || "-") + "</td>" +
                "<td>" + roleBadge(u.role) + "</td>" +
                "<td>" + userStatusBadge(u.status) + "</td>" +
                '<td class="num">' + App.formatNumber(u.record_count || 0) + "</td>" +
                '<td class="muted">' + App.formatDateTime(u.created_at) + "</td>" +
                '<td><div class="table__actions">' +
                '<button class="btn btn--sm" type="button" data-edit-user="' + u.user_id + '">' +
                '<i data-lucide="pencil"></i>编辑</button>' +
                '<button class="btn btn--sm ' + toggleClass + '" type="button" data-toggle-user="' +
                u.user_id + '" data-status="' + nextStatus + '">' +
                '<i data-lucide="power"></i>' + toggleText + "</button>" +
                '<button class="btn btn--sm" type="button" data-reset-user="' + u.user_id + '">' +
                '<i data-lucide="key-round"></i>重置</button>' +
                '<button class="btn btn--sm btn--danger" type="button" data-delete-user="' +
                u.user_id + '"><i data-lucide="trash-2"></i>删除</button>' +
                "</div></td></tr>"
            );
        }).join("");

        el.userCountBadge.textContent = "共 " + state.users.total + " 个用户";
        el.usersPagerInfo.textContent = "第 " + state.users.page + " / " +
            state.users.pages + " 页";
        el.usersPrevBtn.disabled = state.users.page <= 1;
        el.usersNextBtn.disabled = state.users.page >= state.users.pages;

        App.icons();
    }

    async function loadUsers() {
        try {
            const res = await App.api("/api/admin/users", {
                query: {
                    page: state.users.page,
                    page_size: state.users.pageSize,
                    keyword: state.users.keyword,
                    status: state.users.status,
                    role: state.users.role
                }
            });
            renderUsers(pick(res) || {});
        } catch (err) {
            App.toast(err.message, "err");
        }
    }

    function openUserModal(mode, userData) {
        el.userForm.reset();
        el.userModalTitle.textContent = mode === "create" ? "新增用户" : "编辑用户";
        el.userPasswordField.classList.toggle("hidden", mode !== "create");
        el.userStatusField.classList.toggle("hidden", mode === "create");

        el.userForm.user_id.value = mode === "create" ? "" : userData.user_id;

        if (mode === "create") {
            el.userForm.role.value = "user";
            el.userForm.status.value = "1";
        } else {
            el.userForm.username.value = userData.username || "";
            el.userForm.email.value = userData.email || "";
            el.userForm.role.value = userData.role || "user";
            el.userForm.status.value = String(userData.status);
        }

        openModal(el.userModal);
        setTimeout(function () {
            el.userForm.username.focus();
        }, 60);
    }

    el.userForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const userId = el.userForm.user_id.value;
        const payload = {
            username: el.userForm.username.value.trim(),
            email: el.userForm.email.value.trim(),
            role: el.userForm.role.value
        };

        if (payload.username.length < 3) {
            App.toast("用户名长度不能少于 3 位", "warn");
            return;
        }

        try {
            if (userId) {
                payload.status = Number(el.userForm.status.value);
                await App.api("/api/admin/users/" + userId, {
                    method: "PUT",
                    body: payload
                });
                App.toast("用户资料已修改", "ok");
            } else {
                payload.password = el.userForm.password.value;
                if (!payload.password || payload.password.length < 6) {
                    App.toast("初始密码不能少于 6 位", "warn");
                    return;
                }
                await App.api("/api/admin/users", {
                    method: "POST",
                    body: payload
                });
                App.toast("用户已创建", "ok");
            }

            closeModal(el.userModal);
            loadUsers();
        } catch (err) {
            App.toast(err.message, "err");
        }
    });

    async function toggleUserStatus(userId, status) {
        try {
            await App.api("/api/admin/users/" + userId + "/status", {
                method: "PATCH",
                body: { status: status }
            });
            App.toast(status === 1 ? "用户已启用" : "用户已禁用", "ok");
            loadUsers();
        } catch (err) {
            App.toast(err.message, "err");
        }
    }

    function openResetPassword(userData) {
        el.resetPwdForm.reset();
        el.resetPwdForm.user_id.value = userData.user_id;
        el.resetPwdTitle.textContent = "重置密码 · " + userData.username;
        openModal(el.resetPwdModal);
        setTimeout(function () {
            el.resetPwdForm.new_password.focus();
        }, 60);
    }

    el.resetPwdForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const userId = el.resetPwdForm.user_id.value;
        const password = el.resetPwdForm.new_password.value;

        if (!password || password.length < 6) {
            App.toast("新密码不能少于 6 位", "warn");
            return;
        }

        try {
            await App.api(
                "/api/admin/users/" + userId + "/reset-password",
                { method: "POST", body: { new_password: password } }
            );
            App.toast("密码已重置", "ok");
            closeModal(el.resetPwdModal);
        } catch (err) {
            App.toast(err.message, "err");
        }
    });

    async function deleteUser(userData) {
        const message = "确定删除用户「" + userData.username + "」吗？\n" +
            "该用户的 " + (userData.record_count || 0) +
            " 条检测记录及结果文件也会被物理删除，且不可恢复。";

        if (!confirm(message)) return;

        try {
            await App.api("/api/admin/users/" + userData.user_id, {
                method: "DELETE"
            });
            App.toast("用户已删除", "ok");
            loadUsers();
            loadRecords();
        } catch (err) {
            App.toast(err.message, "err");
        }
    }

    /* ---------------- 检测记录管理 ---------------- */

    function renderRecords(data) {
        const items = data.items || [];

        state.records.total = data.total || 0;
        state.records.pages = Math.max(1, data.pages || 1);
        state.records.page = data.page || 1;

        state.recordMap = {};
        items.forEach(function (item) {
            state.recordMap[item.id] = item;
        });

        el.recordsTableWrap.classList.toggle("hidden", items.length === 0);
        el.recordsEmpty.classList.toggle("hidden", items.length > 0);

        el.recordsBody.innerHTML = items.map(function (r) {
            return (
                "<tr>" +
                '<td class="num">' + r.id + "</td>" +
                '<td class="name">' +
                App.escapeHtml(r.username || ("#" + r.user_id)) + "</td>" +
                "<td>" + typeBadge(r.task_type) + "</td>" +
                '<td class="name" title="' + App.escapeHtml(r.original_name) + '">' +
                App.escapeHtml(r.original_name) + "</td>" +
                "<td>" + statusBadge(r.status) + "</td>" +
                '<td class="num">' + App.formatNumber(r.object_count || 0) + "</td>" +
                '<td class="muted">' + App.formatDateTime(r.created_at) + "</td>" +
                '<td><div class="table__actions">' +
                '<button class="btn btn--sm" type="button" data-edit-record="' +
                r.id + '"><i data-lucide="pencil"></i>编辑</button>' +
                '<button class="btn btn--sm btn--danger" type="button" data-delete-record="' +
                r.id + '"><i data-lucide="trash-2"></i>删除</button>' +
                "</div></td></tr>"
            );
        }).join("");

        el.recordCountBadge.textContent = "共 " + state.records.total + " 条记录";
        el.recordsPagerInfo.textContent = "第 " + state.records.page + " / " +
            state.records.pages + " 页";
        el.recordsPrevBtn.disabled = state.records.page <= 1;
        el.recordsNextBtn.disabled = state.records.page >= state.records.pages;

        App.icons();
    }

    async function loadRecords() {
        try {
            const res = await App.api("/api/history", {
                query: {
                    page: state.records.page,
                    page_size: state.records.pageSize,
                    username: state.records.username,
                    filename: state.records.filename,
                    start_date: state.records.start,
                    end_date: state.records.end,
                    task_type: state.records.type,
                    status: state.records.status
                }
            });
            renderRecords(pick(res) || {});
        } catch (err) {
            App.toast(err.message, "err");
        }
    }

    function openRecordModal(record) {
        el.recordForm.reset();
        el.recordForm.record_id.value = record.id;
        el.recordForm.original_name.value = record.original_name || "";
        el.recordForm.remark.value = record.remark || "";
        el.recordForm.status.value = record.status || "completed";
        el.recordModalTitle.textContent = "修改检测记录 #" + record.id;
        openModal(el.recordModal);
    }

    el.recordForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const recordId = el.recordForm.record_id.value;

        try {
            await App.api("/api/history/" + recordId, {
                method: "PUT",
                body: {
                    original_name: el.recordForm.original_name.value.trim(),
                    remark: el.recordForm.remark.value.trim(),
                    status: el.recordForm.status.value
                }
            });
            App.toast("检测记录已修改", "ok");
            closeModal(el.recordModal);
            loadRecords();
        } catch (err) {
            App.toast(err.message, "err");
        }
    });

    async function deleteRecord(record) {
        if (!confirm(
            "确定物理删除检测记录 #" + record.id +
            "（" + record.original_name + "）吗？\n" +
            "原始文件、结果文件和类别统计都会一并删除。"
        )) return;

        try {
            await App.api("/api/history/" + record.id, {
                method: "DELETE"
            });
            App.toast("检测记录已删除", "ok");
            loadRecords();
        } catch (err) {
            App.toast(err.message, "err");
        }
    }

    /* ---------------- Tab / 事件 ---------------- */

    function switchTab(tab) {
        state.tab = tab;

        document.querySelectorAll("#adminTabs .segmented__item").forEach(function (btn) {
            btn.classList.toggle(
                "is-active",
                btn.getAttribute("data-tab") === tab
            );
        });

        el.usersPanel.classList.toggle("hidden", tab !== "users");
        el.recordsPanel.classList.toggle("hidden", tab !== "records");
    }

    document.querySelectorAll("#adminTabs .segmented__item").forEach(function (btn) {
        btn.addEventListener("click", function () {
            switchTab(btn.getAttribute("data-tab"));
        });
    });

    document.getElementById("addUserBtn").addEventListener("click", function () {
        openUserModal("create");
    });
    document.getElementById("refreshUsersBtn").addEventListener("click", loadUsers);
    document.getElementById("searchUsersBtn").addEventListener("click", function () {
        state.users.keyword = el.userKeyword.value.trim();
        state.users.status = el.userStatusFilter.value;
        state.users.role = el.userRoleFilter.value;
        state.users.page = 1;
        loadUsers();
    });
    document.getElementById("resetUsersBtn").addEventListener("click", function () {
        el.userKeyword.value = "";
        el.userStatusFilter.value = "";
        el.userRoleFilter.value = "";
        state.users.keyword = "";
        state.users.status = "";
        state.users.role = "";
        state.users.page = 1;
        loadUsers();
    });
    el.usersPrevBtn.addEventListener("click", function () {
        if (state.users.page > 1) {
            state.users.page--;
            loadUsers();
        }
    });
    el.usersNextBtn.addEventListener("click", function () {
        if (state.users.page < state.users.pages) {
            state.users.page++;
            loadUsers();
        }
    });

    document.getElementById("searchRecordsBtn").addEventListener("click", function () {
        state.records.username = el.recordUsername.value.trim();
        state.records.filename = el.recordFilename.value.trim();
        state.records.start = el.recordStart.value;
        state.records.end = el.recordEnd.value;
        state.records.type = el.recordType.value;
        state.records.status = el.recordStatus.value;
        state.records.page = 1;
        loadRecords();
    });
    document.getElementById("resetRecordsBtn").addEventListener("click", function () {
        el.recordUsername.value = "";
        el.recordFilename.value = "";
        el.recordStart.value = "";
        el.recordEnd.value = "";
        el.recordType.value = "";
        el.recordStatus.value = "";
        state.records.username = "";
        state.records.filename = "";
        state.records.start = "";
        state.records.end = "";
        state.records.type = "";
        state.records.status = "";
        state.records.page = 1;
        loadRecords();
    });
    el.recordsPrevBtn.addEventListener("click", function () {
        if (state.records.page > 1) {
            state.records.page--;
            loadRecords();
        }
    });
    el.recordsNextBtn.addEventListener("click", function () {
        if (state.records.page < state.records.pages) {
            state.records.page++;
            loadRecords();
        }
    });

    document.addEventListener("click", function (e) {
        const editUser = e.target.closest("[data-edit-user]");
        if (editUser) {
            const data = state.userMap[editUser.getAttribute("data-edit-user")];
            if (data) openUserModal("edit", data);
            return;
        }

        const toggleUser = e.target.closest("[data-toggle-user]");
        if (toggleUser) {
            toggleUserStatus(
                toggleUser.getAttribute("data-toggle-user"),
                Number(toggleUser.getAttribute("data-status"))
            );
            return;
        }

        const resetUser = e.target.closest("[data-reset-user]");
        if (resetUser) {
            const data = state.userMap[resetUser.getAttribute("data-reset-user")];
            if (data) openResetPassword(data);
            return;
        }

        const deleteUserBtn = e.target.closest("[data-delete-user]");
        if (deleteUserBtn) {
            const data = state.userMap[deleteUserBtn.getAttribute("data-delete-user")];
            if (data) deleteUser(data);
            return;
        }

        const editRecord = e.target.closest("[data-edit-record]");
        if (editRecord) {
            const data = state.recordMap[editRecord.getAttribute("data-edit-record")];
            if (data) openRecordModal(data);
            return;
        }

        const deleteRecordBtn = e.target.closest("[data-delete-record]");
        if (deleteRecordBtn) {
            const data = state.recordMap[deleteRecordBtn.getAttribute("data-delete-record")];
            if (data) deleteRecord(data);
        }
    });

    [el.userModal, el.resetPwdModal, el.recordModal].forEach(function (modal) {
        modal.addEventListener("click", function (e) {
            if (e.target === modal || e.target.closest("[data-close]")) {
                closeModal(modal);
            }
        });
    });

    loadUsers();
    loadRecords();
})();
