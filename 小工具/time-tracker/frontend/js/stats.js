// 统计分析逻辑

// 全局变量，用于存储当前图表实例
let currentChart = null;

// 加载统计数据
async function loadStats() {
    const user = getCurrentUser();
    if (!user) return;
    
    const statsType = document.getElementById('stats-type').value;
    
    try {
        let stats;
        
        switch (statsType) {
            case 'daily':
                const statsDate = document.getElementById('stats-date').value;
                if (!statsDate) {
                    alert('请选择日期');
                    return;
                }
                const date = statsDate.split('T')[0];
                stats = await statsAPI.getDailyStats(user.id, date);
                displayDailyStats(stats);
                break;
            
            case 'weekly':
                const weekStatsDate = document.getElementById('stats-date').value;
                if (!weekStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const weekDate = new Date(weekStatsDate);
                const year = weekDate.getFullYear();
                const week = getWeekNumber(weekDate);
                stats = await statsAPI.getWeeklyStats(user.id, year, week);
                displayWeeklyStats(stats);
                break;
            
            case 'monthly':
                const monthStatsDate = document.getElementById('stats-date').value;
                if (!monthStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const month = monthStatsDate.substring(0, 7);
                stats = await statsAPI.getMonthlyStats(user.id, month);
                displayMonthlyStats(stats);
                break;
            
            case 'project':
                const projectStatsDate = document.getElementById('stats-date').value;
                if (!projectStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const projectDate = projectStatsDate.split('T')[0];
                // 计算当月的开始和结束日期
                const startDate = projectDate.substring(0, 8) + '01';
                const endDate = new Date(new Date(projectDate).getFullYear(), new Date(projectDate).getMonth() + 1, 0).toISOString().split('T')[0];
                
                stats = await statsAPI.getProjectStats(user.id, {
                    start_date: `${startDate} 00:00:00`,
                    end_date: `${endDate} 23:59:59`
                });
                displayProjectStats(stats, `${startDate} 到 ${endDate}`);
                break;
            
            case 'shift':
                const shiftStatsDate = document.getElementById('stats-date').value;
                if (!shiftStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const shiftDate = shiftStatsDate.split('T')[0];
                // 计算当月的开始和结束日期
                const shiftStartDate = shiftDate.substring(0, 8) + '01';
                const shiftEndDate = new Date(new Date(shiftDate).getFullYear(), new Date(shiftDate).getMonth() + 1, 0).toISOString().split('T')[0];
                
                stats = await statsAPI.getShiftStats(user.id, {
                    start_date: `${shiftStartDate} 00:00:00`,
                    end_date: `${shiftEndDate} 23:59:59`
                });
                displayShiftStats(stats, `${shiftStartDate} 到 ${shiftEndDate}`);
                break;
            
            case 'trend':
                const trendStatsDate = document.getElementById('stats-date').value;
                if (!trendStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const trendDate = trendStatsDate.split('T')[0];
                // 计算当月的开始和结束日期
                const trendStartDate = trendDate.substring(0, 8) + '01';
                const trendEndDate = new Date(new Date(trendDate).getFullYear(), new Date(trendDate).getMonth() + 1, 0).toISOString().split('T')[0];
                
                stats = await statsAPI.getTrendStats(user.id, trendStartDate, trendEndDate);
                displayTrendStats(stats, `${trendStartDate} 到 ${trendEndDate}`);
                break;
            
            case 'attendance':
                const attendanceStatsDate = document.getElementById('stats-date').value;
                if (!attendanceStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const attendanceDate = attendanceStatsDate.split('T')[0];
                // 计算当月的开始和结束日期
                const attendanceStartDate = attendanceDate.substring(0, 8) + '01';
                const attendanceEndDate = new Date(new Date(attendanceDate).getFullYear(), new Date(attendanceDate).getMonth() + 1, 0).toISOString().split('T')[0];
                
                stats = await statsAPI.getAttendanceStats(user.id, attendanceStartDate, attendanceEndDate);
                displayAttendanceStats(stats);
                break;
            
            case 'overtime':
                const overtimeStatsDate = document.getElementById('stats-date').value;
                if (!overtimeStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const overtimeDate = overtimeStatsDate.split('T')[0];
                // 计算当月的开始和结束日期
                const overtimeStartDate = overtimeDate.substring(0, 8) + '01';
                const overtimeEndDate = new Date(new Date(overtimeDate).getFullYear(), new Date(overtimeDate).getMonth() + 1, 0).toISOString().split('T')[0];
                
                stats = await statsAPI.getOvertimeStats(user.id, overtimeStartDate, overtimeEndDate);
                displayOvertimeStats(stats);
                break;
            
            case 'distribution':
                const distributionStatsDate = document.getElementById('stats-date').value;
                if (!distributionStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const distributionDate = distributionStatsDate.split('T')[0];
                // 计算当月的开始和结束日期
                const distributionStartDate = distributionDate.substring(0, 8) + '01';
                const distributionEndDate = new Date(new Date(distributionDate).getFullYear(), new Date(distributionDate).getMonth() + 1, 0).toISOString().split('T')[0];
                
                stats = await statsAPI.getHoursDistribution(user.id, distributionStartDate, distributionEndDate);
                displayHoursDistribution(stats);
                break;
            
            case 'comparison':
                const comparisonStatsDate = document.getElementById('stats-date').value;
                if (!comparisonStatsDate) {
                    alert('请选择日期');
                    return;
                }
                const comparisonDate = comparisonStatsDate.split('T')[0];
                
                // 询问用户要查看哪种周期的对比
                const comparisonPeriod = prompt('请选择对比周期：\n1. 月度对比\n2. 周度对比');
                const period = comparisonPeriod === '1' ? 'month' : 'week';
                
                stats = await statsAPI.getComparisonStats(user.id, period, comparisonDate);
                displayComparisonStats(stats);
                break;
            
            case 'custom':
                const customStartDate = document.getElementById('start-date').value;
                const customEndDate = document.getElementById('end-date').value;
                if (!customStartDate || !customEndDate) {
                    alert('请选择开始日期和结束日期');
                    return;
                }
                
                // 询问用户要查看哪种类型的统计
                const customStatsType = prompt('请选择统计类型：\n1. 项目统计\n2. 班别统计\n3. 工时趋势图\n4. 出勤率统计\n5. 加班情况分析\n6. 工时分布分析\n7. 对比分析');
                if (customStatsType === '1') {
                    stats = await statsAPI.getProjectStats(user.id, {
                        start_date: `${customStartDate} 00:00:00`,
                        end_date: `${customEndDate} 23:59:59`
                    });
                    displayProjectStats(stats, `${customStartDate} 到 ${customEndDate}`);
                } else if (customStatsType === '2') {
                    stats = await statsAPI.getShiftStats(user.id, {
                        start_date: `${customStartDate} 00:00:00`,
                        end_date: `${customEndDate} 23:59:59`
                    });
                    displayShiftStats(stats, `${customStartDate} 到 ${customEndDate}`);
                } else if (customStatsType === '3') {
                    stats = await statsAPI.getTrendStats(user.id, customStartDate, customEndDate);
                    displayTrendStats(stats, `${customStartDate} 到 ${customEndDate}`);
                } else if (customStatsType === '4') {
                    stats = await statsAPI.getAttendanceStats(user.id, customStartDate, customEndDate);
                    displayAttendanceStats(stats);
                } else if (customStatsType === '5') {
                    stats = await statsAPI.getOvertimeStats(user.id, customStartDate, customEndDate);
                    displayOvertimeStats(stats);
                } else if (customStatsType === '6') {
                    stats = await statsAPI.getHoursDistribution(user.id, customStartDate, customEndDate);
                    displayHoursDistribution(stats);
                } else if (customStatsType === '7') {
                    // 询问用户要查看哪种周期的对比
                    const customComparisonPeriod = prompt('请选择对比周期：\n1. 月度对比\n2. 周度对比');
                    const customPeriod = customComparisonPeriod === '1' ? 'month' : 'week';
                    stats = await statsAPI.getComparisonStats(user.id, customPeriod, customEndDate);
                    displayComparisonStats(stats);
                } else {
                    alert('无效的统计类型');
                }
                break;
            
            default:
                alert('不支持的统计类型');
                return;
        }
    } catch (error) {
        alert('加载统计数据失败: ' + error.message);
    }
}

// 显示日统计
function displayDailyStats(stats) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['总工时', '请假', '夜班'],
            datasets: [{
                label: stats.date,
                data: [stats.total_hours, stats.leave_hours, stats.night_shifts],
                backgroundColor: [
                    'rgba(74, 144, 226, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(108, 117, 125, 0.8)'
                ],
                borderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                borderWidth: 1,
                hoverBackgroundColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                hoverBorderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                hoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${stats.date} 日统计`,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(74, 144, 226, 1)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.label === '夜班') {
                                    label += context.parsed.y + ' 天';
                                } else {
                                    label += context.parsed.y + ' 小时';
                                }
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '数值'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// 显示周统计
function displayWeeklyStats(stats) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['总工时', '请假', '夜班'],
            datasets: [{
                label: `${stats.year}年第${stats.week}周`,
                data: [stats.total_hours, stats.leave_hours, stats.night_shifts],
                backgroundColor: [
                    'rgba(74, 144, 226, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(108, 117, 125, 0.8)'
                ],
                borderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                borderWidth: 1,
                hoverBackgroundColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                hoverBorderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                hoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${stats.year}年第${stats.week}周统计`,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(74, 144, 226, 1)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.label === '夜班') {
                                    label += context.parsed.y + ' 天';
                                } else {
                                    label += context.parsed.y + ' 小时';
                                }
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '数值'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// 显示月统计
function displayMonthlyStats(stats) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['总工时', '请假', '夜班'],
            datasets: [{
                label: stats.month,
                data: [stats.total_hours, stats.leave_hours, stats.night_shifts],
                backgroundColor: [
                    'rgba(74, 144, 226, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(108, 117, 125, 0.8)'
                ],
                borderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                borderWidth: 1,
                hoverBackgroundColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                hoverBorderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                hoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${stats.month} 月统计`,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(74, 144, 226, 1)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.label === '夜班') {
                                    label += context.parsed.y + ' 天';
                                } else {
                                    label += context.parsed.y + ' 小时';
                                }
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '数值'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// 显示项目统计
function displayProjectStats(stats, label) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 准备图表数据
    const labels = stats.map(item => item.project_name);
    const data = stats.map(item => item.total_hours);
    const colors = stats.map(item => item.project_color || getRandomColor());
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: label || '项目工时分布',
                data: data,
                backgroundColor: colors.map(color => `${color}80`), // 添加透明度
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: label || '项目工时分布'
                }
            }
        }
    });
}

// 显示班别统计
function displayShiftStats(stats, label) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 准备图表数据
    const labels = Object.keys(stats);
    const data = Object.values(stats);
    const colors = ['#4a90e2', '#6c757d'];
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: label || '班别工时分布',
                data: data,
                backgroundColor: colors.map(color => `${color}80`), // 添加透明度
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: label || '班别工时分布'
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 显示工时趋势图
function displayTrendStats(stats, label) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 准备图表数据
    const labels = stats.map(item => item.date);
    const data = stats.map(item => item.hours);
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label || '工时趋势图',
                data: data,
                backgroundColor: 'rgba(74, 144, 226, 0.2)',
                borderColor: 'rgba(74, 144, 226, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: 'rgba(74, 144, 226, 1)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: label || '工时趋势图'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '工时（小时）'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '日期'
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// 获取周数
function getWeekNumber(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

// 生成随机颜色
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// 初始化统计分析功能
function initStats() {
    // 设置默认日期为今天
    const statsDateEl = document.getElementById('stats-date');
    if (statsDateEl) {
        const now = new Date().toISOString().split('T')[0];
        statsDateEl.value = now;
        document.getElementById('start-date').value = now;
        document.getElementById('end-date').value = now;
    }
    
    // 查看统计按钮事件
    const statsBtn = document.getElementById('stats-btn');
    if (statsBtn) {
        statsBtn.addEventListener('click', loadStats);
    }
    
    // 统计类型选择事件
    const statsTypeEl = document.getElementById('stats-type');
    if (statsTypeEl) {
        statsTypeEl.addEventListener('change', function() {
            const statsDateEl = document.getElementById('stats-date');
            const customDateRangeEl = document.getElementById('custom-date-range');
            
            if (this.value === 'custom') {
                statsDateEl.style.display = 'none';
                customDateRangeEl.style.display = 'flex';
                customDateRangeEl.style.gap = '0.5rem';
            } else {
                statsDateEl.style.display = 'block';
                customDateRangeEl.style.display = 'none';
            }
        });
    }
}

// 显示出勤率统计
function displayAttendanceStats(stats) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['出勤天数', '缺勤天数'],
            datasets: [{
                label: `${stats.start_date} 到 ${stats.end_date} 出勤率`,
                data: [stats.attendance_days, stats.total_days - stats.attendance_days],
                backgroundColor: [
                    'rgba(74, 144, 226, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ],
                borderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(220, 53, 69, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${stats.start_date} 到 ${stats.end_date} 出勤率: ${stats.attendance_rate}%`
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed !== null) {
                                label += context.parsed + ' 天';
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// 显示加班情况分析
function displayOvertimeStats(stats) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['总加班小时数', '加班天数', '最大单日加班', '平均每日加班'],
            datasets: [{
                label: `${stats.start_date} 到 ${stats.end_date} 加班情况`,
                data: [stats.total_overtime_hours, stats.overtime_days, stats.max_overtime_hours, stats.average_overtime_hours],
                backgroundColor: [
                    'rgba(74, 144, 226, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(40, 167, 69, 0.8)'
                ],
                borderColor: [
                    'rgba(74, 144, 226, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(40, 167, 69, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${stats.start_date} 到 ${stats.end_date} 加班情况分析`
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.label === '加班天数') {
                                    label += context.parsed.y + ' 天';
                                } else {
                                    label += context.parsed.y + ' 小时';
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '数值'
                    }
                }
            }
        }
    });
}

// 显示工时分布分析
function displayHoursDistribution(stats) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 准备图表数据
    const labels = stats.distribution.map(item => item.hour + ':00');
    const data = stats.distribution.map(item => item.hours);
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${stats.start_date} 到 ${stats.end_date} 工时分布`,
                data: data,
                backgroundColor: 'rgba(74, 144, 226, 0.2)',
                borderColor: 'rgba(74, 144, 226, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: 'rgba(74, 144, 226, 1)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${stats.start_date} 到 ${stats.end_date} 工时分布分析`
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + ' 小时';
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '工时（小时）'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '小时'
                    },
                    ticks: {
                        maxRotation: 0,
                        minRotation: 0
                    }
                }
            }
        }
    });
}

// 显示对比分析
function displayComparisonStats(stats) {
    const chartCanvas = document.getElementById('chart-canvas');
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // 销毁现有图表
    if (currentChart) {
        currentChart.destroy();
    }
    
    // 检查Chart构造函数是否存在
    if (typeof Chart === 'undefined') {
        alert('Chart.js库未正确加载');
        return;
    }
    
    // 创建新图表
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['总工时', '请假工时', '夜班天数'],
            datasets: [{
                label: stats.current.period,
                data: [stats.current.stats.total_hours, stats.current.stats.leave_hours, stats.current.stats.night_shifts],
                backgroundColor: 'rgba(74, 144, 226, 0.8)',
                borderColor: 'rgba(74, 144, 226, 1)',
                borderWidth: 1
            }, {
                label: stats.previous.period,
                data: [stats.previous.stats.total_hours, stats.previous.stats.leave_hours, stats.previous.stats.night_shifts],
                backgroundColor: 'rgba(108, 117, 125, 0.8)',
                borderColor: 'rgba(108, 117, 125, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${stats.current.period} 与 ${stats.previous.period} 对比分析`
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.label === '夜班天数') {
                                    label += context.parsed.y + ' 天';
                                } else {
                                    label += context.parsed.y + ' 小时';
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '数值'
                    }
                }
            }
        }
    });
}

// 暴露全局函数
window.initStats = initStats;