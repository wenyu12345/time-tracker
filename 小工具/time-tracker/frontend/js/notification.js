// 登录通知轮询与弹窗
let NOTIFICATION_POLL_INTERVAL = null;
let NOTIFICATION_LAST_ID = 0;

// 从 localStorage 恢复 last_id
function initNotificationState() {
    const saved = localStorage.getItem('notification_last_id');
    if (saved) {
        NOTIFICATION_LAST_ID = parseInt(saved, 10) || 0;
    }
}

// 持久化 last_id
function saveNotificationLastId() {
    localStorage.setItem('notification_last_id', String(NOTIFICATION_LAST_ID));
}

// 创建通知弹窗UI
function createNotificationModal() {
    if (document.getElementById('notification-modal-overlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'notification-modal-overlay';
    overlay.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;justify-content:center;align-items:center;font-family:"Microsoft YaHei",sans-serif;';
    overlay.innerHTML = `
        <div id="notification-modal" style="background:#fff;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.2);width:90%;max-width:420px;max-height:80vh;display:flex;flex-direction:column;">
            <div style="padding:16px 20px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center;">
                <h3 style="margin:0;font-size:16px;color:#333;">🔔 系统通知</h3>
                <button id="notification-close-btn" style="background:none;border:none;font-size:20px;cursor:pointer;color:#999;padding:0 8px;">×</button>
            </div>
            <div id="notification-list" style="padding:12px 20px;overflow-y:auto;flex:1;max-height:400px;"></div>
            <div style="padding:12px 20px;border-top:1px solid #eee;display:flex;justify-content:space-between;align-items:center;gap:10px;">
                <span id="notification-count" style="color:#888;font-size:13px;"></span>
                <div style="display:flex;gap:10px;">
                    <button id="notification-read-all-btn" style="padding:8px 16px;background:#4a90e2;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;">全部已读</button>
                    <button id="notification-close-btn2" style="padding:8px 16px;background:#f0f0f0;color:#333;border:none;border-radius:4px;cursor:pointer;font-size:13px;">关闭</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById('notification-close-btn').onclick = hideNotificationModal;
    document.getElementById('notification-close-btn2').onclick = hideNotificationModal;
    document.getElementById('notification-read-all-btn').onclick = handleReadAll;
    overlay.onclick = function(e) {
        if (e.target.id === 'notification-modal-overlay') hideNotificationModal();
    };
}

function showNotificationModal() {
    createNotificationModal();
    const overlay = document.getElementById('notification-modal-overlay');
    overlay.style.display = 'flex';
}

function hideNotificationModal() {
    const overlay = document.getElementById('notification-modal-overlay');
    if (overlay) overlay.style.display = 'none';
}

// 将时间格式化为中文格式（如：2026年6月10日 23时30分）
function formatChineseTime(timeStr) {
    if (!timeStr) return '';
    try {
        // 处理 "2026-06-09 23:30:00" 或 "2026-06-09T23:30:00" 格式
        const cleanStr = String(timeStr).replace('T', ' ').trim();
        const datePart = cleanStr.split(' ')[0];
        const timePart = cleanStr.split(' ')[1] || '';
        
        if (!datePart) return timeStr;
        
        const dateParts = datePart.split('-');
        if (dateParts.length < 3) return timeStr;
        
        const year = parseInt(dateParts[0], 10);
        const month = parseInt(dateParts[1], 10);
        const day = parseInt(dateParts[2], 10);
        
        let result = `${year}年${month}月${day}日`;
        
        if (timePart) {
            const timeParts = timePart.split(':');
            if (timeParts.length >= 2) {
                const hour = parseInt(timeParts[0], 10);
                const minute = parseInt(timeParts[1], 10);
                result += ` ${hour}时${minute}分`;
            }
        }
        return result;
    } catch (e) {
        return timeStr;
    }
}

// 渲染通知列表
function renderNotificationList(notifications) {
    createNotificationModal();
    const list = document.getElementById('notification-list');
    const countSpan = document.getElementById('notification-count');

    if (!notifications || notifications.length === 0) {
        list.innerHTML = '<div style="padding:40px 20px;text-align:center;color:#999;">暂无新通知</div>';
        countSpan.textContent = '';
        return;
    }

    countSpan.textContent = `共 ${notifications.length} 条未读通知`;

    list.innerHTML = notifications.map(n => `
        <div style="padding:12px 0;border-bottom:1px dashed #eee;">
            <div style="font-weight:600;color:#333;margin-bottom:6px;">${escapeHtml(n.title || '系统通知')}</div>
            <div style="color:#555;font-size:14px;line-height:1.6;margin-bottom:6px;">${escapeHtml(n.message || '')}</div>
            <div style="color:#aaa;font-size:12px;">🕐 ${escapeHtml(formatChineseTime(n.created_at))}</div>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 处理全部已读
async function handleReadAll() {
    const user = getCurrentUser();
    if (!user || !user.id) return;
    try {
        const result = await notificationAPI.markAllAsRead(user.id);
        if (result && result.success) {
            // 更新 last_id 为当前最大值
            const pullResult = await notificationAPI.pullNotifications(user.id, NOTIFICATION_LAST_ID);
            if (pullResult && typeof pullResult.latest_id === 'number' && pullResult.latest_id > NOTIFICATION_LAST_ID) {
                NOTIFICATION_LAST_ID = pullResult.latest_id;
                saveNotificationLastId();
            }
            const list = document.getElementById('notification-list');
            if (list) {
                list.innerHTML = '<div style="padding:40px 20px;text-align:center;color:#52c41a;">✅ 所有通知已标记为已读</div>';
            }
            const countSpan = document.getElementById('notification-count');
            if (countSpan) countSpan.textContent = '';
            // 1.5秒后自动关闭
            setTimeout(hideNotificationModal, 1500);
        }
    } catch (e) {
        console.error('一键已读失败:', e);
    }
}

// 拉取并处理一次通知
async function pullAndProcessNotifications() {
    const user = getCurrentUser();
    if (!user || !user.id) return;
    try {
        const result = await notificationAPI.pullNotifications(user.id, NOTIFICATION_LAST_ID);
        if (result && result.notifications && result.notifications.length > 0) {
            // 渲染通知列表并显示弹窗
            renderNotificationList(result.notifications);
            showNotificationModal();

            // 同时在后台逐个标记已读（作为备选）
            try {
                for (const notif of result.notifications) {
                    try {
                        await notificationAPI.markAsRead(notif.id, user.id);
                    } catch (e) {
                        // 静默忽略
                    }
                }
            } catch (e) {
                console.error('标记通知已读失败:', e);
            }

            // 更新 latest_id
            if (typeof result.latest_id === 'number' && result.latest_id > NOTIFICATION_LAST_ID) {
                NOTIFICATION_LAST_ID = result.latest_id;
                saveNotificationLastId();
            }
        }
    } catch (error) {
        // 静默忽略，避免影响用户
    }
}

// 启动轮询（仅在未启动时启动）
function startNotificationPolling() {
    initNotificationState();
    if (NOTIFICATION_POLL_INTERVAL) return;
    // 立即执行一次
    pullAndProcessNotifications();
    // 每 10 秒轮询一次
    NOTIFICATION_POLL_INTERVAL = setInterval(pullAndProcessNotifications, 10000);
    console.log('登录通知轮询已启动');
}

window.startNotificationPolling = startNotificationPolling;
