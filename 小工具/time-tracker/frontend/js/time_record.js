// 工时记录逻辑

// 全局变量，用于跟踪当前正在进行的工时记录
let currentRecordId = null;

// 当前显示的年月
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth();

// 班别列表，从本地存储加载
let shiftTypes = JSON.parse(localStorage.getItem('shift_types')) || ['白班', '夜班'];

// 各班别默认工时（用户可自由修改/删除）
const DEFAULT_HOURS = {
    '白班': 11,
    '夜班': 11.5
};

// 下早班默认工时
const EARLY_OFF_HOURS = 8;

// 加载当月工时统计
async function loadMonthlyStats() {
    const user = getCurrentUser();
    if (!user) return;
    
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    const startDate = `${year}-${month.toString().padStart(2, '0')}-01`;
    const endDate = `${year}-${month.toString().padStart(2, '0')}-${new Date(year, month, 0).getDate()}`;
    
    try {
        const stats = await timeRecordAPI.getTimeRecords(user.id, {
            start_date: `${startDate} 00:00:00`,
            end_date: `${endDate} 23:59:59`
        });
        
        let totalHours = 0;
        const dayShiftsMap = new Map();
        const nightShiftsMap = new Map();
        
        stats.forEach(record => {
            if (!record.is_leave) {
                totalHours += (record.duration || 0) / 60;
                
                let date;
                if (record.start_time.includes('T')) {
                    date = record.start_time.split('T')[0];
                } else if (record.start_time.includes(' ')) {
                    date = record.start_time.split(' ')[0];
                } else {
                    date = record.start_time.substring(0, 10);
                }
                
                let shiftType = record.shift_type;
                // 兼容多种白班夜班格式
                if (shiftType === 'day' || shiftType === '白班') {
                    dayShiftsMap.set(date, true);
                } else if (shiftType === 'night' || shiftType === '夜班') {
                    nightShiftsMap.set(date, true);
                }
            }
        });
        
        const dayShifts = dayShiftsMap.size;
        const nightShifts = nightShiftsMap.size;
        
        // 更新页面显示
        const totalHoursEl = document.getElementById('monthly-total-hours');
        const dayShiftsEl = document.getElementById('monthly-day-shifts');
        const nightShiftsEl = document.getElementById('monthly-night-shifts');
        
        // 优化工时显示格式
        const formatHours = (hours) => {
            if (hours % 1 === 0) {
                return hours.toFixed(0);
            } else {
                return hours.toFixed(1);
            }
        };
        
        if (totalHoursEl) totalHoursEl.textContent = formatHours(totalHours);
        if (dayShiftsEl) dayShiftsEl.textContent = dayShifts;
        if (nightShiftsEl) nightShiftsEl.textContent = nightShifts;
        
        await checkDuplicates();
    } catch (error) {
        console.error('加载当月工时失败:', error);
    }
}

async function checkDuplicates() {
    const user = getCurrentUser();
    if (!user) return;
    
    try {
        const response = await fetchAPI(`/time-records/find-duplicates?user_id=${user.id}`);
        
        if (response.total_duplicate_dates > 0) {
            const warningEl = document.getElementById('duplicate-warning');
            if (warningEl) {
                warningEl.style.display = 'block';
                warningEl.textContent = `发现 ${response.total_duplicate_dates} 天有重复记录，共 ${response.total_duplicate_records} 条`;
            }
        }
    } catch (error) {
        console.error('检查重复记录失败:', error);
    }
}

async function cleanupDuplicates() {
    const user = getCurrentUser();
    if (!user) return;
    
    if (!confirm('确定要清理重复的工时记录吗？\n每天只会保留最后一条记录，其他重复记录将被删除。')) {
        return;
    }
    
    try {
        const response = await fetchAPI('/time-records/cleanup-duplicates', {
            method: 'POST',
            body: JSON.stringify({ user_id: user.id })
        });
        
        if (response.deleted_count > 0) {
            alert(`成功清理了 ${response.deleted_count} 条重复记录`);
            loadMonthlyStats();
            loadTimeRecords();
            generateCalendar();
        } else {
            alert('没有发现重复记录');
        }
        
        const warningEl = document.getElementById('duplicate-warning');
        if (warningEl) {
            warningEl.style.display = 'none';
        }
    } catch (error) {
        alert('清理重复记录失败: ' + error.message);
    }
}

// 添加排班计划
async function addSchedule() {
    const user = getCurrentUser();
    if (!user) return;
    
    const startDate = document.getElementById('schedule-start-date').value;
    const endDate = document.getElementById('schedule-end-date').value;
    const shiftType = document.getElementById('schedule-shift-type').value;
    const hours = parseFloat(document.getElementById('schedule-hours').value);
    const description = document.getElementById('schedule-description').value;
    
    if (!startDate || !endDate || isNaN(hours) || hours <= 0) {
        alert('请输入有效的日期和工时');
        return;
    }
    
    try {
        // 将排班计划添加到后端数据库
        const response = await fetchAPI('/admin/schedules', {
            method: 'POST',
            body: JSON.stringify({
                user_id: user.id,
                start_date: startDate,
                end_date: endDate,
                shift_type: shiftType,
                hours: hours,
                description: description
            })
        });
        
        alert('排班计划添加成功');
        
        // 清空表单
        document.getElementById('schedule-start-date').value = '';
        document.getElementById('schedule-end-date').value = '';
        document.getElementById('schedule-shift-type').value = '白班';
        document.getElementById('schedule-hours').value = '';
        document.getElementById('schedule-description').value = '';
        
    } catch (error) {
        console.error('添加排班失败:', error);
        alert('添加排班失败: ' + error.message);
    }
}

// 查看排班计划
async function viewSchedule() {
    const user = getCurrentUser();
    if (!user) return;
    
    const scheduleList = document.getElementById('schedule-list');
    const modal = document.getElementById('schedule-modal');
    
    if (!scheduleList || !modal) return;
    
    // 清空现有列表并显示加载状态
    scheduleList.innerHTML = '<p>加载中...</p>';
    
    try {
        // 从后端API获取所有排班计划
        const allSchedules = await scheduleAPI.getSchedules(user.id);
        
        // 清空现有列表
        scheduleList.innerHTML = '';
        
        if (allSchedules.length === 0) {
            scheduleList.innerHTML = '<p>暂无排班计划</p>';
        } else {
            // 按开始日期排序
            allSchedules.sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
            
            // 添加排班计划项
            allSchedules.forEach(schedule => {
                const item = document.createElement('div');
                item.className = 'schedule-item';
                
                // 格式化日期为中文格式
                const formatDate = (dateStr) => {
                    const date = new Date(dateStr);
                    return `${date.getMonth() + 1}月${date.getDate()}日`;
                };
                
                // 格式化日期范围
                const formatDateRange = (startDate, endDate) => {
                    const start = new Date(startDate);
                    const end = new Date(endDate);
                    
                    // 如果是同一年
                    if (start.getFullYear() === end.getFullYear()) {
                        // 如果是同一月
                        if (start.getMonth() === end.getMonth()) {
                            // 格式：12月1日-14日
                            return `${start.getMonth() + 1}月${start.getDate()}日-${end.getDate()}日`;
                        } else {
                            // 格式：12月1日-1月14日
                            return `${start.getMonth() + 1}月${start.getDate()}日-${end.getMonth() + 1}月${end.getDate()}日`;
                        }
                    } else {
                        // 格式：2023年12月1日-2024年1月14日
                        return `${start.getFullYear()}年${start.getMonth() + 1}月${start.getDate()}日-${end.getFullYear()}年${end.getMonth() + 1}月${end.getDate()}日`;
                    }
                };
                
                item.innerHTML = `
                    <div class="schedule-info">
                        <h4>${formatDateRange(schedule.start_date, schedule.end_date)} ${schedule.shift_type} ${schedule.hours}小时</h4>
                        <p>${schedule.description || '无描述'}</p>
                    </div>
                    <button class="btn secondary small delete-schedule-btn" data-id="${schedule.id}">删除</button>
                `;
                
                scheduleList.appendChild(item);
            });
            
            // 添加删除按钮事件
            const deleteButtons = document.querySelectorAll('.delete-schedule-btn');
            deleteButtons.forEach(btn => {
                btn.addEventListener('click', async function() {
                    const scheduleId = this.getAttribute('data-id');
                    
                    if (confirm('确定要删除这个排班计划吗？')) {
                        try {
                            // 删除排班计划（所有排班计划都存储在数据库中）
                            await scheduleAPI.deleteSchedule(scheduleId);
                            // 重新加载排班列表
                            viewSchedule();
                        } catch (error) {
                            console.error('删除排班失败:', error);
                            alert('删除排班失败: ' + error.message);
                        }
                    }
                });
            });
        }
    } catch (error) {
        console.error('加载排班计划失败:', error);
        scheduleList.innerHTML = '<p>加载排班计划失败</p>';
    }
    
    // 显示模态框
    modal.classList.add('active');
    
    // 添加关闭按钮事件
    const closeBtn = modal.querySelector('.close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    }
    
    // 点击模态框外部关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

// 加载工时记录列表
async function loadTimeRecords(filters = {}) {
    const user = getCurrentUser();
    if (!user) return;
    
    const recordsList = document.getElementById('records-list');
    if (!recordsList) return;
    
    // 如果没有提供filters，默认加载当前月份的记录
    if (Object.keys(filters).length === 0) {
        const startDate = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-01`;
        const endDate = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${new Date(currentYear, currentMonth + 1, 0).getDate()}`;
        
        filters = {
            start_date: `${startDate} 00:00:00`,
            end_date: `${endDate} 23:59:59`
        };
    }
    
    try {
        const records = await timeRecordAPI.getTimeRecords(user.id, filters);
        
        // 清空现有记录
        recordsList.innerHTML = '';
        
        // 添加记录项
        records.forEach(record => {
            const recordItem = createRecordItem(record);
            recordsList.appendChild(recordItem);
        });
    } catch (error) {
        console.error('加载工时记录失败:', error);
        recordsList.innerHTML = '<p>加载记录失败，请重试</p>';
    }
}

// 创建工时记录项元素
function createRecordItem(record) {
    const item = document.createElement('div');
    item.className = 'record-item';
    
    // 格式化日期
    const date = new Date(record.start_time).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
    
    // 计算时长
    const duration = record.duration || 0;
    let hours = duration / 60;
    if (hours % 1 === 0) {
        hours = hours.toFixed(0);
    } else {
        hours = hours.toFixed(1);
    }
    
    // 记录类型显示
    let recordTypeText = '';
    let recordTypeClass = '';
    
    if (record.is_leave) {
        recordTypeText = '请假';
        recordTypeClass = 'leave-record';
    } else if (record.is_early_off) {
        recordTypeText = '下早班';
        recordTypeClass = 'early-off-record';
    }
    
    // 班别显示
    let shiftText = '';
    let shiftClass = '';
    
    if (!record.is_leave) {
        shiftText = record.shift_type || '未设置';
        shiftClass = record.shift_type === '夜班' ? 'night' : 'day';
    }
    
    item.innerHTML = `
        <div class="record-header">
            <span class="record-date">${date}</span>
            ${shiftText ? `<span class="record-shift ${shiftClass}">${shiftText}</span>` : ''}
            ${recordTypeText ? `<span class="record-type ${recordTypeClass}">${recordTypeText}</span>` : ''}
        </div>
        <div class="record-details">
            <p>${record.description || '无描述'}</p>
        </div>
        <div class="record-footer">
            <span class="record-duration">${hours}小时</span>
            <button class="btn secondary" style="width: auto; padding: 0.25rem 0.5rem; font-size: 0.8rem; margin-right: 0.5rem;" onclick="editRecord(${record.id})">编辑</button>
            <button class="btn secondary" style="width: auto; padding: 0.25rem 0.5rem; font-size: 0.8rem;" onclick="deleteRecord(${record.id})">删除</button>
        </div>
    `;
    
    return item;
}

// 删除工时记录
async function deleteRecord(recordId) {
    const user = getCurrentUser();
    if (!user) return;
    
    if (confirm('确定要删除这条记录吗？')) {
        try {
            await timeRecordAPI.deleteRecord(recordId, user.id);
            loadTimeRecords(); // 重新加载列表
            loadMonthlyStats(); // 更新当月统计
            generateCalendar(); // 更新日历
        } catch (error) {
            alert('删除失败: ' + error.message);
        }
    }
}

// 开始工时记录
async function startRecord() {
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return;
    }
    
    const projectId = document.getElementById('project-select').value;
    const shiftType = document.getElementById('shift-type').value;
    const description = document.getElementById('work-description').value;
    
    try {
        const result = await timeRecordAPI.startRecord({
            user_id: user.id,
            project_id: projectId || null,
            shift_type: shiftType,
            description: description
        });
        
        // 保存当前记录ID
        currentRecordId = result.id || null;
        
        // 更新按钮状态
        document.getElementById('start-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
        
        alert('工时记录已开始');
    } catch (error) {
        alert('开始记录失败: ' + error.message);
    }
}

// 结束工时记录
async function stopRecord() {
    if (!currentRecordId) {
        alert('没有正在进行的记录');
        return;
    }
    
    try {
        await timeRecordAPI.stopRecord(currentRecordId);
        
        // 重置状态
        currentRecordId = null;
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
        
        // 清空表单
        document.getElementById('work-description').value = '';
        
        // 更新统计和列表
        loadTodayStats();
        loadTimeRecords();
        generateCalendar();
        
        alert('工时记录已结束');
    } catch (error) {
        alert('结束记录失败: ' + error.message);
    }
}

// 初始化批量操作模态框
function initBatchModal() {
    // 操作类型选择事件
    const operationTypeSelect = document.getElementById('batch-operation-type');
    const updateFields = document.getElementById('batch-update-fields');
    
    if (operationTypeSelect && updateFields) {
        operationTypeSelect.addEventListener('change', function() {
            if (this.value === 'delete') {
                updateFields.style.display = 'none';
            } else {
                updateFields.style.display = 'block';
            }
        });
    }
}

// 批量操作工时记录
async function batchUpdateRecords() {
    const user = getCurrentUser();
    if (!user) return;
    
    const operationType = document.getElementById('batch-operation-type').value;
    const startDate = document.getElementById('batch-start-date').value;
    const endDate = document.getElementById('batch-end-date').value;
    
    if (!startDate || !endDate) {
        alert('请选择日期范围');
        return;
    }
    
    try {
        if (operationType === 'delete') {
            // 批量删除
            // 获取要删除的记录
            const records = await timeRecordAPI.getTimeRecords(user.id, {
                start_date: `${startDate} 00:00:00`,
                end_date: `${endDate} 23:59:59`
            });
            
            if (records.length === 0) {
                alert('所选日期范围内没有记录');
                return;
            }
            
            if (confirm(`确定要删除所选日期范围内的 ${records.length} 条记录吗？`)) {
                for (const record of records) {
                    await timeRecordAPI.deleteRecord(record.id, user.id);
                }
                
                alert(`成功删除 ${records.length} 条记录`);
            }
        } else if (operationType === 'update') {
            // 批量更新
            // 获取要更新的记录
            const records = await timeRecordAPI.getTimeRecords(user.id, {
                start_date: `${startDate} 00:00:00`,
                end_date: `${endDate} 23:59:59`
            });
            
            if (records.length === 0) {
                alert('所选日期范围内没有记录');
                return;
            }
            
            const shiftType = document.getElementById('batch-shift-type').value;
            const batchHours = document.getElementById('batch-hours').value;
            
            // 转换工时为浮点数
            const hours = batchHours ? parseFloat(batchHours) : null;
            
            // 验证工时输入
            if (hours === null || isNaN(hours)) {
                alert('请输入有效的工时');
                return;
            }
            
            let updateData = [];
            let message = '';
            
            // 该日期范围内有记录，更新现有记录
            updateData = records.map(record => {
                const update = { id: record.id };
                if (shiftType) {
                    update.shift_type = shiftType;
                }
                
                // 更新工时相关字段
                const duration = Math.round(hours * 60); // 转换为分钟
                update.duration = duration;
                
                // 重新计算结束时间
                const start_time = new Date(record.start_time);
                const end_time = new Date(start_time.getTime() + duration * 60 * 1000);
                update.start_time = start_time.toISOString(); // 统一时间格式
                update.end_time = end_time.toISOString(); // 更新结束时间
                
                return update;
            });
            
            // 执行批量更新
            await timeRecordAPI.batchUpdate(user.id, updateData);
            
            message = `成功更新 ${records.length} 条记录`;
            alert(message);
        } else if (operationType === 'add') {
            // 批量添加
            const shiftType = document.getElementById('batch-shift-type').value;
            const batchHours = document.getElementById('batch-hours').value;
            
            // 转换工时为浮点数
            const hours = batchHours ? parseFloat(batchHours) : null;
            
            // 验证工时输入
            if (hours === null || isNaN(hours)) {
                alert('请输入有效的工时');
                return;
            }
            
            // 获取日期范围内的所有日期
            const start = new Date(startDate);
            const end = new Date(endDate);
            const allDates = [];
            
            for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
                allDates.push(d.toISOString().split('T')[0]);
            }
            
            // 获取日期范围内已有的记录
            const existingRecords = await timeRecordAPI.getTimeRecords(user.id, {
                start_date: `${startDate} 00:00:00`,
                end_date: `${endDate} 23:59:59`
            });
            
            // 检查每个日期是否已经有记录
            const existingDates = existingRecords.map(record => new Date(record.start_time).toISOString().split('T')[0]);
            const datesToCreate = allDates.filter(date => !existingDates.includes(date));
            
            if (datesToCreate.length === 0) {
                alert('所选日期范围内的所有日期都已有记录，无法创建新记录');
                return;
            }
            
            // 确认批量添加
            if (confirm(`确定要在所选日期范围内添加 ${datesToCreate.length} 条记录吗？`)) {
                // 准备新记录数据
                const newRecords = [];
                
                for (const date of datesToCreate) {
                    const duration = Math.round(hours * 60); // 转换为分钟
                    
                    // 准备新记录数据
                    const startDateTime = new Date(`${date}T08:00:00`);
                    const endDateTime = new Date(startDateTime.getTime() + duration * 60 * 1000);
                    const newRecord = {
                        start_time: startDateTime.toISOString(), // 统一时间格式
                        end_time: endDateTime.toISOString(), // 统一时间格式
                        duration: duration,
                        shift_type: shiftType || '白班', // 默认班别为白班
                        description: '批量创建的工时记录',
                        is_leave: false,
                        is_early_off: false
                    };
                    
                    newRecords.push(newRecord);
                }
                
                // 执行批量添加
                await timeRecordAPI.batchUpdate(user.id, newRecords);
                
                alert(`成功添加 ${newRecords.length} 条记录`);
            }
        }
        
        // 关闭模态框
        document.getElementById('batch-modal').classList.remove('active');
        
        // 重新加载记录
        loadTimeRecords();
        generateCalendar();
        loadMonthlyStats();
    } catch (error) {
        alert('批量操作失败: ' + error.message);
    }
}

// 生成日历
async function generateCalendar() {
    const user = getCurrentUser();
    if (!user) return;

    const calendarEl = document.getElementById('calendar');
    const currentMonthEl = document.getElementById('current-month');
    if (!calendarEl || !currentMonthEl) return;

    currentMonthEl.textContent = `${currentYear}年${currentMonth + 1}月`;

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(currentYear, currentMonth, 0).getDate();
    const monthPart = String(currentMonth + 1).padStart(2, '0');

    // ---- 阶段 1：立即渲染日历骨架（只有日期格子，不等待数据）----
    const skeletonParts = [];
    for (let i = firstDay - 1; i >= 0; i--) {
        skeletonParts.push(`<div class="calendar-day other-month"><span class="day-number">${daysInPrevMonth - i}</span></div>`);
    }
    for (let day = 1; day <= daysInMonth; day++) {
        const dayPart = String(day).padStart(2, '0');
        const dateStr = `${currentYear}-${monthPart}-${dayPart}`;
        skeletonParts.push(
            `<div class="calendar-day" data-date="${dateStr}">` +
            `<span class="day-number">${day}</span>` +
            `<span class="day-info" style="color:#bbb;font-size:0.7rem;">...</span>` +
            `</div>`
        );
    }
    const totalDays = firstDay + daysInMonth;
    const remainingDays = 42 - totalDays;
    for (let day = 1; day <= remainingDays; day++) {
        skeletonParts.push(`<div class="calendar-day other-month"><span class="day-number">${day}</span></div>`);
    }
    calendarEl.innerHTML = skeletonParts.join('');

    // 事件委托：在日历骨架上预先绑定（点击立刻可以响应）
    calendarEl.onclick = function(e) {
        const dayEl = e.target.closest('.calendar-day:not(.other-month)');
        if (!dayEl) return;
        const date = dayEl.getAttribute('data-date');
        openTimeInputModal(date);
    };

    // ---- 阶段 2：异步拉取数据，填回到已渲染的格子 ----
    const startDate = `${currentYear}-${monthPart}-01`;
    const endDate = `${currentYear}-${monthPart}-${daysInMonth}`;
    let records = [];
    try {
        records = await timeRecordAPI.getTimeRecords(user.id, {
            start_date: `${startDate} 00:00:00`,
            end_date: `${endDate} 23:59:59`
        });
    } catch (error) {
        console.error('加载工时记录失败:', error);
        // 至少把"..."清掉
        calendarEl.querySelectorAll('.calendar-day[data-date]').forEach(el => {
            const info = el.querySelector('.day-info');
            if (info) info.remove();
        });
        return;
    }

    // 按日期分组
    const recordsByDate = {};
    for (let i = 0; i < records.length; i++) {
        const rec = records[i];
        const st = rec.start_time;
        let date;
        if (st.includes('T')) date = st.split('T')[0];
        else if (st.includes(' ')) date = st.split(' ')[0];
        else date = st.substring(0, 10);
        if (!recordsByDate[date]) recordsByDate[date] = [];
        recordsByDate[date].push(rec);
    }

    // 增量更新：只更新当天有记录的格子
    const monthPrefix = `${currentYear}-${monthPart}-`;
    for (let day = 1; day <= daysInMonth; day++) {
        const dayPart = String(day).padStart(2, '0');
        const dateStr = monthPrefix + dayPart;
        const dayRecords = recordsByDate[dateStr];
        if (!dayRecords || dayRecords.length === 0) {
            // 没记录：把占位"..."去掉
            const dayEl = calendarEl.querySelector(`.calendar-day[data-date="${dateStr}"]`);
            if (dayEl) {
                const info = dayEl.querySelector('.day-info');
                if (info) info.remove();
            }
            continue;
        }

        let workHours = 0;
        let leaveHours = 0;
        let shiftName = '';
        let hasWork = false;
        let hasLeave = false;

        for (let j = 0; j < dayRecords.length; j++) {
            const rec = dayRecords[j];
            const hours = (rec.duration || 0) / 60;
            if (rec.is_leave) {
                leaveHours += hours;
                hasLeave = true;
            } else {
                workHours += hours;
                const st = rec.shift_type;
                if (st === 'day') shiftName = '白班';
                else if (st === 'night') shiftName = '夜班';
                else if (st) shiftName = st;
                hasWork = true;
            }
        }

        const hasRecord = hasWork || hasLeave;
        const dayEl = calendarEl.querySelector(`.calendar-day[data-date="${dateStr}"]`);
        if (!dayEl) continue;

        // 重新构建该日期内部内容
        let innerHtml = `<span class="day-number">${day}</span>`;
        if (hasWork) innerHtml += `<span class="day-info work-record">${shiftName} ${workHours.toFixed(1)}小时</span>`;
        if (hasLeave) innerHtml += `<span class="day-info leave-record">请假 ${leaveHours.toFixed(1)}小时</span>`;
        if (hasRecord) {
            innerHtml += `<button class="copy-btn" onclick="openCopyTimeModal('${dateStr}')">复制</button>`;
            dayEl.classList.add('has-record');
        }
        dayEl.innerHTML = innerHtml;
    }
}

// 打开工时输入模态框（已有记录时自动回填，便于直接修改覆盖）
async function openTimeInputModal(date) {
    const modal = document.getElementById('time-input-modal');
    const selectedDateEl = document.getElementById('selected-date');
    const inputDateEl = document.getElementById('input-date');
    const recordTypeEl = document.getElementById('record-type');
    const workHoursSection = document.getElementById('work-hours-section');
    const leaveHoursSection = document.getElementById('leave-hours-section');
    const shiftTypeSection = document.getElementById('shift-type-section');
    const inputHoursEl = document.getElementById('input-hours');
    const leaveHoursEl = document.getElementById('leave-hours');
    const inputShiftEl = document.getElementById('input-shift-type');
    const inputDescEl = document.getElementById('input-description');
    const modalEl = document.getElementById('time-input-modal');

    if (!modal || !selectedDateEl || !inputDateEl) return;

    selectedDateEl.value = date;
    inputDateEl.value = date;

    // 重置表单
    recordTypeEl.value = 'normal';
    inputHoursEl.value = '';
    leaveHoursEl.value = '';
    inputDescEl.value = '';
    // 显示默认字段
    workHoursSection.style.display = 'block';
    leaveHoursSection.style.display = 'none';
    shiftTypeSection.style.display = 'block';

    // 清除上次编辑的 recordId 缓存
    if (modalEl) {
        delete modalEl.dataset.recordId;
    }

    // 更新班别选项
    updateShiftTypeOptions();

    // 尝试加载当天已有记录，如果有数据则自动回填（覆盖式修改体验）
    const user = getCurrentUser();
    let hasExisting = false;
    if (user && date) {
        try {
            const existing = await timeRecordAPI.getTimeRecords(user.id, {
                start_date: `${date} 00:00:00`,
                end_date: `${date} 23:59:59`
            });
            if (existing && existing.length > 0) {
                hasExisting = true;
                const rec = existing[0];
                // 回填类型
                if (rec.is_leave) {
                    recordTypeEl.value = 'leave';
                } else if (rec.is_early_off) {
                    recordTypeEl.value = 'early-off';
                } else {
                    recordTypeEl.value = 'normal';
                }
                // 回填工时/请假时长
                const hours = (rec.duration || 0) / 60;
                if (rec.is_leave) {
                    leaveHoursEl.value = hours.toFixed(1);
                } else {
                    inputHoursEl.value = hours.toFixed(1);
                }
                // 回填班别
                if (inputShiftEl) {
                    inputShiftEl.value = rec.shift_type || '白班';
                }
                // 回填描述
                if (inputDescEl) {
                    inputDescEl.value = rec.description || '';
                }
                // 按当前类型调整显示/隐藏（保留已回填工时，不被默认值覆盖）
                handleRecordTypeChange(true);
            }
        } catch (err) {
            console.warn('加载当日工时记录失败，将作为新记录处理:', err);
        }
    }

    // 无已有记录：按班别自动填默认工时
    if (!hasExisting) {
        handleRecordTypeChange(false);
    }

    modal.classList.add('active');

    // 移除旧的事件监听器，避免重复添加
    recordTypeEl.removeEventListener('change', handleRecordTypeChange);
    // 添加记录类型选择事件监听器（用户手动切换类型时重置工时为默认）
    recordTypeEl.addEventListener('change', function () {
        handleRecordTypeChange(false);
    });
}

// 处理记录类型选择变化
// preserveHours = true 时不重置工时（用于已有记录回填场景）
function handleRecordTypeChange(preserveHours) {
    const recordTypeEl = document.getElementById('record-type');
    if (!recordTypeEl) return;
    const recordType = recordTypeEl.value;
    const workHoursSection = document.getElementById('work-hours-section');
    const leaveHoursSection = document.getElementById('leave-hours-section');
    const shiftTypeSection = document.getElementById('shift-type-section');
    const inputHoursEl = document.getElementById('input-hours');
    const leaveHoursEl = document.getElementById('leave-hours');
    const shiftTypeEl = document.getElementById('input-shift-type');

    // 只有全新填写时才重置工时输入框
    if (!preserveHours) {
        inputHoursEl.value = '';
        if (leaveHoursEl) leaveHoursEl.value = '';
    }

    if (recordType === 'leave') {
        // 请假记录
        workHoursSection.style.display = 'none';
        leaveHoursSection.style.display = 'block';
        shiftTypeSection.style.display = 'none';
    } else if (recordType === 'early-off') {
        // 下早班记录
        workHoursSection.style.display = 'block';
        leaveHoursSection.style.display = 'none';
        shiftTypeSection.style.display = 'block';
        if (!preserveHours) {
            inputHoursEl.value = String(EARLY_OFF_HOURS);
        }
    } else {
        // 正常工时记录：根据当前选中班别自动填默认工时（白班11/夜班11.5）
        workHoursSection.style.display = 'block';
        leaveHoursSection.style.display = 'none';
        shiftTypeSection.style.display = 'block';
        if (!preserveHours && shiftTypeEl && shiftTypeEl.value
            && DEFAULT_HOURS[shiftTypeEl.value] !== undefined) {
            inputHoursEl.value = String(DEFAULT_HOURS[shiftTypeEl.value]);
        }
    }
}

// 处理班别选择变化
function handleShiftTypeChange() {
    const recordTypeEl = document.getElementById('record-type');
    const shiftTypeEl = document.getElementById('input-shift-type');
    const inputHoursEl = document.getElementById('input-hours');
    if (!recordTypeEl || !shiftTypeEl || !inputHoursEl) return;

    const recordType = recordTypeEl.value;
    // 请假时班别不显示，不处理
    if (recordType === 'leave') return;

    // 下早班：保持 8 小时默认（用户已手动修改则不覆盖）
    if (recordType === 'early-off') {
        return;
    }

    // normal：根据班别填默认工时，用户可随时修改
    const shiftType = shiftTypeEl.value;
    if (shiftType && DEFAULT_HOURS[shiftType] !== undefined) {
        inputHoursEl.value = String(DEFAULT_HOURS[shiftType]);
    }
}

// 更新班别选项
function updateShiftTypeOptions() {
    const shiftSelectEl = document.getElementById('input-shift-type');
    const batchShiftSelectEl = document.getElementById('batch-shift-type');

    if (shiftSelectEl) {
        shiftSelectEl.innerHTML = '';
        shiftTypes.forEach(shift => {
            const option = document.createElement('option');
            option.value = shift;
            option.textContent = shift;
            shiftSelectEl.appendChild(option);
        });
        // 绑定班别变化监听器（切换班别时自动填默认工时）
        shiftSelectEl.removeEventListener('change', handleShiftTypeChange);
        shiftSelectEl.addEventListener('change', handleShiftTypeChange);
    }

    if (batchShiftSelectEl) {
        batchShiftSelectEl.innerHTML = '<option value="">不修改</option>';
        shiftTypes.forEach(shift => {
            const option = document.createElement('option');
            option.value = shift;
            option.textContent = shift;
            batchShiftSelectEl.appendChild(option);
        });
    }
}

// 编辑工时记录
async function editRecord(recordId) {
    const user = getCurrentUser();
    if (!user) return;
    
    try {
        // 获取现有记录
        const records = await timeRecordAPI.getTimeRecords(user.id);
        const record = records.find(r => r.id === recordId);
        if (!record) {
            alert('记录未找到');
            return;
        }
        
        // 打开工时输入模态框
        const date = new Date(record.start_time).toISOString().split('T')[0];
        openTimeInputModal(date);
        
        // 填充现有记录数据
        const recordTypeEl = document.getElementById('record-type');
        const inputHoursEl = document.getElementById('input-hours');
        const leaveHoursEl = document.getElementById('leave-hours');
        const inputShiftTypeEl = document.getElementById('input-shift-type');
        const inputDescriptionEl = document.getElementById('input-description');
        
        // 添加记录ID到模态框，用于后续保存
        const modalEl = document.getElementById('time-input-modal');
        modalEl.dataset.recordId = recordId;
        
        // 设置记录类型
        let recordType = 'normal';
        if (record.is_leave) {
            recordType = 'leave';
        } else if (record.is_early_off) {
            recordType = 'early-off';
        }
        recordTypeEl.value = recordType;
        
        // 设置工时或请假时长
        const hours = (record.duration || 0) / 60;
        if (record.is_leave) {
            leaveHoursEl.value = hours.toFixed(1);
        } else {
            inputHoursEl.value = hours.toFixed(1);
        }
        
        // 设置班别
        inputShiftTypeEl.value = record.shift_type || '白班';
        
        // 设置描述
        inputDescriptionEl.value = record.description || '';
        
        // 触发记录类型变化事件，更新表单显示（保留已回填工时）
        handleRecordTypeChange(true);
    } catch (error) {
        console.error('编辑记录失败:', error);
        alert('编辑记录失败: ' + error.message);
    }
}

// 保存工时记录（后端已做同日期查重：有则覆盖，无则新增）
async function saveTimeRecord() {
    console.log('保存工时记录函数调用');
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return;
    }

    // 获取表单元素
    const selectedDateEl = document.getElementById('selected-date');
    const recordTypeEl = document.getElementById('record-type');
    const inputHoursEl = document.getElementById('input-hours');
    const leaveHoursEl = document.getElementById('leave-hours');
    const inputShiftTypeEl = document.getElementById('input-shift-type');
    const inputDescriptionEl = document.getElementById('input-description');
    const modalEl = document.getElementById('time-input-modal');

    // 检查元素是否存在
    if (!selectedDateEl || !recordTypeEl || !inputShiftTypeEl || !inputDescriptionEl || !modalEl) {
        console.error('表单元素未找到');
        alert('保存失败: 表单元素未找到');
        return;
    }

    const date = selectedDateEl.value;
    const recordType = recordTypeEl.value;
    const shiftType = inputShiftTypeEl.value;
    const description = inputDescriptionEl.value;

    let hours, duration, isLeave, isEarlyOff;

    if (recordType === 'leave') {
        hours = parseFloat(leaveHoursEl.value);
        isLeave = true;
        isEarlyOff = false;
        duration = Math.round(hours * 60);

        if (isNaN(hours) || hours <= 0) {
            alert('请输入有效的请假时长');
            return;
        }
    } else {
        hours = parseFloat(inputHoursEl.value);
        isLeave = false;
        isEarlyOff = recordType === 'early-off';
        duration = Math.round(hours * 60);

        if (isNaN(hours) || hours <= 0) {
            alert('请输入有效的工时');
            return;
        }
    }

    console.log('表单数据:', { date, recordType, hours, shiftType, description, isLeave, isEarlyOff });

    if (!date) {
        alert('请选择有效的日期');
        return;
    }

    try {
        // 计算起止时间
        const startTime = `${date}T08:00:00`;
        const endTime = `${date}T${(8 + hours).toFixed(2).replace('.', ':')}:00`;

        const recordData = {
            user_id: user.id,
            start_time: startTime,
            end_time: endTime,
            duration: duration,
            shift_type: shiftType,
            description: description,
            is_leave: isLeave,
            is_early_off: isEarlyOff
        };

        // 后端 createTimeRecord 已实现查重：同用户+同日期有记录则 UPDATE，否则 INSERT
        console.log('发送创建/覆盖工时记录请求');
        const result = await timeRecordAPI.createTimeRecord(recordData);

        console.log('工时记录保存成功:', result);

        // 关闭模态框
        modalEl.classList.remove('active');
        delete modalEl.dataset.recordId;

        // 清空表单
        inputHoursEl.value = '';
        leaveHoursEl.value = '';
        inputDescriptionEl.value = '';

        // 更新日历和记录列表
        await generateCalendar();
        await loadTimeRecords();
        await loadMonthlyStats();

        const actionText = (result && result.action === 'update') ? '已覆盖原有记录' : '已新增记录';
        alert(`工时记录保存成功（${actionText}）`);
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败: ' + (error.message || '未知错误'));
    }
}

// 添加工别
function addShiftType() {
    const newShiftInput = document.getElementById('new-shift-name');
    if (!newShiftInput) return;
    
    const newShift = newShiftInput.value.trim();
    if (!newShift) {
        alert('请输入班别名称');
        return;
    }
    
    if (!shiftTypes.includes(newShift)) {
        shiftTypes.push(newShift);
        localStorage.setItem('shift_types', JSON.stringify(shiftTypes));
        updateShiftTypeOptions();
        renderShiftList();
        newShiftInput.value = '';
    } else {
        alert('该班别已存在');
    }
}

// 删除班别
function deleteShiftType(shift) {
    shiftTypes = shiftTypes.filter(s => s !== shift);
    localStorage.setItem('shift_types', JSON.stringify(shiftTypes));
    updateShiftTypeOptions();
    renderShiftList();
}

// 渲染班别列表
function renderShiftList() {
    const shiftListEl = document.getElementById('shift-list');
    if (!shiftListEl) return;
    
    shiftListEl.innerHTML = '';
    shiftTypes.forEach(shift => {
        const shiftItem = document.createElement('div');
        shiftItem.className = 'shift-item';
        shiftItem.innerHTML = `
            <span class="shift-name">${shift}</span>
            <button class="delete-shift" onclick="deleteShiftType('${shift}')">删除</button>
        `;
        shiftListEl.appendChild(shiftItem);
    });
}

// 删除过期排班
async function deleteExpiredSchedules() {
    const user = getCurrentUser();
    if (!user) return;
    
    if (confirm('确定要删除所有过期的排班计划吗？')) {
        try {
            const result = await scheduleAPI.deleteExpiredSchedules();
            alert(result.message);
        } catch (error) {
            console.error('删除过期排班失败:', error);
            alert('删除过期排班失败: ' + error.message);
        }
    }
}

// 初始化工时记录功能
async function initTimeRecord() {
    // 加载当月统计
    loadMonthlyStats();
    
    // 加载工时记录列表
    loadTimeRecords();
    
    // 生成日历
    await generateCalendar();
    
    // 初始化批量操作模态框
    initBatchModal();
    
    // 排班管理功能事件监听器
    const addScheduleBtn = document.getElementById('add-schedule-btn');
    if (addScheduleBtn) {
        addScheduleBtn.addEventListener('click', addSchedule);
    }
    
    const viewScheduleBtn = document.getElementById('view-schedule-btn');
    if (viewScheduleBtn) {
        viewScheduleBtn.addEventListener('click', viewSchedule);
    }
    
    // 添加删除过期排班按钮
    const scheduleContainer = document.querySelector('.schedule-container');
    if (scheduleContainer) {
        // 检查是否已经有删除过期排班按钮
        if (!document.getElementById('delete-expired-schedules-btn')) {
            const deleteExpiredBtn = document.createElement('button');
            deleteExpiredBtn.id = 'delete-expired-schedules-btn';
            deleteExpiredBtn.className = 'btn secondary';
            deleteExpiredBtn.textContent = '一键删除过期排班';
            deleteExpiredBtn.addEventListener('click', deleteExpiredSchedules);
            
            // 将按钮添加到排班容器中
            scheduleContainer.appendChild(deleteExpiredBtn);
        }
    }
    
    // 筛选按钮事件（保留原有功能）
    const filterBtn = document.getElementById('filter-btn');
    if (filterBtn) {
        filterBtn.addEventListener('click', function() {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            
            const filters = {};
            if (startDate) filters.start_date = `${startDate} 00:00:00`;
            if (endDate) filters.end_date = `${endDate} 23:59:59`;
            
            loadTimeRecords(filters);
        });
    }
    
    // 批量应用按钮事件
    const batchApplyBtn = document.getElementById('batch-apply-btn');
    if (batchApplyBtn) {
        batchApplyBtn.addEventListener('click', batchUpdateRecords);
    }
    
    // 日历导航按钮事件
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');
    
    if (prevMonthBtn) {
        prevMonthBtn.addEventListener('click', async function() {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            await generateCalendar();
            await loadTimeRecords(); // 同步加载当前月份的工时记录
        });
    }
    
    if (nextMonthBtn) {
        nextMonthBtn.addEventListener('click', async function() {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            await generateCalendar();
            await loadTimeRecords(); // 同步加载当前月份的工时记录
        });
    }
    
    // 保存工时记录按钮事件
    const saveTimeBtn = document.getElementById('save-time-btn');
    if (saveTimeBtn) {
        saveTimeBtn.addEventListener('click', saveTimeRecord);
    }
    
    // 班别设置按钮事件
    const shiftSettingsBtn = document.getElementById('shift-settings-btn');
    const shiftSettingsModal = document.getElementById('shift-settings-modal');
    
    if (shiftSettingsBtn && shiftSettingsModal) {
        shiftSettingsBtn.addEventListener('click', function() {
            renderShiftList();
            shiftSettingsModal.classList.add('active');
        });
    }
    
    // 添加班别按钮事件
    const addShiftBtn = document.getElementById('add-shift-btn');
    if (addShiftBtn) {
        addShiftBtn.addEventListener('click', addShiftType);
    }
    
    // 关闭模态框事件
    const closeBtns = document.querySelectorAll('.close-btn');
    closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // 点击模态框外部关闭
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // 复制工时按钮事件
    const copyTimeBtn = document.getElementById('copy-time-btn');
    if (copyTimeBtn) {
        copyTimeBtn.addEventListener('click', copyTimeRecords);
    }
    
    // Excel导入工时按钮事件
    const importExcelBtn = document.getElementById('import-excel-btn');
    if (importExcelBtn) {
        importExcelBtn.addEventListener('click', openImportExcelModal);
    }
    
    // 提交导入按钮事件
    const submitImportBtn = document.getElementById('submit-import-btn');
    if (submitImportBtn) {
        submitImportBtn.addEventListener('click', handleImportExcel);
    }
    
    // 取消导入按钮事件
    const cancelImportBtn = document.getElementById('cancel-import-btn');
    if (cancelImportBtn) {
        cancelImportBtn.addEventListener('click', closeImportExcelModal);
    }
    
    // Excel文件选择事件（用于获取工作表列表）
    const importExcelFileInput = document.getElementById('import-excel-file');
    if (importExcelFileInput) {
        importExcelFileInput.addEventListener('change', handleExcelFileSelect);
    }
    
    // 初始化班别选项
    updateShiftTypeOptions();
}

// 打开Excel导入模态框
function openImportExcelModal() {
    const modal = document.getElementById('import-excel-modal');
    const fileInput = document.getElementById('import-excel-file');
    const sheetSelect = document.getElementById('import-sheet-select');
    
    if (modal) {
        modal.classList.add('active');
    }
    
    // 重置文件选择和工作表选择
    if (fileInput) {
        fileInput.value = '';
    }
    if (sheetSelect) {
        sheetSelect.innerHTML = '<option value="">请先选择Excel文件</option>';
        sheetSelect.disabled = true;
    }
}

// 关闭Excel导入模态框
function closeImportExcelModal() {
    const modal = document.getElementById('import-excel-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// 处理Excel文件选择（获取工作表列表）
async function handleExcelFileSelect(e) {
    const file = e.target.files[0];
    const sheetSelect = document.getElementById('import-sheet-select');
    
    if (!file || !file.name.endsWith('.xlsx')) {
        sheetSelect.innerHTML = '<option value="">请先选择Excel文件</option>';
        sheetSelect.disabled = true;
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const result = await fetchAPI('/time-records/import-excel/sheets', {
            method: 'POST',
            body: formData,
            headers: {}
        });
        
        // 填充工作表选择
        sheetSelect.innerHTML = '<option value="">默认工作表</option>';
        result.sheets.forEach(sheet => {
            const option = document.createElement('option');
            option.value = sheet;
            option.textContent = sheet;
            sheetSelect.appendChild(option);
        });
        sheetSelect.disabled = false;
        
    } catch (error) {
        alert('读取Excel文件失败: ' + error.message);
        sheetSelect.innerHTML = '<option value="">请先选择Excel文件</option>';
        sheetSelect.disabled = true;
    }
}

// 处理Excel导入
async function handleImportExcel() {
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return;
    }
    
    const fileInput = document.getElementById('import-excel-file');
    const sheetSelect = document.getElementById('import-sheet-select');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('请选择Excel文件');
        return;
    }
    
    const file = fileInput.files[0];
    const sheetName = sheetSelect.value || '';
    
    if (!file.name.endsWith('.xlsx')) {
        alert('请选择 .xlsx 格式的Excel文件');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', user.id);
        if (sheetName) {
            formData.append('sheet_name', sheetName);
        }
        
        const result = await fetchAPI('/time-records/import-excel', {
            method: 'POST',
            body: formData,
            headers: {}
        });
        
        alert(`导入完成！\n总记录数: ${result.total_rows}\n成功导入: ${result.success_count}\n重复跳过: ${result.duplicate_count}\n导入失败: ${result.error_count}`);
        
        // 关闭模态框并刷新页面
        closeImportExcelModal();
        await loadRecords(currentYear, currentMonth);
        
    } catch (error) {
        alert('导入失败: ' + error.message);
    }
}

// 打开复制工时模态框
function openCopyTimeModal(sourceDate) {
    const modal = document.getElementById('copy-time-modal');
    const sourceDateEl = document.getElementById('source-date');
    
    if (!modal || !sourceDateEl) return;
    
    sourceDateEl.value = sourceDate;
    modal.classList.add('active');
}

// 复制工时记录
async function copyTimeRecords() {
    const user = getCurrentUser();
    if (!user) return;
    
    const sourceDate = document.getElementById('source-date').value;
    const startDate = document.getElementById('copy-start-date').value;
    const endDate = document.getElementById('copy-end-date').value;
    
    if (!sourceDate || !startDate || !endDate) {
        alert('请选择完整的日期范围');
        return;
    }
    
    try {
        // 获取源日期的工时记录
        const sourceRecords = await timeRecordAPI.getTimeRecords(user.id, {
            start_date: `${sourceDate} 00:00:00`,
            end_date: `${sourceDate} 23:59:59`
        });
        
        if (sourceRecords.length === 0) {
            alert('源日期没有工时记录');
            return;
        }
        
        // 生成日期范围内的所有日期
        const start = new Date(startDate);
        const end = new Date(endDate);
        const allDates = [];
        
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const date = d.toISOString().split('T')[0];
            allDates.push(date);
        }
        
        // 检查目标日期范围内的每个日期是否已经有记录
        const existingRecords = await timeRecordAPI.getTimeRecords(user.id, {
            start_date: `${startDate}T00:00:00`,
            end_date: `${endDate}T23:59:59`
        });
        
        const existingDates = existingRecords.map(record => new Date(record.start_time).toISOString().split('T')[0]);
        const datesToCopy = allDates.filter(date => !existingDates.includes(date));
        
        if (datesToCopy.length === 0) {
            alert('所选日期范围内的所有日期都已有记录，无法复制记录');
            return;
        }
        
        // 复制记录到每个目标日期
        const copyPromises = datesToCopy.map(date => {
            return Promise.all(sourceRecords.map(record => {
                // 计算新的开始和结束时间
                const recordStart = new Date(record.start_time);
                const recordEnd = new Date(record.end_time);
                const duration = record.duration || 0;
                
                // 创建新记录
                return timeRecordAPI.createTimeRecord({
                    user_id: user.id,
                    start_time: `${date}T${recordStart.toTimeString().split(' ')[0]}`,
                    end_time: `${date}T${recordEnd.toTimeString().split(' ')[0]}`,
                    duration: duration,
                    shift_type: record.shift_type,
                    is_leave: record.is_leave,
                    description: record.description
                });
            }));
        });
        
        // 执行所有复制操作
        await Promise.all(copyPromises);
        
        // 关闭模态框
        document.getElementById('copy-time-modal').classList.remove('active');
        
        // 重新加载记录
        loadTimeRecords();
        generateCalendar();
        
        alert(`成功复制 ${sourceRecords.length} 条记录到 ${datesToCopy.length} 天`);
    } catch (error) {
        alert('复制失败: ' + error.message);
    }
}

// 自动记录当天工时（每天晚上8:00）
function setupAutoRecord() {
    const checkAutoRecord = async () => {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        
        // 每天晚上8:00自动记录当天工时
        if (hours === 20 && minutes === 0) {
            const user = getCurrentUser();
            if (user) {
                const today = now.toISOString().split('T')[0];
                
                try {
                    // 检查当天是否已经有记录
                    const existingRecords = await timeRecordAPI.getTimeRecords(user.id, {
                        start_date: `${today}T00:00:00`,
                        end_date: `${today}T23:59:59`
                    });
                    
                    if (existingRecords.length === 0) {
                        // 从后端API加载所有排班计划
                        const allSchedules = await scheduleAPI.getSchedules(user.id);
                        
                        // 检查当天是否有排班计划
                        const todayDate = new Date(today);
                        const matchingSchedule = allSchedules.find(schedule => {
                            const startDate = new Date(schedule.start_date);
                            const endDate = new Date(schedule.end_date);
                            return todayDate >= startDate && todayDate <= endDate;
                        });
                        
                        if (matchingSchedule) {
                            // 根据排班计划记录工时
                            const duration = Math.round(matchingSchedule.hours * 60); // 转换为分钟
                            await timeRecordAPI.createTimeRecord({
                                user_id: user.id,
                                start_time: `${today}T08:00:00`,
                                end_time: `${today}T${(8 + matchingSchedule.hours).toFixed(2).replace('.', ':')}:00`,
                                duration: duration,
                                shift_type: matchingSchedule.shift_type,
                                description: matchingSchedule.description || '系统自动记录',
                                is_leave: false
                            });
                            console.log('系统根据排班计划自动记录当天工时');
                            // 更新当月统计
                            loadMonthlyStats();
                        } else {
                            console.log('当天没有排班计划，不自动记录工时');
                        }
                    }
                } catch (error) {
                    console.error('自动记录工时失败:', error);
                }
            }
        }
    };
    
    // 每分钟检查一次
    setInterval(checkAutoRecord, 60000);
}

// 暴露全局函数
window.deleteRecord = deleteRecord;
window.deleteShiftType = deleteShiftType;
window.openCopyTimeModal = openCopyTimeModal;
window.copyTimeRecords = copyTimeRecords;
window.initTimeRecord = initTimeRecord;
window.setupAutoRecord = setupAutoRecord;
window.cleanupDuplicates = cleanupDuplicates;