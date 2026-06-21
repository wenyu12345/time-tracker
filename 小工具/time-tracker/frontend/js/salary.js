// 工资计算逻辑

// 加载薪资等级列表
async function loadSalaryLevels() {
    const salaryLevelSelect = document.getElementById('salary-level');
    if (!salaryLevelSelect) return;
    
    try {
        const levels = await salaryAPI.getSalaryLevels();
        
        // 清空现有选项
        salaryLevelSelect.innerHTML = '';
        
        // 添加薪资等级选项
        levels.forEach(level => {
            const option = document.createElement('option');
            option.value = level.level;
            option.textContent = `${level.level} - ${level.base_salary}元`;
            salaryLevelSelect.appendChild(option);
        });
    } catch (error) {
        console.error('加载薪资等级失败:', error);
    }
}

// 保存工资信息
async function saveSalaryInfo() {
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return;
    }
    
    const month = document.getElementById('salary-month').value;
    const utilityFee = parseFloat(document.getElementById('utility-fee').value) || 0;
    const insurance = parseFloat(document.getElementById('insurance').value) || 0;
    const simulatedHours = parseFloat(document.getElementById('simulated-hours').value) || 0;
    const performanceBonus = parseFloat(document.getElementById('performance-bonus').value) || 0;
    
    if (!month) {
        alert('请选择月份');
        return;
    }
    
    try {
        // 自动从工时记录中提取请假时间
        const leaveHours = await getLeaveHoursFromRecords(user.id, month);
        
        // 更新页面上的请假时间输入框
        const leaveHoursInput = document.getElementById('leave-hours');
        if (leaveHoursInput) {
            leaveHoursInput.value = leaveHours;
        }
        
        await salaryAPI.saveSalaryInfo({
            user_id: user.id,
            month: month,
            salary_level: user.salary_level || 'E17', // 使用用户的薪级
            utility_fee: utilityFee,
            insurance: insurance,
            leave_hours: leaveHours,
            simulated_hours: simulatedHours,
            total_night_shifts: 0, // 夜班天数由系统自动计算
            performance_bonus: performanceBonus // 添加绩效奖励
        });
        
        alert('工资信息保存成功');
        return true;
    } catch (error) {
        alert('保存失败: ' + error.message);
        return false;
    }
}

// 从工时记录中提取请假时间
async function getLeaveHoursFromRecords(userId, month) {
    try {
        // 计算月份的开始和结束日期
        const [year, monthNum] = month.split('-');
        const startDate = `${year}-${monthNum}-01T00:00:00`;
        const endDate = new Date(year, monthNum, 0).toISOString();
        
        // 获取当月的所有工时记录
        const records = await timeRecordAPI.getTimeRecords(userId, {
            start_date: startDate,
            end_date: endDate
        });
        
        // 计算请假总时长
        let totalLeaveHours = 0;
        records.forEach(record => {
            if (record.is_leave) {
                totalLeaveHours += (record.duration || 0) / 60;
            }
        });
        
        return totalLeaveHours;
    } catch (error) {
        console.error('提取请假时间失败:', error);
        return 0;
    }
}

// 计算工资
async function calculateSalary() {
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return;
    }
    
    const month = document.getElementById('salary-month').value;
    if (!month) {
        alert('请选择月份');
        return;
    }
    
    // 计算工资前先保存参数，确保水电费和五险一金的值被保存
    await saveSalaryInfo();
    
    // 获取模拟总工时
    const simulatedHours = parseFloat(document.getElementById('simulated-hours').value) || 0;
    
    try {
        const result = await salaryAPI.calculateSalary(user.id, month, simulatedHours);
        
        // 显示计算结果
        displaySalaryResult(result);
    } catch (error) {
        alert('计算失败: ' + error.message);
    }
}

// 显示工资计算结果
function displaySalaryResult(result) {
    const resultDiv = document.getElementById('salary-result');
    if (!resultDiv) return;
    
    const details = result.salary_details;
    
    // 获取绩效奖励值，默认为0
    const performanceBonus = parseFloat(document.getElementById('performance-bonus').value) || 0;
    
    // 计算包含绩效奖励的实发工资
    const netSalaryWithBonus = details.net_salary + performanceBonus;
    
    resultDiv.innerHTML = `
        <h3>${result.month}月工资计算结果</h3>
        <div class="salary-item">
            <span class="salary-label">实际总工时</span>
            <span class="salary-value">${result.total_hours}小时</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">自动计算夜班天数</span>
            <span class="salary-value">${result.night_shifts}天</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">底薪</span>
            <span class="salary-value">${details.base_salary.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">满勤奖</span>
            <span class="salary-value">${details.attendance_bonus.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">加班费</span>
            <span class="salary-value">${details.overtime_pay.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">夜班补贴</span>
            <span class="salary-value">${details.night_shift_allowance.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">工龄奖</span>
            <span class="salary-value">${details.seniority_bonus.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">绩效奖励</span>
            <span class="salary-value">${performanceBonus >= 0 ? '+' : ''}${performanceBonus.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">税前工资</span>
            <span class="salary-value">${details.pre_tax_salary.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">水电费</span>
            <span class="salary-value">-${details.utility_fee.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">五险一金</span>
            <span class="salary-value">-${details.insurance.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">税费</span>
            <span class="salary-value">-${details.tax.toFixed(2)}元</span>
        </div>
        <div class="salary-item">
            <span class="salary-label">实发工资（含绩效）</span>
            <span class="salary-value">${netSalaryWithBonus.toFixed(2)}元</span>
        </div>
    `;
}

// 保存工资计算参数到服务器
async function saveSalaryParams() {
    const user = getCurrentUser();
    if (!user) {
        alert('请先登录');
        return;
    }
    
    // 调用saveSalaryInfo函数，将参数保存到服务器
    const success = await saveSalaryInfo();
    if (success) {
        alert('工资计算参数已保存到服务器');
    }
}

// 从服务器加载工资计算参数
async function loadSalaryParams() {
    const user = getCurrentUser();
    if (!user) return;
    
    // 获取当前日期，根据3号规则确定默认月份
    const now = new Date();
    const day = now.getDate();
    let year = now.getFullYear();
    let month = now.getMonth();
    
    // 如果当前日期 <= 3号，则默认月份为上个月
    if (day <= 3) {
        month = month - 1;
        if (month < 0) {
            month = 11;
            year = year - 1;
        }
    }
    
    // 格式化月份为YYYY-MM格式
    const defaultMonth = `${year}-${String(month + 1).padStart(2, '0')}`;
    const monthValue = document.getElementById('salary-month').value || defaultMonth;
    
    try {
        // 从服务器获取工资信息
        const salaryInfo = await salaryAPI.getSalaryInfo(user.id, monthValue);
        
        // 设置表单值
        const utilityFeeEl = document.getElementById('utility-fee');
        const insuranceEl = document.getElementById('insurance');
        const leaveHoursEl = document.getElementById('leave-hours');
        const simulatedHoursEl = document.getElementById('simulated-hours');
        const performanceBonusEl = document.getElementById('performance-bonus');
        
        if (utilityFeeEl) utilityFeeEl.value = salaryInfo.utility_fee || '';
        if (insuranceEl) insuranceEl.value = salaryInfo.insurance || '';
        if (leaveHoursEl) leaveHoursEl.value = salaryInfo.leave_hours || '';
        if (simulatedHoursEl) simulatedHoursEl.value = salaryInfo.simulated_hours || '';
        if (performanceBonusEl) performanceBonusEl.value = salaryInfo.performance_bonus || '';
        
        console.log('从服务器加载工资参数成功');
    } catch (error) {
        console.error('从服务器加载工资计算参数失败:', error);
        // 如果服务器加载失败，尝试从本地存储加载
        loadLocalSalaryParams();
    }
}

// 从本地存储加载工资计算参数（备用）
function loadLocalSalaryParams() {
    const user = getCurrentUser();
    if (!user) return;
    
    // 从本地存储加载
    const savedParams = localStorage.getItem(`salary_params_${user.id}`);
    
    try {
        const salaryMonthEl = document.getElementById('salary-month');
        
        if (savedParams) {
            const params = JSON.parse(savedParams);
            
            // 设置表单值（不包括薪级，薪级从用户资料中获取）
            const utilityFeeEl = document.getElementById('utility-fee');
            const insuranceEl = document.getElementById('insurance');
            const leaveHoursEl = document.getElementById('leave-hours');
            const simulatedHoursEl = document.getElementById('simulated-hours');
            const performanceBonusEl = document.getElementById('performance-bonus');
            
            if (salaryMonthEl && params.month) salaryMonthEl.value = params.month;
            if (utilityFeeEl && params.utilityFee) utilityFeeEl.value = params.utilityFee;
            if (insuranceEl && params.insurance) insuranceEl.value = params.insurance;
            if (leaveHoursEl && params.leaveHours) leaveHoursEl.value = params.leaveHours;
            if (simulatedHoursEl && params.simulatedHours) simulatedHoursEl.value = params.simulatedHours;
            if (performanceBonusEl && params.performanceBonus) performanceBonusEl.value = params.performanceBonus;
            
            console.log('从本地存储加载工资参数成功');
        } else {
            // 如果本地存储没有保存参数，设置默认月份
            // 获取当前日期，根据3号规则确定默认月份
            const now = new Date();
            const day = now.getDate();
            let year = now.getFullYear();
            let month = now.getMonth();
            
            // 如果当前日期 <= 3号，则默认月份为上个月
            if (day <= 3) {
                month = month - 1;
                if (month < 0) {
                    month = 11;
                    year = year - 1;
                }
            }
            
            // 格式化月份为YYYY-MM格式
            const defaultMonth = `${year}-${String(month + 1).padStart(2, '0')}`;
            if (salaryMonthEl) {
                salaryMonthEl.value = defaultMonth;
            }
            
            console.log('本地存储无参数，设置默认月份:', defaultMonth);
        }
    } catch (error) {
        console.error('加载工资计算参数失败:', error);
        // 加载失败时，设置默认月份
        const now = new Date();
        const day = now.getDate();
        let year = now.getFullYear();
        let month = now.getMonth();
        
        // 如果当前日期 <= 3号，则默认月份为上个月
        if (day <= 3) {
            month = month - 1;
            if (month < 0) {
                month = 11;
                year = year - 1;
            }
        }
        
        // 格式化月份为YYYY-MM格式
        const defaultMonth = `${year}-${String(month + 1).padStart(2, '0')}`;
        const salaryMonthEl = document.getElementById('salary-month');
        if (salaryMonthEl) {
            salaryMonthEl.value = defaultMonth;
        }
    }
}

// 初始化工资计算功能
async function initSalaryCalculation() {
    // 加载薪资等级
    loadSalaryLevels();
    
    // 加载工资计算参数（不包括薪级）
    loadSalaryParams();
    
    // 自动从用户资料中获取薪级
    const user = getCurrentUser();
    const salaryLevelSelect = document.getElementById('salary-level');
    if (user && salaryLevelSelect) {
        // 打印调试信息
        console.log('当前用户信息:', user);
        
        // 设置用户的薪级
        salaryLevelSelect.value = user.salary_level || 'E17';
        // 禁用薪级选择框，因为薪级现在是从用户资料中获取的
        salaryLevelSelect.disabled = true;
        
        // 获取当前日期，根据3号规则确定默认月份
        const now = new Date();
        const day = now.getDate();
        let year = now.getFullYear();
        let month = now.getMonth();
        
        // 如果当前日期 <= 3号，则默认月份为上个月
        if (day <= 3) {
            month = month - 1;
            if (month < 0) {
                month = 11;
                year = year - 1;
            }
        }
        
        // 格式化月份为YYYY-MM格式
        const defaultMonth = `${year}-${String(month + 1).padStart(2, '0')}`;
        const selectedMonth = document.getElementById('salary-month').value || defaultMonth;
        // 设置默认月份
        document.getElementById('salary-month').value = selectedMonth;
        
        // 先加载已保存的工资信息，再自动保存薪级
        await loadSalaryParams();
        
        // 只保存薪级，不覆盖其他字段
        try {
            await salaryAPI.saveSalaryInfo({
                user_id: user.id,
                month: selectedMonth,
                salary_level: user.salary_level || 'E17',
                // 其他字段使用默认值，避免覆盖已保存的值
                utility_fee: parseFloat(document.getElementById('utility-fee').value) || 0,
                insurance: parseFloat(document.getElementById('insurance').value) || 0,
                leave_hours: parseFloat(document.getElementById('leave-hours').value) || 0,
                simulated_hours: parseFloat(document.getElementById('simulated-hours').value) || 0,
                total_night_shifts: 0
            });
            console.log('薪级保存成功');
        } catch (error) {
            console.error('保存薪级失败:', error);
        }
    }
    
    // 计算工资按钮事件
    const calculateBtn = document.getElementById('calculate-salary-btn');
    if (calculateBtn) {
        calculateBtn.addEventListener('click', calculateSalary);
    }
    
    // 保存参数按钮事件
    const saveBtn = document.getElementById('save-salary-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveSalaryParams);
    }
}

// 暴露全局函数
window.initSalaryCalculation = initSalaryCalculation;