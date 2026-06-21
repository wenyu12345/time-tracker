// 应用主入口：DOMContentLoaded 后初始化所有功能模块
// 设计要点：
//   1. 每个模块独立 try-catch，一个失败不影响其他
//   2. 所有错误统一上报到 console 并由 boot.js 收集展示
//   3. boot.js 也会在页面加载后执行一次完整初始化（双保险）
(function () {
    'use strict';

    // 带错误防护的初始化：返回 { name, ok, error }
    function safeInit(name, fn) {
        try {
            const result = fn();
            if (result && typeof result.then === 'function') {
                result.catch(function (err) {
                    console.error('[' + name + '] 异步初始化失败:', err);
                    window.AppErrors = window.AppErrors || [];
                    window.AppErrors.push({ module: name, error: err.message });
                });
            }
            return { name: name, ok: true };
        } catch (err) {
            console.error('[' + name + '] 初始化失败:', err);
            window.AppErrors = window.AppErrors || [];
            window.AppErrors.push({ module: name, error: err.message });
            return { name: name, ok: false, error: err };
        }
    }

    document.addEventListener('DOMContentLoaded', async function () {
        // ============================================
        // 【最小化加载模式】启动时只加载：认证 + 考勤
        // 其他模块（工时/工资/基金/统计等）全部延迟，由用户点击 tab 时触发
        // tabs.js 的 switchTab -> initTabByName 会调用对应 init
        // ============================================

        // 1. 认证模块先初始化（需要登录态才能拉数据）
        try {
            if (typeof window.initAuth === 'function') {
                await window.initAuth();
            }
        } catch (err) {
            console.error('[认证] 初始化失败:', err);
            window.AppErrors = window.AppErrors || [];
            window.AppErrors.push({ module: '认证', error: err.message });
        }

        // 2. 登录通知轮询
        try {
            if (typeof window.isLoggedIn === 'function' && window.isLoggedIn() &&
                typeof window.startNotificationPolling === 'function') {
                window.startNotificationPolling();
            }
        } catch (err) {
            console.error('[通知轮询] 启动失败:', err);
        }

        // 3. 仅启动 考勤列表（首页）
        safeInit('考勤列表', function () {
            if (typeof window.initAttendance === 'function') window.initAttendance();
        });

        // 其他模块（工时/工资/工资配置/统计/留言墙/木鱼/数独/猜数字/基金/师徒）
        // 全部延迟：由 tabs.js 在用户点击对应 tab 时调用 initTabByName(tabName)
        console.log('%c[app.js] 🔸 最小化加载模式：仅认证 + 考勤，其他模块延迟到点击 tab 时加载', 'color:#ff9800;font-weight:bold');

        // 4. 自动记录工时
        try {
            if (typeof window.setupAutoRecord === 'function') window.setupAutoRecord();
        } catch (e) { /* 忽略 */ }

        // 5. 管理系统入口
        try { initRemoteAdmin(); } catch (e) { /* 忽略 */ }
        try { initAdminEntry(); } catch (e) { /* 忽略 */ }

        // 6. 记录用户在线
        try { recordUserOnline(); } catch (e) { /* 忽略 */ }

        console.log('%c✅ 应用主入口完成 (app.js) - 最小化加载', 'color:#4caf50;font-weight:bold');
    });

    // 记录用户在线访问
    async function recordUserOnline() {
        const user = window.getCurrentUser ? window.getCurrentUser() : null;
        if (!user) return;
        try {
            if (window.onlineAPI && typeof window.onlineAPI.recordUserOnline === 'function') {
                await window.onlineAPI.recordUserOnline(user.id, user.username);
            }
        } catch (error) {
            console.error('更新用户在线记录失败:', error);
        }
    }

    // 初始化远程打开管理系统功能
    function initRemoteAdmin() {
        const openAdminBtn = document.getElementById('open-admin-btn');
        if (openAdminBtn) {
            openAdminBtn.addEventListener('click', function () {
                window.open('http://localhost:5000', '_blank');
                alert('管理系统已打开，请查看新的浏览器标签页');
            });
        }
    }

    // 初始化管理系统入口功能
    function initAdminEntry() {
        const adminEntryBtn = document.getElementById('admin-entry-btn');
        if (adminEntryBtn) {
            adminEntryBtn.addEventListener('click', function () {
                window.location.href = '/admin.html';
            });
        }
    }
})();
