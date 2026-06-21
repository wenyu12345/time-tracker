// ============== API 请求封装 ==============
// 关键：根据当前页面 origin 自动推导 API 目标地址
// 若页面是从 http://127.0.0.1:5000/ 加载的 → API 目标 = http://127.0.0.1:5000/api
// 若页面是从 file:// 或其他非 http 协议加载的 → 回退到 http://127.0.0.1:5000/api
(function() {
    let base = '/api';
    try {
        if (typeof window !== 'undefined' && window.location) {
            const proto = window.location.protocol;
            const host = window.location.host; // 含端口，如 "127.0.0.1:5000"
            if (proto === 'file:' || !proto || proto === 'about:') {
                // 直接双击 index.html 的情况：必须显式指向本地 Flask
                base = 'http://127.0.0.1:5000/api';
                console.warn('[api.js] 页面是从 file:// 或异常协议加载，API 目标强制回退到', base);
            } else if (proto === 'http:' || proto === 'https:') {
                // 正常情况：保留相对路径（同源请求）
                base = '/api';
            } else {
                base = 'http://127.0.0.1:5000/api';
            }
        }
    } catch (e) { /* 无法判断时回退 */ base = '/api'; }

    window.__API_BASE_URL__ = base;
    try { window.__PAGE_ORIGIN__ = (typeof window !== 'undefined' && window.location) ? window.location.href : 'unknown'; } catch(e) { window.__PAGE_ORIGIN__ = 'unknown'; }
    console.log('[api.js] 初始化完成：API_BASE =', base, '，页面URL =', window.__PAGE_ORIGIN__);
})();
const API_BASE_URL = (typeof window !== 'undefined' && window.__API_BASE_URL__) || '/api';

// 通用请求函数
async function fetchAPI(endpoint, options) {
    const defaultOptions = { headers: { 'Content-Type': 'application/json' } };
    const mergedOptions = Object.assign({}, defaultOptions, options || {});

    try {
        const url = API_BASE_URL + endpoint;
        const response = await fetch(url, mergedOptions);

        if (!response.ok) {
            const errorData = await response.json().catch(function() { return {}; });
            throw new Error((errorData.error || 'API请求失败: HTTP ' + response.status));
        }
        return await response.json();
    } catch (error) {
        // 让浏览器层面的失败（网络不可达/CORS/端口没服务）给出清晰的诊断信息
        const msg = (error && error.message) ? error.message : String(error);
        if (msg.indexOf('Failed to fetch') >= 0 || msg.indexOf('NetworkError') >= 0 || msg.indexOf('拒绝') >= 0) {
            console.error(
                '[api.js] ❌ 浏览器无法连接到后端。目标地址:', API_BASE_URL + endpoint,
                '请确认：',
                '① Flask 进程是否在运行？当前页面地址: ', (typeof window !== 'undefined' && window.location && window.location.href),
                '② 是否以 http://127.0.0.1:5000/ 打开页面（不是双击 index.html）',
                '原始错误:', error
            );
            throw new Error('❌ 无法连接后端服务。请确认：Flask已启动，且页面是通过 http://127.0.0.1:5000/ 打开的。详情: ' + msg);
        }
        console.error('API请求错误:', error, '| URL:', API_BASE_URL + endpoint);
        throw error;
    }
}

// 认证相关API
const authAPI = {
    register: async function(userData) {
        console.log('发送注册请求:', userData);
        try {
            const response = await fetchAPI('/auth/register', {
                method: 'POST',
                body: JSON.stringify(userData),
            });
            console.log('注册请求成功:', response);
            return response;
        } catch (error) {
            console.error('注册请求失败:', error);
            throw error;
        }
    },
    
    login: function(credentials) {
        return fetchAPI('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
    },
    
    getUser: function(userId) {
        return fetchAPI('/auth/user?user_id=' + userId);
    },
    
    updateSalaryLevel: function(userId, salaryLevel) {
        return fetchAPI('/auth/user/salary-level', {
            method: 'PUT',
            body: JSON.stringify({
                user_id: userId,
                salary_level: salaryLevel
            }),
        });
    },
    
    updatePassword: function(data) {
        return fetchAPI('/auth/user/password', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
};

// 项目相关API
const projectAPI = {
    getProjects: function(userId) {
        return fetchAPI('/projects?user_id=' + userId);
    },
    
    createProject: function(projectData) {
        return fetchAPI('/projects', {
            method: 'POST',
            body: JSON.stringify(projectData),
        });
    },
    
    getProject: function(projectId) {
        return fetchAPI('/projects/' + projectId);
    },
    
    updateProject: function(projectId, projectData) {
        return fetchAPI('/projects/' + projectId, {
            method: 'PUT',
            body: JSON.stringify(projectData),
        });
    },
    
    deleteProject: function(projectId) {
        return fetchAPI('/projects/' + projectId, {
            method: 'DELETE',
        });
    },
};

// 工时记录相关API
const timeRecordAPI = {
    getTimeRecords: function(userId, filters) {
        const queryParams = new URLSearchParams({ user_id: userId });
        if (filters && filters.start_date) {
            queryParams.append('start_date', filters.start_date);
        }
        if (filters && filters.end_date) {
            queryParams.append('end_date', filters.end_date);
        }
        return fetchAPI('/time-records?' + queryParams.toString());
    },
    
    createTimeRecord: function(recordData) {
        return fetchAPI('/time-records', {
            method: 'POST',
            body: JSON.stringify(recordData),
        });
    },
    
    updateTimeRecord: function(recordId, recordData) {
        // 从recordData中提取user_id，然后将其作为查询参数传递
        const userId = recordData.user_id;
        // 删除recordData中的user_id，因为后端API不期望在请求体中接收user_id
        delete recordData.user_id;
        
        return fetchAPI('/time-records/' + recordId + '?user_id=' + userId, {
            method: 'PUT',
            body: JSON.stringify(recordData),
        });
    },
    
    startRecord: function(recordData) {
        return fetchAPI('/time-records/start', {
            method: 'POST',
            body: JSON.stringify(recordData),
        });
    },
    
    stopRecord: function(recordId) {
        return fetchAPI('/time-records/stop', {
            method: 'POST',
            body: JSON.stringify({ record_id: recordId }),
        });
    },
    
    batchUpdate: function(userId, records) {
        return fetchAPI('/time-records/batch', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, records: records }),
        });
    },
    
    deleteRecord: function(recordId, userId) {
        return fetchAPI('/time-records/' + recordId + '?user_id=' + userId, {
            method: 'DELETE',
        });
    },
};

// 统计相关API
const statsAPI = {
    getDailyStats: function(userId, date) {
        return fetchAPI('/stats/daily?user_id=' + userId + '&date=' + date);
    },
    
    getWeeklyStats: function(userId, year, week) {
        return fetchAPI('/stats/weekly?user_id=' + userId + '&year=' + year + '&week=' + week);
    },
    
    getMonthlyStats: function(userId, month) {
        return fetchAPI('/stats/monthly?user_id=' + userId + '&month=' + month);
    },
    
    getProjectStats: function(userId, filters) {
        const queryParams = new URLSearchParams({ user_id: userId });
        if (filters && filters.start_date) {
            queryParams.append('start_date', filters.start_date);
        }
        if (filters && filters.end_date) {
            queryParams.append('end_date', filters.end_date);
        }
        return fetchAPI('/stats/project?' + queryParams.toString());
    },
    
    getShiftStats: function(userId, filters) {
        const queryParams = new URLSearchParams({ user_id: userId });
        if (filters && filters.start_date) {
            queryParams.append('start_date', filters.start_date);
        }
        if (filters && filters.end_date) {
            queryParams.append('end_date', filters.end_date);
        }
        return fetchAPI('/stats/shift?' + queryParams.toString());
    },
    
    getTrendStats: function(userId, startDate, endDate) {
        const queryParams = new URLSearchParams({ user_id: userId });
        queryParams.append('start_date', `${startDate} 00:00:00`);
        queryParams.append('end_date', `${endDate} 23:59:59`);
        return fetchAPI('/stats/trend?' + queryParams.toString());
    },
    
    getCustomStats: function(userId, startDate, endDate) {
        const queryParams = new URLSearchParams({ user_id: userId });
        queryParams.append('start_date', `${startDate} 00:00:00`);
        queryParams.append('end_date', `${endDate} 23:59:59`);
        return fetchAPI('/stats/project?' + queryParams.toString());
    },
    
    getAttendanceStats: function(userId, startDate, endDate) {
        const queryParams = new URLSearchParams({ user_id: userId });
        queryParams.append('start_date', `${startDate} 00:00:00`);
        queryParams.append('end_date', `${endDate} 23:59:59`);
        return fetchAPI('/stats/attendance?' + queryParams.toString());
    },
    
    getOvertimeStats: function(userId, startDate, endDate, standardHours = 8) {
        const queryParams = new URLSearchParams({ user_id: userId });
        queryParams.append('start_date', `${startDate} 00:00:00`);
        queryParams.append('end_date', `${endDate} 23:59:59`);
        queryParams.append('standard_hours', standardHours);
        return fetchAPI('/stats/overtime?' + queryParams.toString());
    },
    
    getHoursDistribution: function(userId, startDate, endDate) {
        const queryParams = new URLSearchParams({ user_id: userId });
        queryParams.append('start_date', `${startDate} 00:00:00`);
        queryParams.append('end_date', `${endDate} 23:59:59`);
        return fetchAPI('/stats/distribution?' + queryParams.toString());
    },
    
    getComparisonStats: function(userId, period = 'month', date = new Date().toISOString().split('T')[0]) {
        const queryParams = new URLSearchParams({ user_id: userId });
        queryParams.append('period', period);
        queryParams.append('date', date);
        return fetchAPI('/stats/comparison?' + queryParams.toString());
    },
};

// 工资相关API
const salaryAPI = {
    saveSalaryInfo: function(salaryData) {
        return fetchAPI('/salary/info', {
            method: 'POST',
            body: JSON.stringify(salaryData),
        });
    },
    
    getSalaryInfo: function(userId, month) {
        return fetchAPI('/salary/info/' + month + '?user_id=' + userId);
    },
    
    calculateSalary: function(userId, month, simulatedHours) {
        const queryParams = new URLSearchParams({ user_id: userId, month: month });
        if (simulatedHours > 0) {
            queryParams.append('simulated_hours', simulatedHours);
        }
        return fetchAPI('/salary/calculate?' + queryParams.toString());
    },
    
    getSalaryLevels: function() {
        return fetchAPI('/salary/levels');
    },
};

// 排班相关API
const scheduleAPI = {
    getSchedules: function(userId) {
        return fetchAPI('/admin/schedules/user/' + userId);
    },
    
    getSchedulesByDate: function(date) {
        return fetchAPI('/admin/schedules/date/' + date);
    },
    
    deleteSchedule: function(scheduleId) {
        return fetchAPI('/admin/schedules/' + scheduleId, {
            method: 'DELETE',
        });
    },
    
    deleteExpiredSchedules: function() {
        return fetchAPI('/admin/schedules/expired', {
            method: 'DELETE',
        });
    },
};

// 留言相关API
const messageAPI = {
    getMessages: function(page = 1, per_page = 20) {
        return fetchAPI('/messages?page=' + page + '&per_page=' + per_page);
    },
    
    createMessage: function(messageData) {
        return fetchAPI('/messages', {
            method: 'POST',
            body: JSON.stringify(messageData),
        });
    },
    
    deleteMessage: function(messageId) {
        return fetchAPI('/messages/' + messageId, {
            method: 'DELETE',
        });
    },
};

// 用户在线记录API
const onlineAPI = {
    recordUserOnline: function(user_id, username) {
        return fetchAPI(`/admin/user-online-logs?user_id=${user_id}&username=${encodeURIComponent(username)}`, {
            method: 'POST',
        });
    },
    
    getUserOnlineLogs: function(date) {
        return fetchAPI(`/admin/user-online-logs?date=${date}`);
    },
    
    getTodayUserOnlineLogs: function() {
        return fetchAPI('/admin/user-online-logs/today');
    },
    
    getUserOnlineStats: function(start_date, end_date) {
        return fetchAPI(`/admin/user-online-logs/stats?start_date=${start_date}&end_date=${end_date}`);
    },
};

// 角色相关API
const roleAPI = {
    getRoles: function() {
        return fetchAPI('/admin/roles');
    },
    
    getUserRoles: function(userId) {
        return fetchAPI(`/admin/users/${userId}/roles`);
    },
    
    getUsersByRole: function(roleId) {
        return fetchAPI(`/admin/roles/${roleId}/users`);
    },
    
    assignRoles: function(userId, roleIds) {
        return fetchAPI(`/admin/users/${userId}/roles`, {
            method: 'POST',
            body: JSON.stringify({ role_ids: roleIds }),
        });
    },
};

// 管理系统API
const adminAPI = {
    // 管理员认证
    adminLogin: function(credentials) {
        return fetchAPI('/admin/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
    },
    
    adminLogout: function() {
        return fetchAPI('/admin/logout', {
            method: 'POST',
        });
    },
    
    // 用户管理
    getUsers: function() {
        return fetchAPI('/admin/users');
    },
    
    getUser: function(userId) {
        return fetchAPI(`/admin/users/${userId}`);
    },
    
    addUser: function(userData) {
        return fetchAPI('/admin/users', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    },
    
    updateUser: function(userId, userData) {
        return fetchAPI(`/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData),
        });
    },
    
    deleteUser: function(userId) {
        return fetchAPI(`/admin/users/${userId}`, {
            method: 'DELETE',
        });
    },
    
    searchUsers: function(searchTerm) {
        return fetchAPI(`/admin/users/search?keyword=${encodeURIComponent(searchTerm)}`);
    },
    
    // 角色管理
    addRole: function(roleData) {
        return fetchAPI('/admin/roles', {
            method: 'POST',
            body: JSON.stringify(roleData),
        });
    },
    
    updateRole: function(roleId, roleData) {
        return fetchAPI(`/admin/roles/${roleId}`, {
            method: 'PUT',
            body: JSON.stringify(roleData),
        });
    },
    
    deleteRole: function(roleId) {
        return fetchAPI(`/admin/roles/${roleId}`, {
            method: 'DELETE',
        });
    },
    
    getRole: function(roleId) {
        return fetchAPI(`/admin/roles/${roleId}`);
    },
    
    // 权限管理
    getPermissions: function() {
        return fetchAPI('/admin/permissions');
    },
    
    addPermission: function(permissionData) {
        return fetchAPI('/admin/permissions', {
            method: 'POST',
            body: JSON.stringify(permissionData),
        });
    },
    
    updatePermission: function(permissionId, permissionData) {
        return fetchAPI(`/admin/permissions/${permissionId}`, {
            method: 'PUT',
            body: JSON.stringify(permissionData),
        });
    },
    
    deletePermission: function(permissionId) {
        return fetchAPI(`/admin/permissions/${permissionId}`, {
            method: 'DELETE',
        });
    },
    
    getPermission: function(permissionId) {
        return fetchAPI(`/admin/permissions/${permissionId}`);
    },
    
    // 排班管理
    getSchedules: function() {
        return fetchAPI('/admin/schedules');
    },
    
    getSchedule: function(scheduleId) {
        return fetchAPI(`/admin/schedules/${scheduleId}`);
    },
    
    addSchedule: function(scheduleData) {
        return fetchAPI('/admin/schedules', {
            method: 'POST',
            body: JSON.stringify(scheduleData),
        });
    },
    
    batchSchedule: function(batchData) {
        return fetchAPI('/admin/schedules/batch', {
            method: 'POST',
            body: JSON.stringify(batchData),
        });
    },
    
    updateSchedule: function(scheduleId, scheduleData) {
        return fetchAPI(`/admin/schedules/${scheduleId}`, {
            method: 'PUT',
            body: JSON.stringify(scheduleData),
        });
    },
    
    deleteSchedule: function(scheduleId) {
        return fetchAPI(`/admin/schedules/${scheduleId}`, {
            method: 'DELETE',
        });
    },
    
    deleteExpiredSchedules: function() {
        return fetchAPI('/admin/schedules/expired', {
            method: 'DELETE',
        });
    },
    
    // 工资管理
    getSalaryConfig: function() {
        return fetchAPI('/salary/config');
    },
    
    getSalaryConfigById: function(configId) {
        return fetchAPI(`/salary/config/${configId}`);
    },
    
    updateSalaryConfig: function(configId, configData) {
        return fetchAPI('/salary/config', {
            method: 'POST',
            body: JSON.stringify(configData),
        });
    },
    
    resetSalaryConfig: function() {
        return fetchAPI('/salary/config/reset', {
            method: 'POST',
        });
    },
    
    calculateSalary: function(userId, month, simulatedHours = 0) {
        const params = new URLSearchParams({ user_id: userId, month: month });
        if (simulatedHours > 0) {
            params.append('simulated_hours', simulatedHours);
        }
        return fetchAPI(`/salary/calculate?${params.toString()}`);
    },
    
    // 统计分析
    getAdminStats: function(type, startDate = '', endDate = '') {
        const params = new URLSearchParams();
        if (startDate) {
            params.append('start_date', startDate);
        }
        if (endDate) {
            params.append('end_date', endDate);
        }
        return fetchAPI(`/admin/stats/${type}?${params.toString()}`);
    },
    
    // 工时记录管理
    getTimeRecords: function() {
        return fetchAPI('/admin/time-records');
    },
    
    searchTimeRecords: function(searchTerm) {
        return fetchAPI(`/admin/time-records/search?keyword=${encodeURIComponent(searchTerm)}`);
    },
    
    checkDuplicateTimeRecords: function() {
        return fetchAPI('/admin/time-records/check-duplicates');
    },
    
    // 操作日志
    getOperationLogs: function(limit = 20) {
        return fetchAPI(`/admin/operation-logs?limit=${limit}`);
    },
    
    // 自动任务管理器
    getSchedulerJobs: function() {
        return fetchAPI('/scheduler/jobs');
    },
    
    executeSchedulerJob: function(jobName) {
        return fetchAPI('/scheduler/jobs/execute', {
            method: 'POST',
            body: JSON.stringify({ job_name: jobName }),
        });
    },
    
    toggleSchedulerJob: function(jobName) {
        return fetchAPI(`/scheduler/jobs/${jobName}/toggle`, {
            method: 'PATCH',
        });
    },
    
    getSchedulerLogs: function(limit = 20) {
        return fetchAPI(`/scheduler/logs?limit=${limit}`);
    },
    
    // 数据备份
    createBackup: function() {
        return fetchAPI('/backup', {
            method: 'GET',
        });
    },
    
    getBackupList: function() {
        return fetchAPI('/backup/list');
    },
    
    deleteBackup: function(filename) {
        return fetchAPI(`/backup/${filename}`, {
            method: 'DELETE',
        });
    },
    
    restoreBackup: function(filename) {
        return fetchAPI('/backup/restore', {
            method: 'POST',
            body: JSON.stringify({ filename: filename }),
        });
    },
    
    autoBackup: function() {
        return fetchAPI('/backup/auto', {
            method: 'GET',
        });
    },
    
    // 报表管理
    // 每日出勤报表
    getDailyAttendanceReport: function(startDate, endDate, roleId) {
        let apiUrl;
        if (startDate && endDate) {
            apiUrl = `/admin/time-records/range/${startDate}/${endDate}`;
        } else {
            apiUrl = `/admin/time-records/date/${startDate}`;
        }
        
        // 如果提供了角色ID，添加到查询参数
        if (roleId) {
            apiUrl += `?role_id=${roleId}`;
        }
        
        return fetchAPI(apiUrl);
    },
    
    // 个人出勤报表
    getPersonalAttendanceReport: function(userId, startDate, endDate) {
        return fetchAPI(`/time-records?user_id=${userId}&start_date=${startDate} 00:00:00&end_date=${endDate} 23:59:59`);
    },
    
    // 定时任务报表
    getSchedulerStats: function() {
        return fetchAPI('/scheduler/stats');
    },
    
    // 登录报表
    getUserLoginStats: function() {
        return fetchAPI('/admin/user-login-logs/stats');
    },
    
    getUserLoginLogs: function(startDate, endDate) {
        if (startDate && endDate) {
            return fetchAPI(`/admin/user-login-logs?start_date=${startDate}&end_date=${endDate}`);
        }
        return fetchAPI('/admin/user-login-logs');
    },
    
    // 在线用户报表
    getOnlineUsers: function() {
        return fetchAPI('/admin/user-online-logs');
    },
    
    // 获取所有用户
    getAllUsers: function() {
        return fetchAPI('/admin/users');
    },
    
    // 更新工时记录
    updateTimeRecord: function(recordId, data) {
        return fetchAPI(`/admin/time-records/${recordId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
    
    // 批量更新工时记录
    batchUpdateTimeRecords: function(batchData) {
        return fetchAPI('/admin/time-records/batch', {
            method: 'PUT',
            body: JSON.stringify(batchData),
        });
    },
    
    // 批量删除工时记录
    batchDeleteTimeRecords: function(batchData) {
        return fetchAPI('/admin/time-records/batch-delete', {
            method: 'DELETE',
            body: JSON.stringify(batchData),
        });
    },
    
    // 批量添加工时记录
    batchAddTimeRecords: function(batchData) {
        return fetchAPI('/admin/time-records/batch-add', {
            method: 'POST',
            body: JSON.stringify(batchData),
        });
    },
    
    // 将排班转换为工时记录
    schedulesToTimeRecords: function() {
        return fetchAPI('/admin/schedules/to-time-records', {
            method: 'POST',
        });
    },
    
    // 批量安排调休
    arrangeLeave: function(leaveData) {
        return fetchAPI('/admin/arrange-leave', {
            method: 'POST',
            body: JSON.stringify(leaveData),
        });
    },
    
    // Excel导入工时记录
    importExcelTimeRecords: function(formData) {
        return fetchAPI('/time-records/import-excel', {
            method: 'POST',
            body: formData,
            headers: {},
        });
    },
};

// 数独相关API
const sudokuAPI = {
    // 获取用户数独积分
    getScores: async function(userId) {
        return fetchAPI(`/sudoku/scores/${userId}`);
    },
    
    // 更新用户数独积分
    updateScores: async function(scoreData) {
        return fetchAPI('/sudoku/scores', {
            method: 'POST',
            body: JSON.stringify(scoreData),
        });
    },
    
    // 获取数独排行榜
    getLeaderboard: async function() {
        return fetchAPI('/sudoku/leaderboard');
    }
};

// 猜数字游戏相关API
const guessNumberAPI = {
    // 获取用户猜数字游戏统计数据
    getStats: async function(userId) {
        return fetchAPI(`/guess-number/stats?user_id=${userId}`);
    },
    
    // 更新用户猜数字游戏统计数据
    updateStats: async function(statsData) {
        return fetchAPI('/guess-number/stats', {
            method: 'POST',
            body: JSON.stringify(statsData),
        });
    },
    
    // 获取猜数字游戏排行榜
    getLeaderboard: async function() {
        return fetchAPI('/guess-number/leaderboard');
    }
};

// 通知相关API
const notificationAPI = {
    // 拉取未读通知
    pullNotifications: function(user_id, last_id = 0) {
        const query = new URLSearchParams({ user_id, last_id });
        return fetchAPI('/auth/notifications/pull?' + query.toString());
    },
    // 标记单条通知已读
    markAsRead: function(notification_id, user_id) {
        return fetchAPI(`/auth/notifications/${notification_id}/read`, {
            method: 'POST',
            body: JSON.stringify({ user_id })
        });
    },
    // 一键标记所有通知已读
    markAllAsRead: function(user_id) {
        return fetchAPI('/auth/notifications/read-all', {
            method: 'POST',
            body: JSON.stringify({ user_id })
        });
    }
};

// 导出API对象
const api = {
    ...authAPI,
    ...projectAPI,
    ...timeRecordAPI,
    ...statsAPI,
    ...salaryAPI,
    ...scheduleAPI,
    ...messageAPI,
    ...onlineAPI,
    ...roleAPI,
    ...adminAPI,
    ...sudokuAPI,
    ...guessNumberAPI,
    ...notificationAPI
};

// 暴露API对象到全局作用域
window.api = api;
window.notificationAPI = notificationAPI;