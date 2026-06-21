// 出勤名单功能
(function() {
    'use strict';

    // 全局变量：存储当前用户数据
    let currentUserData = null;
    let currentAttendanceData = null;
    let positionOptions = [];
    let autoRefreshInterval = null; // 自动刷新定时器（setInterval 返回的数字ID）
    let countdownInterval = null; // 倒计时定时器（独立的 setInterval ID）
    const AUTO_REFRESH_INTERVAL = 600000; // 自动刷新间隔（毫秒），10分钟

    function getLocalDate() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function initAttendance() {
        console.log('📍 [attendance.js] initAttendance 开始');
        initUserAttendance();
        initAdminAttendance();
        loadPositions();
        startAutoRefresh(); // 启动自动刷新
    }
    
    // 启动自动刷新
    function startAutoRefresh() {
        // 清理之前的定时器
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }

        let remainingTime = AUTO_REFRESH_INTERVAL;

        // 更新刷新状态显示
        function updateRefreshStatus() {
            const userStatusEl = document.getElementById('refresh-status');
            const adminStatusEl = document.getElementById('admin-refresh-status');
            const seconds = Math.ceil(remainingTime / 1000);

            const statusText = `自动刷新: ${seconds}秒后`;

            if (userStatusEl) userStatusEl.textContent = statusText;
            if (adminStatusEl) adminStatusEl.textContent = statusText;
        }

        // 初始化显示
        try {
            updateRefreshStatus();
        } catch (e) { /* 忽略显示错误 */ }

        // 倒计时定时器
        countdownInterval = setInterval(function() {
            remainingTime -= 1000;
            if (remainingTime <= 0) {
                remainingTime = AUTO_REFRESH_INTERVAL;
            }
            try { updateRefreshStatus(); } catch (e) { /* 忽略显示错误 */ }
        }, 1000);

        // 自动刷新定时器
        autoRefreshInterval = setInterval(function() {
            const dateInput = document.getElementById('attendance-date') || document.getElementById('admin-attendance-date');
            const containerId = document.getElementById('admin-attendance-list') ? 'admin-attendance-list' : 'attendance-list';
            const filterId = document.getElementById('admin-shift-filter') ? 'admin-shift-filter' : 'shift-filter';

            if (dateInput) {
                loadAttendanceList(dateInput.value, containerId, getShiftFilterValue(filterId));
            }
            remainingTime = AUTO_REFRESH_INTERVAL;
        }, AUTO_REFRESH_INTERVAL);
    }
    
    // 停止自动刷新
    function stopAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }

        // 清除状态显示
        const userStatusEl = document.getElementById('refresh-status');
        const adminStatusEl = document.getElementById('admin-refresh-status');
        if (userStatusEl) userStatusEl.textContent = '';
        if (adminStatusEl) adminStatusEl.textContent = '';
    }
    
    // 根据当前时间获取推荐的班别筛选
    function getRecommendedShiftFilter() {
        const now = new Date();
        const hour = now.getHours();
        
        // 00:00-08:00 显示前一天夜班
        if (hour >= 0 && hour < 8) {
            return 'night';
        }
        // 白班时间段：8:00-20:00
        else if (hour >= 8 && hour < 20) {
            return 'day';
        }
        // 夜班时间段：20:00-24:00
        else {
            return 'night';
        }
    }

    // 根据当前时间获取推荐的日期
    function getRecommendedDate() {
        const now = new Date();
        const hour = now.getHours();
        
        // 00:00-08:00 显示前一天
        if (hour >= 0 && hour < 8) {
            now.setDate(now.getDate() - 1);
        }
        
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    async function loadPositions() {
        try {
            const response = await fetch('/api/positions');
            const data = await response.json();
            if (data.positions) {
                positionOptions = data.positions;
            }
        } catch (e) {
            console.error('加载岗位失败:', e);
            positionOptions = ['配料', '涂布', '辊分', '一一车间'];
        }
    }

    function initUserAttendance() {
        console.log('📍 [attendance.js] initUserAttendance 开始');
        const attendanceDate = document.getElementById('attendance-date');
        const refreshBtn = document.getElementById('refresh-attendance-btn');
        const shiftFilter = document.getElementById('shift-filter');
        console.log('📍 [attendance.js] DOM 元素:', {
            attendanceDate: !!attendanceDate,
            refreshBtn: !!refreshBtn,
            shiftFilter: !!shiftFilter
        });

        if (attendanceDate) {
            const recommendedDate = getRecommendedDate();
            attendanceDate.value = recommendedDate;
            
            // 根据当前时间自动选择合适的班别筛选
            const recommendedFilter = getRecommendedShiftFilter();
            if (shiftFilter) {
                shiftFilter.value = recommendedFilter;
            }
            
            loadAttendanceList(recommendedDate, 'attendance-list', recommendedFilter);

            attendanceDate.addEventListener('change', function() {
                loadAttendanceList(this.value, 'attendance-list', getShiftFilterValue('shift-filter'));
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                if (attendanceDate && attendanceDate.value) {
                    loadAttendanceList(attendanceDate.value, 'attendance-list', getShiftFilterValue('shift-filter'));
                }
            });
        }

        if (shiftFilter) {
            shiftFilter.addEventListener('change', function() {
                if (attendanceDate && attendanceDate.value) {
                    loadAttendanceList(attendanceDate.value, 'attendance-list', this.value);
                }
            });
        }

        // 导入前一天出勤按钮
        const importBtn = document.getElementById('import-prev-day-btn');
        if (importBtn) {
            importBtn.addEventListener('click', function() {
                if (attendanceDate && attendanceDate.value) {
                    openImportPrevDayModal(attendanceDate.value);
                }
            });
        }

        // 批量添加按钮
        const batchAddBtn = document.getElementById('batch-add-btn');
        if (batchAddBtn) {
            batchAddBtn.addEventListener('click', function() {
                if (attendanceDate && attendanceDate.value) {
                    openBatchAddModal(attendanceDate.value);
                }
            });
        }

        // 批量删除按钮
        const batchDeleteBtn = document.getElementById('batch-delete-btn');
        if (batchDeleteBtn) {
            batchDeleteBtn.addEventListener('click', function() {
                if (attendanceDate && attendanceDate.value) {
                    openBatchDeleteModal(attendanceDate.value);
                }
            });
        }
    }

    function initAdminAttendance() {
        const attendanceDate = document.getElementById('admin-attendance-date');
        const refreshBtn = document.getElementById('admin-refresh-attendance-btn');
        const shiftFilter = document.getElementById('admin-shift-filter');

        if (attendanceDate) {
            const recommendedDate = getRecommendedDate();
            attendanceDate.value = recommendedDate;
            
            // 根据当前时间自动选择合适的班别筛选
            const recommendedFilter = getRecommendedShiftFilter();
            if (shiftFilter) {
                shiftFilter.value = recommendedFilter;
            }
            
            loadAttendanceList(recommendedDate, 'admin-attendance-list', recommendedFilter);

            attendanceDate.addEventListener('change', function() {
                loadAttendanceList(this.value, 'admin-attendance-list', getShiftFilterValue('admin-shift-filter'));
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                if (attendanceDate && attendanceDate.value) {
                    loadAttendanceList(attendanceDate.value, 'admin-attendance-list', getShiftFilterValue('admin-shift-filter'));
                }
            });
        }

        if (shiftFilter) {
            shiftFilter.addEventListener('change', function() {
                if (attendanceDate && attendanceDate.value) {
                    loadAttendanceList(attendanceDate.value, 'admin-attendance-list', this.value);
                }
            });
        }
    }

    function getShiftFilterValue(elementId) {
        const filter = document.getElementById(elementId);
        return filter ? filter.value : 'all';
    }

    async function loadAttendanceList(date, containerId, shiftFilter) {
        console.log('📍 [attendance.js] loadAttendanceList 被调用:', { date, containerId, shiftFilter });
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn('📍 [attendance.js] 容器不存在:', containerId);
            return;
        }

        // 先显示"骨架" —— 给用户即时反馈，同时避免重复点击
        container.innerHTML = '<div style="text-align:center;padding:2rem;color:#666;">加载中...</div>';

        let url = `/api/attendance/list?date=${date}`;
        if (shiftFilter && shiftFilter !== 'all') {
            url += `&shift=${shiftFilter}`;
        }

        try {
            const t0 = performance.now();
            console.log('📍 [attendance.js] 发起 fetch 请求: ' + url + '  （请在 Network 面板查看此请求的状态码与响应体）');
            const response = await fetch(url);
            const t1 = performance.now();
            const elapsed = (t1 - t0).toFixed(0);

            const rawText = await response.text(); // 先拿原始文本，再尝试 JSON 解析，便于定位非 JSON 响应
            console.log('📍 [attendance.js] fetch 响应状态:', response.status, '耗时:', elapsed + 'ms', '内容长度:', rawText.length, '字符');

            if (!response.ok) {
                console.error('📍 [attendance.js] HTTP 非 2xx：原始响应文本 =', rawText.slice(0, 500));
                throw new Error('HTTP ' + response.status + '（详细内容请查看上方日志）');
            }

            let data;
            try {
                data = JSON.parse(rawText);
            } catch (jsonErr) {
                console.error('📍 [attendance.js] 响应体不是合法 JSON：', jsonErr, '原始响应前 500 字符 =', rawText.slice(0, 500));
                throw new Error('后端返回了非 JSON 内容（请查看上方日志）');
            }

            console.log('📍 [attendance.js] 解析成功，数据 keys:', Object.keys(data));
            currentAttendanceData = data;
            renderAttendanceList(data, container, shiftFilter);
        } catch (error) {
            console.error('加载出勤名单失败:', error);
            container.innerHTML =
                '<div class="attendance-empty">加载失败: ' + (error && error.message ? error.message : String(error)) +
                '<br><small style="color:#888;">请按 F12 → Network → 刷新，查看 /api/attendance/list 请求的状态码和响应体</small>' +
                '</div>';
        }
    }

    function renderAttendanceList(data, container, currentShift) {
        console.log('📍 [attendance.js] renderAttendanceList 被调用，data:',
            'date=' + data.date,
            'total_count=' + data.total_count,
            'work_count=' + data.work_count,
            'absent_count=' + data.absent_count,
            'leave_count=' + data.leave_count,
            'new_employee_count=' + data.new_employee_count,
            'resigned_count=' + data.resigned_count,
            'roles.length=' + (data.roles ? data.roles.length : 0),
            'absent_users.length=' + (data.absent_users ? data.absent_users.length : 0),
            'leave_users.length=' + (data.leave_users ? data.leave_users.length : 0),
            'total_duration_hours=' + data.total_duration_hours,
            'total_duration_minutes=' + data.total_duration_minutes,
            'container.id=' + (container ? container.id : 'NO-CONTAINER'),
            'container.innerHTML 长度=' + (container ? container.innerHTML.length : 0)
        );
        if (!container) {
            console.error('❌ [attendance.js] 没有找到容器元素！');
            return;
        }

        const hasAbsent = data.absent_users && data.absent_users.length > 0;
        const hasResigned = data.resigned_users && data.resigned_users.length > 0;
        const hasLeave = data.leave_users && data.leave_users.length > 0;
        const hasInLieu = data.in_lieu_users && data.in_lieu_users.length > 0;
        const hasNewEmp = data.new_employee_users && data.new_employee_users.length > 0;
        const hasRoles = data.roles && data.roles.length > 0;

        console.log('📍 [attendance.js] hasFlags: hasAbsent=' + hasAbsent, 'hasLeave=' + hasLeave,
            'hasInLieu=' + hasInLieu, 'hasResigned=' + hasResigned, 'hasNewEmp=' + hasNewEmp,
            'hasRoles=' + hasRoles,
            'in_lieu_users=', JSON.stringify(data.in_lieu_users || []));

        if (!hasRoles && !hasLeave && !hasInLieu && !hasNewEmp && !hasAbsent && !hasResigned) {
            container.innerHTML = '<div class="attendance-empty">【' + data.date + '】该日期暂无出勤记录</div>';
            console.log('📍 [attendance.js] ✅ 写入 "暂无出勤记录"，当前 innerHTML 前 300 字:',
                container.innerHTML.substring(0, 300));
            return;
        }

        // 决定哪个选项卡默认激活（第一个有数据的选项卡）
        let activeIndex;
        if (hasLeave) activeIndex = 'leave';
        else if (hasInLieu) activeIndex = 'in_lieu';
        else if (hasAbsent) activeIndex = 'absent';
        else if (hasResigned) activeIndex = 'resigned';
        else if (hasNewEmp) activeIndex = 'new_employee';
        else if (hasRoles) activeIndex = 0;
        else activeIndex = null;

        // 汇总信息：出勤小计 + 总工时
        const workCount = typeof data.work_count === 'number' ? data.work_count :
            (data.total_count - (data.leave_count || 0) - (data.in_lieu_count || 0) - (data.absent_count || 0) - (data.resigned_count || 0));
        const totalHours = typeof data.total_duration_hours === 'number' ? data.total_duration_hours :
            (data.total_duration_minutes ? (data.total_duration_minutes / 60.0).toFixed(1) : 0);

        const parts = [];

        // 顶部汇总栏
        parts.push(`<div class="attendance-summary-bar">
            <span class="summary-pill work">出勤小计：<strong>${workCount}人</strong></span>
            <span class="summary-pill hours">总工时：<strong>${Number(totalHours).toFixed(1)}小时</strong></span>
        </div>`);

        parts.push('<div class="attendance-grid"><div class="role-grid">');

        const mkActive = (idx) => (idx === activeIndex) ? 'active' : '';

        if (hasLeave) {
            parts.push(`<button class="role-grid-item ${mkActive('leave')}" data-role-index="leave"><span class="role-grid-name">请假</span><span class="role-grid-count">${data.leave_count}人</span></button>`);
        }
        if (hasInLieu) {
            parts.push(`<button class="role-grid-item ${mkActive('in_lieu')}" data-role-index="in_lieu" style="background-color:#e3f2fd;border:2px solid #1565c0;"><span class="role-grid-name">调休</span><span class="role-grid-count">${data.in_lieu_count}人</span></button>`);
        }
        if (hasAbsent) {
            parts.push(`<button class="role-grid-item ${mkActive('absent')}" data-role-index="absent" style="background-color:#fff3e0;border:2px solid #f44336;"><span class="role-grid-name">未到岗</span><span class="role-grid-count">${data.absent_count}人</span></button>`);
        }
        if (hasResigned) {
            parts.push(`<button class="role-grid-item ${mkActive('resigned')}" data-role-index="resigned" style="background-color:#f5f5f5;border:2px solid #757575;"><span class="role-grid-name">自离</span><span class="role-grid-count">${data.resigned_count}人</span></button>`);
        }
        if (hasNewEmp) {
            parts.push(`<button class="role-grid-item ${mkActive('new_employee')}" data-role-index="new_employee" style="background-color:#fff3e0;border:2px dashed #ff9800;"><span class="role-grid-name">新员工</span><span class="role-grid-count">${data.new_employee_count}人</span></button>`);
        }
        for (let i = 0; i < data.roles.length; i++) {
            const role = data.roles[i];
            if (role.role_name === '请假' || role.role_name === '自离' || role.role_name === '未到岗' || role.role_name === '调休') continue;
            parts.push(`<button class="role-grid-item ${mkActive(i)}" data-role-index="${i}"><span class="role-grid-name">${role.role_name}</span><span class="role-grid-count">${role.count}人</span></button>`);
        }
        parts.push('</div>');

        // ---- 请假内容 ----
        if (hasLeave) {
            const userHtml = data.leave_users.map(user => {
                const spacedName = user.username.split('').join('   ');
                return `<div class="user-item" style="background-color:#ffebee;color:#c62828;" onclick="openAttendanceEditModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}', '请假')">${spacedName}<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#c62828;color:white;border-radius:8px;">请假</span></div>`;
            }).join('');
            parts.push(`<div class="role-content ${mkActive('leave')}" data-role-index="leave"><div class="user-grid-4">${userHtml}</div></div>`);
        }

        // ---- 调休内容 ----
        if (hasInLieu) {
            const userHtml = data.in_lieu_users.map(user => {
                const spacedName = user.username.split('').join('   ');
                return `<div class="user-item" style="background-color:#e3f2fd;color:#1565c0;" onclick="openAttendanceEditModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}', '调休')">${spacedName}<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#1565c0;color:white;border-radius:8px;">调休</span></div>`;
            }).join('');
            parts.push(`<div class="role-content ${mkActive('in_lieu')}" data-role-index="in_lieu"><div class="user-grid-4">${userHtml}</div></div>`);
        }

        // ---- 未到岗内容 ----
        if (hasAbsent) {
            const userHtml = data.absent_users.map(user => {
                const spacedName = user.username.split('').join('   ');
                return `<div class="user-item" style="background-color:#fff3e0;color:#d32f2f;border:2px solid #f44336;" onclick="openAttendanceEditModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}', '未到岗')">${spacedName}<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#f44336;color:white;border-radius:8px;">未到岗</span></div>`;
            }).join('');
            parts.push(`<div class="role-content ${mkActive('absent')}" data-role-index="absent"><div class="user-grid-4">${userHtml}</div></div>`);
        }

        // ---- 自离内容 ----
        if (hasResigned) {
            const userHtml = data.resigned_users.map(user => {
                const spacedName = user.username.split('').join('   ');
                return `<div class="user-item" style="background-color:#fafafa;color:#757575;border:1px solid #9e9e9e;text-decoration:line-through;" onclick="openResignedInfoModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}')">${spacedName}<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#757575;color:white;border-radius:8px;">自离</span></div>`;
            }).join('');
            parts.push(`<div class="role-content ${mkActive('resigned')}" data-role-index="resigned"><div class="user-grid-4">${userHtml}</div></div>`);
        }

        // ---- 新员工内容 ----
        if (hasNewEmp) {
            const userHtml = data.new_employee_users.map(user => {
                const spacedName = user.username.split('').join('   ');
                return `<div class="user-item" style="background-color:#fff3e0;color:#e65100;border:2px dashed #ff9800;" onclick="openNewEmployeeAssignModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}')">${spacedName}<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#ff9800;color:white;border-radius:8px;">新员工-待分配</span></div>`;
            }).join('');
            parts.push(`<div class="role-content ${mkActive('new_employee')}" data-role-index="new_employee"><div class="user-grid-4">${userHtml}</div></div>`);
        }

        // ---- 各角色内容 ----
        for (let i = 0; i < data.roles.length; i++) {
            const role = data.roles[i];
            if (role.role_name === '请假' || role.role_name === '自离' || role.role_name === '未到岗' || role.role_name === '调休') continue;
            const userHtml = role.users.map(user => {
                const spacedName = user.username.split('').join('   ');
                const shiftBadge = getShiftBadge(user.shift_type, role.role_name, currentShift);
                if (role.role_name === '自离') {
                    return `<div class="user-item" style="background-color:#fafafa;color:#757575;border:1px solid #9e9e9e;text-decoration:line-through;" onclick="openResignedInfoModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}')">${spacedName}<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#757575;color:white;border-radius:8px;">自离</span></div>`;
                }
                if (user.is_new_employee) {
                    return `<div class="user-item" style="border:2px dashed #ff9800;" onclick="openAttendanceEditModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}', '${role.role_name}')">${spacedName}${shiftBadge}<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#ff9800;color:white;border-radius:8px;">新员工</span></div>`;
                }
                return `<div class="user-item" onclick="openAttendanceEditModal(${user.user_id}, '${data.date}', '${user.username}', '${user.shift_type}', '${role.role_name}')">${spacedName}${shiftBadge}</div>`;
            }).join('');
            parts.push(`<div class="role-content ${mkActive(i)}" data-role-index="${i}"><div class="user-grid-4">${userHtml}</div></div>`);
        }

        parts.push('</div>');

        // ---- 一次写入DOM ----
        container.innerHTML = parts.join('');

        // ---- 使用事件委托（onclick 覆盖，避免多次加载重复绑定）----
        container.onclick = function(e) {
            const clickedItem = e.target.closest('.role-grid-item');
            if (!clickedItem) return;
            const index = clickedItem.getAttribute('data-role-index');
            container.querySelectorAll('.role-grid-item').forEach(el => el.classList.remove('active'));
            container.querySelectorAll('.role-content').forEach(el => el.classList.remove('active'));
            clickedItem.classList.add('active');
            const content = container.querySelector(`.role-content[data-role-index="${index}"]`);
            if (content) content.classList.add('active');
        };
    }

    function getShiftBadge(shiftType, roleName, currentShift) {
        if (!shiftType) return '';
        
        // 固定长白班的角色
        const longRoles = ['主管', '职能', '物料'];
        
        let badgeColor = '#666';
        let badgeText = shiftType;
        
        // 如果角色属于固定长白班岗位，直接显示长白班
        if (longRoles.includes(roleName)) {
            return `<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:#ff9800;color:white;border-radius:8px;">长</span>`;
        }
        
        // 其他所有人都根据 shiftType 显示对应班别
        if (shiftType === 'A班白班' || shiftType === '白班' || shiftType === 'day') {
            badgeColor = '#4caf50';
            badgeText = '白';
        } else if (shiftType === 'B班夜班' || shiftType === '夜班' || shiftType === 'night') {
            badgeColor = '#2196f3';
            badgeText = '夜';
        } else if (shiftType === '长白班') {
            badgeColor = '#ff9800';
            badgeText = '长';
        }
        return `<span style="display:inline-block;margin-left:0.3rem;font-size:0.7rem;padding:0.1rem 0.4rem;background-color:${badgeColor};color:white;border-radius:8px;">${badgeText}</span>`;
    }

    // 打开编辑模态框
    window.openAttendanceEditModal = function(userId, date, username, shiftType, roleName) {
        currentUserData = {
            userId,
            date,
            username,
            shiftType,
            roleName
        };

        // 先获取该用户当天的考勤记录
        fetch(`/api/attendance/user-record?user_id=${userId}&date=${date}`)
            .then(res => res.json())
            .then(data => {
                showEditModal(data.record || null);
            })
            .catch(err => {
                console.error('获取考勤记录失败:', err);
                showEditModal(null);
            });
    };

    function showEditModal(existingRecord) {
        // 移除旧的模态框
        const oldModal = document.getElementById('attendance-edit-modal');
        if (oldModal) oldModal.remove();

        const modal = document.createElement('div');
        modal.id = 'attendance-edit-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>编辑考勤 - ${currentUserData.username}</h2>
                    <button onclick="closeAttendanceEditModal()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>出勤状态</label>
                        <select id="edit-status">
                            <option value="出勤">出勤</option>
                            <option value="请假">请假</option>
                            <option value="调休">调休</option>
                            <option value="年假">年假</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>班别</label>
                        <select id="edit-shift">
                            <option value="白班">白班</option>
                            <option value="夜班">夜班</option>
                            <option value="长白班">长白班</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>工时</label>
                        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
                            <button type="button" class="btn secondary" onclick="setWorkHours(11)">白班11小时</button>
                            <button type="button" class="btn secondary" onclick="setWorkHours(11.5)">夜班11.5小时</button>
                            <button type="button" class="btn secondary" onclick="setWorkHours(8)">下早班8小时</button>
                            <input type="number" id="edit-hours" step="0.5" min="0" style="width:100px;padding:0.6rem;border:1px solid #d1d5db;border-radius:6px;font-size:1rem;">
                        </div>
                    </div>
                    <div class="form-group" style="display:flex;align-items:center;gap:0.5rem;">
                        <input type="checkbox" id="edit-early-leave" style="width:auto;">
                        <label for="edit-early-leave" style="margin:0;">下早班</label>
                    </div>
                    <div class="form-group" style="display:flex;align-items:center;gap:0.5rem;padding:0.8rem;background-color:#e3f2fd;border-radius:8px;border:2px solid #1565c0;">
                        <input type="checkbox" id="edit-in-lieu" style="width:auto;" onchange="handleInLieuToggle()">
                        <label for="edit-in-lieu" style="margin:0;color:#1565c0;font-weight:bold;">调休（勾选后工时设为0，自动标记为调休状态）</label>
                    </div>
                    <div class="form-group">
                        <label>岗位</label>
                        <select id="edit-role" onchange="handleRoleChange()"></select>
                    </div>
                    <div class="form-group" style="display:flex;align-items:center;gap:0.5rem;padding:0.8rem;background-color:#fff3e0;border-radius:8px;border:1px solid #ffb74d;">
                        <input type="checkbox" id="edit-resigned" style="width:auto;">
                        <label for="edit-resigned" style="margin:0;color:#e65100;font-weight:bold;">标记为自离（勾选后将自动禁用登录权限）</label>
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea id="edit-remark" rows="3" placeholder="添加备注..."></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn secondary" onclick="closeAttendanceEditModal()">取消</button>
                    <button class="btn primary" onclick="saveAttendance()">保存</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 加载岗位选项（含默认值）
        const defaultRole = existingRecord?.role || currentUserData.roleName || '一一车间';
        loadPositionOptionsForModal(modal, defaultRole);

        // 填充数据
        if (existingRecord) {
            document.getElementById('edit-status').value = existingRecord.status || '出勤';
            document.getElementById('edit-shift').value = existingRecord.shift_type || currentUserData.shiftType;
            document.getElementById('edit-hours').value = existingRecord.hours || '';
            document.getElementById('edit-early-leave').checked = existingRecord.early_leave || false;
            document.getElementById('edit-role').value = defaultRole;
            document.getElementById('edit-remark').value = existingRecord.remark || '';
            // 如果状态是调休，自动勾选调休复选框
            document.getElementById('edit-in-lieu').checked = (existingRecord.status === '调休');
            if (existingRecord.status === '调休') {
                document.getElementById('edit-hours').value = 0;
            }
        } else {
            // 无记录时：根据班别自动填默认工时（白班11 / 夜班11.5）
            const initialShift = currentUserData.shiftType || '白班';
            document.getElementById('edit-shift').value = initialShift;
            document.getElementById('edit-role').value = defaultRole;
            if (initialShift === '白班') {
                document.getElementById('edit-hours').value = 11;
            } else if (initialShift === '夜班') {
                document.getElementById('edit-hours').value = 11.5;
            }
        }

        // 班别变化：自动联动更新工时为对应默认值（白班11 / 夜班11.5）
        const shiftSelectEl = document.getElementById('edit-shift');
        if (shiftSelectEl) {
            shiftSelectEl.addEventListener('change', function() {
                const hoursInputEl = document.getElementById('edit-hours');
                if (!hoursInputEl) return;
                const newShift = this.value;
                // 若当前工时刚好是某个班别的默认值，才自动切换；否则保留用户手动输入的工时
                const currentHours = parseFloat(hoursInputEl.value);
                const isDefaultValue = currentHours === 11 || currentHours === 11.5 || currentHours === 8;
                if (isNaN(currentHours) || currentHours <= 0 || isDefaultValue) {
                    if (newShift === '白班') {
                        hoursInputEl.value = 11;
                    } else if (newShift === '夜班') {
                        hoursInputEl.value = 11.5;
                    }
                }
            });
        }

        // 调休勾选变化：自动设置/取消调休状态
        // handleInLieuToggle 函数定义在 showEditModal 外部

        // 检查用户是否已标记为自离，设置勾选框状态
        fetch(`/api/auth/user/${currentUserData.userId}/is-resigned`)
            .then(res => res.json())
            .then(data => {
                document.getElementById('edit-resigned').checked = data.is_resigned || false;
            })
            .catch(err => {
                console.error('检查自离状态失败:', err);
                document.getElementById('edit-resigned').checked = false;
            });

        // 岗位选择变化（自动同步到本地岗位列表）
        const positionInput = document.getElementById('edit-role');
        positionInput.addEventListener('change', async function() {
            const value = this.value.trim();
            if (value && !positionOptions.includes(value)) {
                try {
                    const response = await fetch('/api/positions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: value })
                    });
                    const result = await response.json();
                    if (result.positions) {
                        positionOptions = result.positions;
                        loadPositionOptionsForModal(modal, value);
                    }
                } catch (e) {
                    console.error('添加岗位失败:', e);
                }
            }
        });

        // 点击遮罩关闭
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeAttendanceEditModal();
            }
        });
    }

    async function loadPositionOptionsForModal(modal, defaultRole) {
        const fixedPositions = ['配料', '涂布', '辊压', '辊分', '分条', '发片', '激光切', '领班', '主管', '职能', '物料', '请假', '调休', '年假', '新员工', '自离', '未到岗', '一一车间'];

        let allHistoryPositions = [];

        try {
            const response = await fetch('/api/attendance/all-roles');
            const data = await response.json();
            if (data.roles && Array.isArray(data.roles)) {
                allHistoryPositions = data.roles;
            }
        } catch (e) {
            console.error('获取所有岗位失败:', e);
        }

        const allPositions = [...fixedPositions];
        allHistoryPositions.forEach(pos => {
            if (!allPositions.includes(pos)) {
                allPositions.push(pos);
            }
        });

        // 确保默认岗位在列表中存在
        if (defaultRole && !allPositions.includes(defaultRole)) {
            allPositions.unshift(defaultRole);
        }

        const selectEl = modal.querySelector('#edit-role');
        if (selectEl) {
            const currentVal = defaultRole || '';
            selectEl.innerHTML = allPositions.map(pos =>
                `<option value="${pos}" ${pos === currentVal ? 'selected' : ''}>${pos}</option>`
            ).join('');
        }
    }

    // 打开新员工岗位分配模态框
    window.openNewEmployeeAssignModal = function(userId, date, username, shiftType) {
        const modal = document.createElement('div');
        modal.id = 'new-employee-assign-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>新员工岗位分配 - ${username}</h2>
                    <button onclick="closeNewEmployeeAssignModal()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="padding: 1rem; background-color: #fff3e0; border-radius: 8px; margin-bottom: 1rem;">
                        <p style="margin: 0; color: #e65100;">
                            <strong>提示：</strong>该员工目前只有"新员工"角色，请为其分配具体岗位。
                            分配后，"新员工"标签会自动移除。
                        </p>
                    </div>
                    <div class="form-group">
                        <label>班别</label>
                        <select id="ne-shift">
                            <option value="白班">白班</option>
                            <option value="夜班">夜班</option>
                            <option value="长白班">长白班</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>岗位</label>
                        <select id="ne-role">
                            <option value="配料">配料</option>
                            <option value="涂布">涂布</option>
                            <option value="辊压">辊压</option>
                            <option value="分条">分条</option>
                            <option value="发片">发片</option>
                            <option value="领班">领班</option>
                            <option value="物料">物料</option>
                            <option value="主管">主管</option>
                            <option value="职能">职能</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn secondary" onclick="closeNewEmployeeAssignModal()">取消</button>
                    <button class="btn primary" onclick="assignNewEmployeeRole(${userId}, '${username}')">分配岗位</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 设置默认班别
        document.getElementById('ne-shift').value = shiftType || '白班';
    };

    window.closeNewEmployeeAssignModal = function() {
        const modal = document.getElementById('new-employee-assign-modal');
        if (modal) modal.remove();
    };

    // 为新员工分配岗位
    window.assignNewEmployeeRole = function(userId, username) {
        const newRole = document.getElementById('ne-role').value;
        const shiftType = document.getElementById('ne-shift').value;

        const data = {
            user_id: userId,
            date: getLocalDate(),
            status: '出勤',
            shift_type: shiftType,
            hours: shiftType === '夜班' ? 11.5 : 11,
            early_leave: false,
            role: newRole,
            remark: '新员工岗位分配'
        };

        fetch('/api/attendance/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(result => {
            alert(`已为 ${username} 分配岗位：${newRole}`);
            closeNewEmployeeAssignModal();
            // 刷新列表
            const dateInput = document.getElementById('admin-attendance-date') || document.getElementById('attendance-date');
            if (dateInput) {
                loadAttendanceList(
                    dateInput.value,
                    document.getElementById('admin-attendance-list') ? 'admin-attendance-list' : 'attendance-list',
                    getShiftFilterValue(document.getElementById('admin-shift-filter') ? 'admin-shift-filter' : 'shift-filter')
                );
            }
        })
        .catch(err => {
            alert('分配岗位失败: ' + err.message);
        });
    };

    // 打开自离人员信息模态框
    window.openResignedInfoModal = function(userId, date, username, shiftType) {
        const modal = document.createElement('div');
        modal.id = 'resigned-info-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>自离员工 - ${username}</h2>
                    <button onclick="closeResignedInfoModal()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="padding: 1.5rem; background-color: #fafafa; border-radius: 8px;">
                        <p style="margin: 0 0 1rem 0; color: #757575; font-size: 1.1rem;">
                            <strong>员工姓名：</strong>${username}
                        </p>
                        <p style="margin: 0 0 1rem 0; color: #757575; font-size: 1.1rem;">
                            <strong>当前状态：</strong><span style="color: #d32f2f; font-weight: bold;">自离</span>
                        </p>
                        <p style="margin: 0 0 1rem 0; color: #757575; font-size: 1.1rem;">
                            <strong>原班别：</strong>${shiftType || '未设置'}
                        </p>
                        <div style="padding: 1rem; background-color: #fff3e0; border-radius: 8px; margin-top: 1rem;">
                            <p style="margin: 0; color: #e65100;">
                                <strong>说明：</strong>该员工已自离，仍保留在看板中以便参考历史记录。<br>
                                如需取消自离状态，恢复工时和登录权限，请点击下方按钮。
                            </p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn secondary" onclick="closeResignedInfoModal()">关闭</button>
                    <button class="btn primary" onclick="cancelResigned(${userId}, '${date}', '${username}')" style="background-color: #4caf50;">取消自离，恢复账号</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    };

    // 取消自离状态，恢复工时和登录
    window.cancelResigned = async function(userId, date, username) {
        if (!confirm(`确认取消 ${username} 的自离状态？\n\n将恢复：\n- 当天工时（11.5小时）\n- 登录权限（is_active=1）\n- 默认角色（涂布）`)) {
            return;
        }

        try {
            const response = await fetch(`/api/auth/user/${userId}/unmark-resigned`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: date })
            });

            if (!response.ok) {
                const err = await response.json();
                alert('取消自离失败：' + (err.error || '未知错误'));
                return;
            }

            const result = await response.json();
            alert(`${username} 的自离状态已取消！\n${result.message}`);
            closeResignedInfoModal();

            // 刷新看板
            const currentDate = document.getElementById('attendance-date').value;
            const shiftFilter = document.getElementById('shift-filter').value;
            loadAttendanceList(currentDate, 'attendance-list', shiftFilter);
        } catch (e) {
            console.error('取消自离失败:', e);
            alert('取消自离失败：' + e.message);
        }
    };

    window.closeResignedInfoModal = function() {
        const modal = document.getElementById('resigned-info-modal');
        if (modal) modal.remove();
    };

    window.setWorkHours = function(hours) {
        document.getElementById('edit-hours').value = hours;
        if (hours === 8) {
            document.getElementById('edit-early-leave').checked = true;
        } else {
            document.getElementById('edit-early-leave').checked = false;
        }
    };

    window.closeAttendanceEditModal = function() {
        const modal = document.getElementById('attendance-edit-modal');
        if (modal) modal.remove();
    };

    // 调休勾选切换：勾选时自动设置状态为调休、工时为0、岗位为调休
    window.handleInLieuToggle = function() {
        const inLieuChecked = document.getElementById('edit-in-lieu').checked;
        const statusSelect = document.getElementById('edit-status');
        const hoursInput = document.getElementById('edit-hours');
        const roleSelect = document.getElementById('edit-role');
        const remarkInput = document.getElementById('edit-remark');

        if (inLieuChecked) {
            // 勾选调休：保存当前岗位到临时变量
            window._originalRole = roleSelect.value;
            statusSelect.value = '调休';
            hoursInput.value = 0;
            // 岗位改为调休，同时备注清空
            const options = roleSelect.options;
            for (let i = 0; i < options.length; i++) {
                if (options[i].value === '调休') {
                    roleSelect.value = '调休';
                    break;
                }
            }
            if (roleSelect.value !== '调休') {
                const opt = document.createElement('option');
                opt.value = '调休';
                opt.text = '调休';
                roleSelect.add(opt);
                roleSelect.value = '调休';
            }
            remarkInput.value = '调休';
        } else {
            // 取消调休：恢复为出勤
            statusSelect.value = '出勤';
            // 根据班别恢复默认工时
            const shift = document.getElementById('edit-shift').value;
            hoursInput.value = (shift === '白班' || shift === '长白班') ? 11 : 11.5;
            // 恢复原来的岗位
            if (window._originalRole && window._originalRole !== '调休' && window._originalRole !== '请假' && window._originalRole !== '年假' && window._originalRole !== '未到岗') {
                roleSelect.value = window._originalRole;
                // 同步填入备注
                remarkInput.value = window._originalRole;
            } else {
                // 如果没有保存过原始岗位，用用户的默认岗位
                const defaultRole = currentUserData.roleName || '配料';
                roleSelect.value = defaultRole;
                // 同步填入备注
                remarkInput.value = defaultRole;
            }
        }
    };

    // 岗位下拉框变化时，自动填入备注
    window.handleRoleChange = function() {
        const roleSelect = document.getElementById('edit-role');
        const remarkInput = document.getElementById('edit-remark');
        const inLieuChecked = document.getElementById('edit-in-lieu').checked;
        // 只有非调休状态时才自动填入备注
        if (!inLieuChecked && roleSelect.value && roleSelect.value !== '调休' && roleSelect.value !== '请假' && roleSelect.value !== '年假' && roleSelect.value !== '未到岗') {
            remarkInput.value = roleSelect.value;
        }
    };

    window.saveAttendance = async function() {
        const positionInput = document.getElementById('edit-role');
        const positionValue = positionInput.value.trim();
        const isResigned = document.getElementById('edit-resigned').checked;

        // 如果输入了新岗位，先添加
        if (positionValue && !positionOptions.includes(positionValue)) {
            try {
                const response = await fetch('/api/positions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: positionValue })
                });
                const result = await response.json();
                if (result.positions) {
                    positionOptions = result.positions;
                }
            } catch (e) {
                console.error('添加岗位失败:', e);
            }
        }

        // 如果勾选了自离，先调用自离API
        if (isResigned) {
            try {
                const resignedResponse = await fetch(`/api/auth/user/${currentUserData.userId}/mark-resigned`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        remark: document.getElementById('edit-remark').value,
                        date: currentUserData.date
                    })
                });
                if (!resignedResponse.ok) {
                    const err = await resignedResponse.json();
                    alert('标记自离失败: ' + (err.error || '未知错误'));
                    return;
                }
            } catch (e) {
                console.error('标记自离失败:', e);
                alert('标记自离失败: ' + e.message);
                return;
            }
        } else {
            // 如果取消自离勾选，恢复为可登录状态
            try {
                const restoreResponse = await fetch(`/api/auth/user/${currentUserData.userId}/unmark-resigned`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ date: currentUserData.date })
                });
                if (!restoreResponse.ok) {
                    const err = await restoreResponse.json();
                    console.warn('取消自离失败（可能该用户未标记为自离）:', err);
                }
            } catch (e) {
                console.warn('取消自离失败:', e);
            }
        }

        const data = {
            user_id: currentUserData.userId,
            date: currentUserData.date,
            status: document.getElementById('edit-status').value,
            shift_type: document.getElementById('edit-shift').value,
            hours: parseFloat(document.getElementById('edit-hours').value) || 0,
            early_leave: document.getElementById('edit-early-leave').checked,
            role: positionValue || '一一车间',
            remark: document.getElementById('edit-remark').value,
            is_resigned: isResigned
        };

        fetch('/api/attendance/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(result => {
            alert(isResigned ? '保存成功！该员工已标记为自离。' : '保存成功！');
            closeAttendanceEditModal();
            // 刷新列表
            const dateInput = document.getElementById('admin-attendance-date') || document.getElementById('attendance-date');
            if (dateInput) {
                loadAttendanceList(
                    dateInput.value,
                    document.getElementById('admin-attendance-list') ? 'admin-attendance-list' : 'attendance-list',
                    getShiftFilterValue(document.getElementById('admin-shift-filter') ? 'admin-shift-filter' : 'shift-filter')
                );
            }
        })
        .catch(err => {
            alert('保存失败: ' + err.message);
        });
    };

    // ==================== 导入前一天出勤 ====================
    function openImportPrevDayModal(currentDate) {
        // 先关闭已有的模态框，防止ID重复
        closeImportPrevDayModal();

        // 计算前一天日期
        const prevDate = new Date(currentDate);
        prevDate.setDate(prevDate.getDate() - 1);
        const prevDateStr = prevDate.toISOString().split('T')[0];

        const modal = document.createElement('div');
        modal.id = 'import-prev-day-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width:600px;">
                <div class="modal-header">
                    <h2>导入前一天出勤数据</h2>
                    <button onclick="closeImportPrevDayModal()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="padding:1rem;background-color:#e3f2fd;border-radius:8px;margin-bottom:1rem;">
                        <p style="margin:0;color:#1565c0;">
                            <strong>说明：</strong>将 <strong>${prevDateStr}</strong> 的出勤数据复制到 <strong>${currentDate}</strong>。
                            <br>导入后可在看板中修改、添加或删除人员。
                        </p>
                    </div>
                    <div class="form-group">
                        <label>选择班别</label>
                        <select id="import-shift" style="width:100%;padding:0.6rem;border:1px solid #d1d5db;border-radius:6px;">
                            <option value="day">白班</option>
                            <option value="night">夜班</option>
                            <option value="all">全部班别</option>
                        </select>
                    </div>
                    <div class="form-group" style="display:flex;align-items:center;gap:0.5rem;">
                        <input type="checkbox" id="import-override" style="width:auto;">
                        <label for="import-override" style="margin:0;color:#c62828;">覆盖现有数据（勾选后将删除当天已有记录再导入）</label>
                    </div>
                    <div id="import-preview" style="margin-top:1rem;padding:1rem;background-color:#f5f5f5;border-radius:8px;max-height:300px;overflow-y:auto;">
                        <p style="color:#666;margin:0;">点击"预览"查看前一天数据...</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn secondary" onclick="previewPrevDayData('${prevDateStr}')">预览</button>
                    <button class="btn secondary" onclick="closeImportPrevDayModal()">取消</button>
                    <button class="btn primary" onclick="executeImportPrevDay('${prevDateStr}', '${currentDate}')">确认导入</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closeImportPrevDayModal();
        });
    }

    window.closeImportPrevDayModal = function() {
        const modal = document.getElementById('import-prev-day-modal');
        if (modal) modal.remove();
    };

    window.previewPrevDayData = function(prevDate) {
        const modal = document.getElementById('import-prev-day-modal');
        const shift = modal ? modal.querySelector('#import-shift').value : 'day';
        const previewEl = modal ? modal.querySelector('#import-preview') : document.getElementById('import-preview');
        if (!previewEl) return;
        previewEl.innerHTML = '<p style="color:#666;">加载中...</p>';

        let url = `/api/attendance/list?date=${prevDate}`;
        if (shift !== 'all') url += `&shift=${shift}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                let html = `<p style="margin:0 0 0.5rem 0;"><strong>${prevDate}</strong> 出勤概况：</p>`;
                html += `<p>总人数：${data.total_count}人 | 出勤：${data.work_count}人 | 请假：${data.leave_count}人 | 调休：${data.in_lieu_count || 0}人</p>`;
                if (data.roles && data.roles.length > 0) {
                    html += '<ul style="margin:0.5rem 0;padding-left:1.5rem;">';
                    data.roles.forEach(r => {
                        if (r.role_name === '请假' || r.role_name === '自离' || r.role_name === '未到岗' || r.role_name === '调休') return;
                        html += `<li>${r.role_name}: ${r.count}人</li>`;
                    });
                    html += '</ul>';
                }
                previewEl.innerHTML = html;
            })
            .catch(err => {
                previewEl.innerHTML = `<p style="color:#c62828;">加载失败: ${err.message}</p>`;
            });
    };

    window.executeImportPrevDay = function(prevDate, currentDate) {
        const modal = document.getElementById('import-prev-day-modal');
        const shift = modal ? modal.querySelector('#import-shift').value : 'day';
        const override = modal ? modal.querySelector('#import-override').checked : false;

        if (!confirm(`确认将 ${prevDate} 的数据导入到 ${currentDate}？\n\n班别：${shift === 'all' ? '全部' : (shift === 'day' ? '白班' : '夜班')}\n覆盖：${override ? '是（将删除现有数据）' : '否（保留现有数据）'}`)) {
            return;
        }

        fetch('/api/attendance/import-prev-day', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prev_date: prevDate,
                target_date: currentDate,
                shift: shift,
                override: override
            })
        })
        .then(res => res.json())
        .then(result => {
            if (result.error) {
                alert('导入失败: ' + result.error);
            } else {
                alert(`导入成功！\n复制了 ${result.copied_count || 0} 条记录。\n${result.message || ''}`);
                closeImportPrevDayModal();
                // 刷新看板
                const dateInput = document.getElementById('attendance-date');
                if (dateInput) {
                    loadAttendanceList(dateInput.value, 'attendance-list', getShiftFilterValue('shift-filter'));
                }
            }
        })
        .catch(err => {
            alert('导入失败: ' + err.message);
        });
    };

    // ==================== 批量添加人员 ====================
    function openBatchAddModal(currentDate) {
        const modal = document.createElement('div');
        modal.id = 'batch-add-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width:700px;">
                <div class="modal-header">
                    <h2>批量添加人员 - ${currentDate}</h2>
                    <button onclick="closeBatchAddModal()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="padding:1rem;background-color:#fff3e0;border-radius:8px;margin-bottom:1rem;">
                        <p style="margin:0;color:#e65100;">
                            <strong>格式说明：</strong>每行一个人员，格式为"岗位：姓名1、姓名2、姓名3"。
                            <br>支持岗位：配料、涂布、辊压、激光切、发片、领班、主管、物料、职能。
                            <br>特殊状态：请假、调休、未到岗。
                        </p>
                    </div>
                    <div class="form-group">
                        <label>班别</label>
                        <select id="batch-add-shift" style="width:100%;padding:0.6rem;border:1px solid #d1d5db;border-radius:6px;">
                            <option value="白班">白班</option>
                            <option value="夜班">夜班</option>
                            <option value="长白班">长白班</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>人员列表（每行一个岗位组）</label>
                        <textarea id="batch-add-text" rows="12" style="width:100%;padding:0.6rem;border:1px solid #d1d5db;border-radius:6px;font-size:0.95rem;" placeholder="配料：张三、李四、王五
涂布：赵六、钱七
辊压：周八
请假：宁福
调休：李景均"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn secondary" onclick="closeBatchAddModal()">取消</button>
                    <button class="btn primary" onclick="executeBatchAdd('${currentDate}')">确认添加</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closeBatchAddModal();
        });
    }

    window.closeBatchAddModal = function() {
        const modal = document.getElementById('batch-add-modal');
        if (modal) modal.remove();
    };

    window.executeBatchAdd = function(date) {
        const shift = document.getElementById('batch-add-shift').value;
        const text = document.getElementById('batch-add-text').value.trim();

        if (!text) {
            alert('请输入人员列表');
            return;
        }

        fetch('/api/attendance/text-import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: `${date}，${shift}\n${text}`
            })
        })
        .then(res => res.json())
        .then(result => {
            if (result.error) {
                alert('添加失败: ' + result.error);
            } else {
                alert(`添加成功！\n出勤：${result.attend_count || 0}人\n请假：${result.leave_count || 0}人\n调休：${result.in_lieu_count || 0}人\n新增：${result.added || 0}条记录`);
                closeBatchAddModal();
                // 刷新看板
                const dateInput = document.getElementById('attendance-date');
                if (dateInput) {
                    loadAttendanceList(dateInput.value, 'attendance-list', getShiftFilterValue('shift-filter'));
                }
            }
        })
        .catch(err => {
            alert('添加失败: ' + err.message);
        });
    };

    // ==================== 批量删除人员 ====================
    function openBatchDeleteModal(currentDate) {
        const modal = document.createElement('div');
        modal.id = 'batch-delete-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width:600px;">
                <div class="modal-header">
                    <h2>批量删除人员 - ${currentDate}</h2>
                    <button onclick="closeBatchDeleteModal()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;">&times;</button>
                </div>
                <div class="modal-body">
                    <div style="padding:1rem;background-color:#ffebee;border-radius:8px;margin-bottom:1rem;">
                        <p style="margin:0;color:#c62828;">
                            <strong>警告：</strong>删除操作不可恢复，请谨慎操作。
                            <br>输入要删除的人员姓名，多个姓名用逗号或顿号分隔。
                        </p>
                    </div>
                    <div class="form-group">
                        <label>班别筛选</label>
                        <select id="batch-delete-shift" style="width:100%;padding:0.6rem;border:1px solid #d1d5db;border-radius:6px;">
                            <option value="all">全部班别</option>
                            <option value="白班">白班</option>
                            <option value="夜班">夜班</option>
                            <option value="长白班">长白班</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>要删除的人员姓名</label>
                        <textarea id="batch-delete-names" rows="6" style="width:100%;padding:0.6rem;border:1px solid #d1d5db;border-radius:6px;" placeholder="张三、李四、王五"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn secondary" onclick="closeBatchDeleteModal()">取消</button>
                    <button class="btn primary" style="background-color:#c62828;" onclick="executeBatchDelete('${currentDate}')">确认删除</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closeBatchDeleteModal();
        });
    }

    window.closeBatchDeleteModal = function() {
        const modal = document.getElementById('batch-delete-modal');
        if (modal) modal.remove();
    };

    window.executeBatchDelete = function(date) {
        const shift = document.getElementById('batch-delete-shift').value;
        const namesText = document.getElementById('batch-delete-names').value.trim();

        if (!namesText) {
            alert('请输入要删除的人员姓名');
            return;
        }

        // 解析姓名列表（支持逗号、顿号、空格分隔）
        const names = namesText.split(/[，,、\s]+/).filter(n => n.trim());

        if (names.length === 0) {
            alert('未识别到有效姓名');
            return;
        }

        if (!confirm(`确认删除以下 ${names.length} 人的考勤记录？\n\n${names.join('、')}\n\n此操作不可恢复！`)) {
            return;
        }

        fetch('/api/attendance/batch-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                shift: shift,
                names: names
            })
        })
        .then(res => res.json())
        .then(result => {
            if (result.error) {
                alert('删除失败: ' + result.error);
            } else {
                alert(`删除成功！\n已删除 ${result.deleted_count || 0} 条记录`);
                closeBatchDeleteModal();
                // 刷新看板
                const dateInput = document.getElementById('attendance-date');
                if (dateInput) {
                    loadAttendanceList(dateInput.value, 'attendance-list', getShiftFilterValue('shift-filter'));
                }
            }
        })
        .catch(err => {
            alert('删除失败: ' + err.message);
        });
    };

    // 暴露给 app.js 和 tabs.js 调用（统一由 app.js 调度初始化）
    window.initAttendance = initAttendance;

})();
