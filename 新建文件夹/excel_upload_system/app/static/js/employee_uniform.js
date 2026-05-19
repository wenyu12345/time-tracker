/**
 * 员工工装管理系统JavaScript
 * 修复按钮失效问题
 */

// 全局变量
let employees = [];
let uniformTypes = [];
let uniformRecords = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('员工工装管理系统初始化...');
    
    // 防止重复初始化
    if (window.employeeUniformInitialized) {
        console.log('系统已初始化，跳过重复初始化');
        return;
    }
    window.employeeUniformInitialized = true;
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 加载初始数据
    loadInitialData();
});

// 绑定所有事件监听器
function bindEventListeners() {
    console.log('绑定事件监听器...');
    
    // 选项卡切换事件
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function (e) {
            const targetId = e.target.getAttribute('data-bs-target');
            console.log('切换到选项卡:', targetId);
            
            switch(targetId) {
                case '#employees':
                    loadEmployees();
                    break;
                case '#uniform-types':
                    // 如果工装类型数据已加载，只需要渲染表格
                    if (uniformTypes.length > 0) {
                        renderUniformTypeTable();
                    } else {
                        loadUniformTypes();
                    }
                    break;
                case '#issuance':
                    loadQuickStats();
                    break;
                case '#records':
                    loadRecords();
                    break;
                case '#summary':
                    // 总是先确保工装类型数据已加载
                    Promise.all([
                        uniformTypes.length > 0 ? Promise.resolve(uniformTypes) : 
                            fetch('/employee_uniform/uniform_types').then(r => r.json()).then(d => d.success ? d.data : []),
                        fetch('/employee_uniform/employees').then(r => r.json()).then(d => d.success ? d.data : [])
                    ]).then(([types, employees]) => {
                        if (types.length > 0) {
                            uniformTypes = types;
                        }
                        if (employees.length > 0) {
                            employees = employees;
                        }
                        initializeSummaryFilters();
                        loadSummaryData();
                    }).catch(error => {
                        console.error('初始化汇总筛选失败:', error);
                        initializeSummaryFilters(); // 即使失败也尝试初始化
                        loadSummaryData();
                    });
                    break;
            }
        });
    });
    
    // 添加员工按钮
    const addEmployeeBtn = document.getElementById('addEmployeeBtn');
    if (addEmployeeBtn) {
        console.log('找到添加员工按钮');
        addEmployeeBtn.addEventListener('click', function() {
            console.log('添加员工按钮被点击');
            showAddEmployeeModal();
        });
    } else {
        console.error('找不到添加员工按钮');
    }
    
    // 保存员工按钮
    const saveEmployeeBtn = document.getElementById('saveEmployeeBtn');
    if (saveEmployeeBtn) {
        saveEmployeeBtn.addEventListener('click', saveEmployee);
    }
    
    // 添加工装类型按钮
    const addUniformTypeBtn = document.getElementById('addUniformTypeBtn');
    if (addUniformTypeBtn) {
        addUniformTypeBtn.addEventListener('click', showAddUniformTypeModal);
    }
    
    // 保存工装类型按钮
    const saveUniformTypeBtn = document.getElementById('saveUniformTypeBtn');
    if (saveUniformTypeBtn) {
        saveUniformTypeBtn.addEventListener('click', saveUniformType);
    }
    
    // 发放工装按钮
    const issueUniformBtn = document.getElementById('issueUniformBtn');
    if (issueUniformBtn) {
        issueUniformBtn.addEventListener('click', showIssueUniformModal);
    }
    
    // 汇总筛选按钮
    const applySummaryFilterBtn = document.getElementById('applySummaryFilter');
    if (applySummaryFilterBtn) {
        applySummaryFilterBtn.addEventListener('click', loadSummaryData);
    }
    
    // 汇总刷新按钮
    const refreshSummaryBtn = document.getElementById('refreshSummaryBtn');
    if (refreshSummaryBtn) {
        refreshSummaryBtn.addEventListener('click', loadSummaryData);
    }
    
    // 筛选条件变化事件监听
    const summaryUniformTypeFilter = document.getElementById('summaryUniformTypeFilter');
    if (summaryUniformTypeFilter) {
        summaryUniformTypeFilter.addEventListener('change', loadSummaryData);
    }
    
    const summaryYearFilter = document.getElementById('summaryYearFilter');
    if (summaryYearFilter) {
        summaryYearFilter.addEventListener('change', loadSummaryData);
    }
    
    // 重置筛选按钮
    const resetSummaryFilterBtn = document.getElementById('resetSummaryFilter');
    if (resetSummaryFilterBtn) {
        resetSummaryFilterBtn.addEventListener('click', function() {
            document.getElementById('summarySearch').value = '';
            document.getElementById('summaryUniformTypeFilter').value = '';
            document.getElementById('summaryYearFilter').value = '';
            loadSummaryData();
        });
    }
    
    // 搜索框回车事件
    const summarySearch = document.getElementById('summarySearch');
    if (summarySearch) {
        summarySearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                loadSummaryData();
            }
        });
    }
    
    // 确认发放按钮
    const confirmIssueBtn = document.getElementById('confirmIssueBtn');
    if (confirmIssueBtn) {
        confirmIssueBtn.addEventListener('click', issueUniform);
    }
    
    // 领取记录筛选按钮
    const filterRecordsBtn = document.getElementById('filterRecordsBtn');
    if (filterRecordsBtn) {
        filterRecordsBtn.addEventListener('click', filterRecords);
    }
    
    // 领取记录搜索框回车事件
    const recordSearch = document.getElementById('recordSearch');
    if (recordSearch) {
        recordSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                filterRecords();
            }
        });
    }
    
    // 领取记录工装类型筛选变化事件
    const uniformTypeFilter = document.getElementById('uniformTypeFilter');
    if (uniformTypeFilter) {
        uniformTypeFilter.addEventListener('change', filterRecords);
    }
    
    // 批量添加员工按钮
    const batchAddEmployeeBtn = document.getElementById('batchAddEmployeeBtn');
    if (batchAddEmployeeBtn) {
        batchAddEmployeeBtn.addEventListener('click', function() {
            console.log('批量添加员工按钮被点击');
            showBatchAddEmployeeModal();
        });
    }
    
    // 预览批量员工数据
    const previewBatchEmployeesBtn = document.getElementById('previewBatchEmployees');
    if (previewBatchEmployeesBtn) {
        previewBatchEmployeesBtn.addEventListener('click', previewBatchEmployees);
    }
    
    // 清空批量数据
    const clearBatchDataBtn = document.getElementById('clearBatchData');
    if (clearBatchDataBtn) {
        clearBatchDataBtn.addEventListener('click', clearBatchData);
    }
    
    // 批量保存员工
    const saveBatchEmployeesBtn = document.getElementById('saveBatchEmployeesBtn');
    if (saveBatchEmployeesBtn) {
        saveBatchEmployeesBtn.addEventListener('click', saveBatchEmployees);
    }
    
    // 批量发放工装按钮
    const batchIssueUniformBtn = document.getElementById('batchIssueUniformBtn');
    if (batchIssueUniformBtn) {
        batchIssueUniformBtn.addEventListener('click', showBatchIssueUniformModal);
    }
    
    // 确认删除按钮
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', confirmDelete);
    }
    
    // 表单提交事件
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
        });
    });
    
    console.log('事件监听器绑定完成');
}

// 加载初始数据
function loadInitialData() {
    console.log('加载初始数据...');
    
    // 总是先加载工装类型数据，因为其他页面可能需要使用
    loadUniformTypes();
    
    // 然后根据当前选项卡加载对应数据
    const activeTab = document.querySelector('.tab-pane.active').id;
    
    switch(activeTab) {
        case 'employees':
            loadEmployees();
            break;
        case 'uniform-types':
            // 工装类型已经加载，只需要渲染表格
            renderUniformTypeTable();
            break;
        case 'issuance':
            loadQuickStats();
            break;
        case 'records':
            loadRecords();
            break;
        case 'summary':
            loadSummaryData();
            break;
        default:
            // 默认加载员工列表
            loadEmployees();
    }
}

// 加载员工列表
function loadEmployees() {
    console.log('加载员工列表...');
    
    fetch('/employee_uniform/employees')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(data => {
            console.log('员工列表数据:', data);
            
            if (data.success && Array.isArray(data.data)) {
                employees = data.data;
                renderEmployeeTable();
                
                // 更新快速统计
                updateQuickStats();
            } else {
                console.error('员工数据格式错误:', data);
                showToast('加载员工列表失败', 'error');
            }
        })
        .catch(error => {
            console.error('加载员工列表失败:', error);
            showToast('加载员工列表失败: ' + error.message, 'error');
        });
}

// 渲染员工表格
function renderEmployeeTable() {
    const tbody = document.getElementById('employeeTableBody');
    if (!tbody) {
        console.error('找不到员工表格主体');
        return;
    }
    
    if (employees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">暂无员工数据</td></tr>';
        return;
    }
    
    let html = '';
    employees.forEach(employee => {
        html += `
            <tr>
                <td>${employee.employee_id}</td>
                <td>${employee.name}</td>
                <td>${employee.created_at}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="editEmployee('${employee.employee_id}', '${employee.name}')">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="showDeleteConfirm('employee', '${employee.employee_id}', '员工 ${employee.name} (${employee.employee_id})')">删除</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 加载工装类型
function loadUniformTypes() {
    console.log('加载工装类型...');
    
    fetch('/employee_uniform/uniform_types')
        .then(response => response.json())
        .then(data => {
            console.log('工装类型数据:', data);
            
            if (data.success && Array.isArray(data.data)) {
                uniformTypes = data.data;
                renderUniformTypeTable();
                
                // 更新快速统计
                updateQuickStats();
            } else {
                console.error('工装类型数据格式错误:', data);
                showToast('加载工装类型失败', 'error');
            }
        })
        .catch(error => {
            console.error('加载工装类型失败:', error);
            showToast('加载工装类型失败', 'error');
        });
}

// 渲染工装类型表格
function renderUniformTypeTable() {
    const tbody = document.getElementById('uniformTypeTableBody');
    if (!tbody) {
        console.error('找不到工装类型表格主体');
        return;
    }
    
    if (uniformTypes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">暂无工装类型数据</td></tr>';
        return;
    }
    
    let html = '';
    uniformTypes.forEach(uniformType => {
        html += `
            <tr>
                <td>${uniformType.id}</td>
                <td>${uniformType.name}</td>
                <td>${uniformType.description || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="showDeleteConfirm('uniform_type', '${uniformType.id}', '工装类型 ${uniformType.name}')">删除</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 加载领取记录
function loadRecords() {
    console.log('加载领取记录...');
    
    // 确保工装类型数据已加载
    if (uniformTypes.length === 0) {
        fetch('/employee_uniform/uniform_types')
            .then(response => response.json())
            .then(data => {
                if (data.success && Array.isArray(data.data)) {
                    uniformTypes = data.data;
                    initializeRecordFilters();
                }
                loadRecordsData();
            })
            .catch(error => {
                console.error('加载工装类型失败:', error);
                initializeRecordFilters();
                loadRecordsData();
            });
    } else {
        initializeRecordFilters();
        loadRecordsData();
    }
}

// 加载领取记录数据
function loadRecordsData() {
    fetch('/employee_uniform/issuance_records')
        .then(response => response.json())
        .then(data => {
            console.log('领取记录数据:', data);
            
            if (data.success && Array.isArray(data.data)) {
                uniformRecords = data.data;
                renderRecordTable();
            } else {
                console.error('领取记录数据格式错误:', data);
                showToast('加载领取记录失败', 'error');
            }
        })
        .catch(error => {
            console.error('加载领取记录失败:', error);
            showToast('加载领取记录失败', 'error');
        });
}

// 初始化领取记录筛选选项
function initializeRecordFilters() {
    console.log('初始化领取记录筛选选项...');
    console.log('当前工装类型数据:', uniformTypes);
    
    // 加载工装类型选项
    const uniformTypeSelect = document.getElementById('uniformTypeFilter');
    if (uniformTypeSelect) {
        uniformTypeSelect.innerHTML = '<option value="">所有工装类型</option>';
        
        if (uniformTypes.length > 0) {
            uniformTypes.forEach(uniformType => {
                const option = document.createElement('option');
                option.value = uniformType.id;
                option.textContent = uniformType.name;
                uniformTypeSelect.appendChild(option);
            });
            console.log('领取记录工装类型选项加载成功，共', uniformTypes.length, '个选项');
        } else {
            console.warn('工装类型数据为空');
        }
    } else {
        console.error('找不到领取记录工装类型筛选下拉框');
    }
}

// 筛选领取记录
function filterRecords() {
    const searchTerm = document.getElementById('recordSearch')?.value.toLowerCase() || '';
    const uniformTypeId = document.getElementById('uniformTypeFilter')?.value || '';
    
    if (!uniformRecords || uniformRecords.length === 0) {
        return;
    }
    
    const filteredRecords = uniformRecords.filter(record => {
        // 搜索条件筛选
        const matchSearch = !searchTerm || 
            (record.employee_id && record.employee_id.toLowerCase().includes(searchTerm)) ||
            (record.employee_name && record.employee_name.toLowerCase().includes(searchTerm));
        
        // 工装类型筛选
        const matchUniformType = !uniformTypeId || 
            (record.uniform_type_id && record.uniform_type_id === uniformTypeId);
        
        return matchSearch && matchUniformType;
    });
    
    renderRecordTableFiltered(filteredRecords);
}

// 渲染领取记录表格
function renderRecordTable() {
    renderRecordTableFiltered(uniformRecords);
}

// 渲染筛选后的领取记录表格
function renderRecordTableFiltered(records) {
    const tbody = document.getElementById('recordTableBody');
    if (!tbody) {
        console.error('找不到领取记录表格主体');
        return;
    }
    
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无符合条件的记录</td></tr>';
        return;
    }
    
    let html = '';
    records.forEach(record => {
        html += `
            <tr>
                <td>${record.id}</td>
                <td>${record.employee_id}</td>
                <td>${record.employee_name || '-'}</td>
                <td>${record.uniform_type_name || '-'}</td>
                <td>${record.issue_date}</td>
                <td>${record.recorded_at || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="showDeleteConfirm('record', '${record.id}', '领取记录 #${record.id}')">删除</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 为汇总统计加载工装类型数据
function loadUniformTypesForSummary() {
    console.log('为汇总统计加载工装类型数据...');
    
    fetch('/employee_uniform/uniform_types')
        .then(response => response.json())
        .then(data => {
            if (data.success && Array.isArray(data.data)) {
                uniformTypes = data.data;
                console.log('工装类型数据加载成功:', uniformTypes);
                initializeSummaryFilters();
            } else {
                console.error('工装类型数据格式错误:', data);
            }
        })
        .catch(error => {
            console.error('加载工装类型失败:', error);
        });
}

// 初始化汇总筛选选项
function initializeSummaryFilters() {
    console.log('初始化汇总筛选选项...');
    console.log('当前工装类型数据:', uniformTypes);
    
    // 加载工装类型选项
    const uniformTypeSelect = document.getElementById('summaryUniformTypeFilter');
    if (uniformTypeSelect) {
        uniformTypeSelect.innerHTML = '<option value="">🧥 所有工装类型</option>';
        
        if (uniformTypes.length > 0) {
            uniformTypes.forEach(uniformType => {
                const option = document.createElement('option');
                option.value = uniformType.id;
                option.textContent = uniformType.name;
                uniformTypeSelect.appendChild(option);
            });
            console.log('工装类型选项加载成功，共', uniformTypes.length, '个选项');
        } else {
            console.warn('工装类型数据为空');
            // 添加重试按钮
            const retryOption = document.createElement('option');
            retryOption.value = '';
            retryOption.textContent = '点击刷新按钮重新加载';
            retryOption.disabled = true;
            uniformTypeSelect.appendChild(retryOption);
        }
    } else {
        console.error('找不到工装类型筛选下拉框');
    }
    
    // 加载年份选项
    const yearSelect = document.getElementById('summaryYearFilter');
    if (yearSelect) {
        const currentYear = new Date().getFullYear();
        yearSelect.innerHTML = '<option value="">所有年份</option>';
        for (let year = currentYear; year >= currentYear - 5; year--) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year + '年';
            yearSelect.appendChild(option);
        }
    }
}

// 加载汇总数据
function loadSummaryData() {
    console.log('加载汇总数据...');
    
    // 获取筛选条件
    const uniformTypeId = document.getElementById('summaryUniformTypeFilter')?.value || '';
    const yearFilter = document.getElementById('summaryYearFilter')?.value || '';
    const searchTerm = document.getElementById('summarySearch')?.value || '';
    
    // 构建URL参数
    const params = new URLSearchParams();
    if (uniformTypeId) params.append('uniform_type_id', uniformTypeId);
    if (yearFilter) params.append('year', yearFilter);
    if (searchTerm) params.append('search', searchTerm);
    
    const url = '/employee_uniform/uniform-summary' + (params.toString() ? '?' + params.toString() : '');
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('汇总数据:', data);
            
            if (data.success && Array.isArray(data.data)) {
                renderSummaryTable(data.data);
                calculateStatistics(data.data);
            } else {
                console.error('汇总数据格式错误:', data);
                showToast('加载汇总数据失败', 'error');
            }
        })
        .catch(error => {
            console.error('加载汇总数据失败:', error);
            showToast('加载汇总数据失败', 'error');
        });
}

// 渲染汇总表格
function renderSummaryTable(summaryData) {
    const tbody = document.getElementById('summaryTableBody');
    if (!tbody) {
        console.error('找不到汇总表格主体');
        return;
    }
    
    if (summaryData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">暂无汇总数据</td></tr>';
        return;
    }
    
    let html = '';
    summaryData.forEach(item => {
        let daysClass = '';
        let daysText = item.days_since_last_issue;
        
        if (item.days_since_last_issue > 365) {
            daysClass = 'text-danger';
            daysText += ' (超期)';
        } else if (item.days_since_last_issue > 180) {
            daysClass = 'text-warning';
            daysText += ' (即将超期)';
        }
        
        // 计算状态
        let statusBadge = '';
        let statusText = '';
        
        if (item.days_since_last_issue === -1) {
            statusBadge = 'bg-secondary';
            statusText = '未领取';
        } else if (item.days_since_last_issue > 365) {
            statusBadge = 'bg-danger';
            statusText = '超期';
        } else if (item.days_since_last_issue > 180) {
            statusBadge = 'bg-warning';
            statusText = '即将超期';
        } else {
            statusBadge = 'bg-success';
            statusText = '正常';
        }
        
        html += `
            <tr>
                <td><strong>${item.employee_id}</strong></td>
                <td>${item.employee_name}</td>
                <td>
                    <span class="badge bg-primary">${item.this_year_count} 套</span>
                </td>
                <td class="${daysClass}">${daysText} 天</td>
                <td>
                    <span class="badge ${statusBadge}">${statusText}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewEmployeeHistory('${item.employee_id}')">
                        <i class="bi bi-clock-history"></i> 历史记录
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 计算统计信息
function calculateStatistics(summaryData) {
    if (!summaryData || summaryData.length === 0) {
        return;
    }
    
    // 员工总数
    document.getElementById('totalEmployeesCount').textContent = summaryData.length;
    
    // 今年总发放套数
    const totalThisYear = summaryData.reduce((sum, item) => sum + item.this_year_count, 0);
    document.getElementById('totalThisYearCount').textContent = totalThisYear;
    
    // 超期未领人数（超过365天）
    const overdueCount = summaryData.filter(item => item.days_since_last_issue > 365).length;
    document.getElementById('overdueCount').textContent = overdueCount;
    
    // 平均领取间隔天数
    const validDays = summaryData
        .filter(item => item.days_since_last_issue > 0)
        .map(item => item.days_since_last_issue);
    
    if (validDays.length > 0) {
        const avgDays = Math.round(validDays.reduce((sum, days) => sum + days, 0) / validDays.length);
        document.getElementById('avgDaysBetweenIssuance').textContent = avgDays;
    } else {
        document.getElementById('avgDaysBetweenIssuance').textContent = '-';
    }
}

// 加载快速统计数据
function loadQuickStats() {
    console.log('加载快速统计数据...');
    
    Promise.all([
        fetch('/employee_uniform/employees').then(response => response.json()),
        fetch('/employee_uniform/uniform_types').then(response => response.json()),
        fetch('/employee_uniform/issuance_records').then(response => response.json())
    ])
    .then(([employeesData, uniformTypesData, recordsData]) => {
        if (employeesData.success) {
            employees = employeesData.data;
        }
        
        if (uniformTypesData.success) {
            uniformTypes = uniformTypesData.data;
        }
        
        if (recordsData.success) {
            uniformRecords = recordsData.data;
        }
        
        updateQuickStats();
    })
    .catch(error => {
        console.error('加载统计数据失败:', error);
    });
}

// 更新快速统计
function updateQuickStats() {
    const employeeCountElement = document.getElementById('quickEmployeeCount');
    if (employeeCountElement) {
        employeeCountElement.textContent = employees.length;
    }
    
    const uniformTypeCountElement = document.getElementById('quickUniformTypeCount');
    if (uniformTypeCountElement) {
        uniformTypeCountElement.textContent = uniformTypes.length;
    }
    
    const recordCountElement = document.getElementById('quickRecordCount');
    if (recordCountElement) {
        recordCountElement.textContent = uniformRecords.length;
    }
}

// 显示添加员工模态框
function showAddEmployeeModal() {
    console.log('显示添加员工模态框');
    
    const modal = new bootstrap.Modal(document.getElementById('addEmployeeModal'));
    
    // 重置表单
    document.getElementById('addEmployeeForm').reset();
    
    modal.show();
}

// 保存员工
function saveEmployee() {
    console.log('保存员工...');
    
    const employeeId = document.getElementById('employeeId').value.trim();
    const employeeName = document.getElementById('employeeName').value.trim();
    
    if (!employeeId || !employeeName) {
        showToast('请填写完整的员工信息', 'warning');
        return;
    }
    
    fetch('/employee_uniform/employees', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ employee_id: employeeId, name: employeeName })
    })
    .then(response => response.json())
    .then(data => {
        console.log('保存员工响应:', data);
        
        if (data.success) {
            showToast('员工添加成功', 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('addEmployeeModal'));
            modal.hide();
            
            // 重新加载员工列表
            loadEmployees();
        } else {
            showToast('员工添加失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('保存员工失败:', error);
        showToast('员工添加失败', 'error');
    });
}

// 显示添加工装类型模态框
function showAddUniformTypeModal() {
    console.log('显示添加工装类型模态框');
    
    const modal = new bootstrap.Modal(document.getElementById('addUniformTypeModal'));
    
    // 重置表单
    document.getElementById('addUniformTypeForm').reset();
    
    modal.show();
}

// 保存工装类型
function saveUniformType() {
    console.log('保存工装类型...');
    
    const typeName = document.getElementById('uniformTypeName').value.trim();
    const description = document.getElementById('uniformTypeDesc').value.trim();
    
    if (!typeName) {
        showToast('请输入工装类型名称', 'warning');
        return;
    }
    
    fetch('/employee_uniform/uniform_types', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ type_name: typeName, description: description })
    })
    .then(response => response.json())
    .then(data => {
        console.log('保存工装类型响应:', data);
        
        if (data.success) {
            showToast('工装类型添加成功', 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('addUniformTypeModal'));
            modal.hide();
            
            // 重新加载工装类型列表
            loadUniformTypes();
        } else {
            showToast('工装类型添加失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('保存工装类型失败:', error);
        showToast('工装类型添加失败', 'error');
    });
}

// 显示发放工装模态框
function showIssueUniformModal() {
    console.log('显示发放工装模态框');
    
    const modal = new bootstrap.Modal(document.getElementById('issueUniformModal'));
    
    // 重置表单
    document.getElementById('issueUniformForm').reset();
    
    // 加载员工和工装类型选项
    loadEmployeeSelectOptions();
    loadUniformTypeSelectOptions();
    
    // 设置默认日期为今天
    const today = new Date();
    const formattedDate = today.toISOString().split('T')[0];
    document.getElementById('issueDate').value = formattedDate;
    
    modal.show();
}

// 加载员工选择选项
function loadEmployeeSelectOptions() {
    const select = document.getElementById('issueEmployeeId');
    select.innerHTML = '<option value="">请选择员工</option>';
    
    employees.forEach(employee => {
        const option = document.createElement('option');
        option.value = employee.employee_id;
        option.textContent = `${employee.employee_id} - ${employee.name}`;
        select.appendChild(option);
    });
}

// 加载工装类型选择选项
function loadUniformTypeSelectOptions() {
    const select = document.getElementById('issueUniformTypeId');
    select.innerHTML = '<option value="">请选择工装类型</option>';
    
    uniformTypes.forEach(uniformType => {
        const option = document.createElement('option');
        option.value = uniformType.id;
        option.textContent = uniformType.name;
        select.appendChild(option);
    });
}

// 发放工装
function issueUniform() {
    console.log('发放工装...');
    
    const employeeId = document.getElementById('issueEmployeeId').value;
    const uniformTypeId = document.getElementById('issueUniformTypeId').value;
    const issueDate = document.getElementById('issueDate').value;
    
    console.log('发放参数:', { employeeId, uniformTypeId, issueDate });
    
    if (!employeeId || !uniformTypeId) {
        showToast('请选择员工和工装类型', 'warning');
        return;
    }
    
    // 显示加载状态
    const confirmBtn = document.getElementById('confirmIssueBtn');
    const originalText = confirmBtn.textContent;
    confirmBtn.textContent = '发放中...';
    confirmBtn.disabled = true;
    
    fetch('/employee_uniform/issuance_records', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            employee_id: employeeId, 
            uniform_type_id: uniformTypeId,  // 使用正确的字段名
            issue_date: issueDate 
        })
    })
    .then(response => {
        console.log('响应状态:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('发放工装响应:', data);
        
        // 恢复按钮状态
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
        
        if (data.success) {
            showToast('工装发放记录添加成功', 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('issueUniformModal'));
            if (modal) {
                modal.hide();
            }
            
            // 重新加载数据
            loadRecords();
            loadSummaryData();
            loadEmployees(); // 刷新员工统计
        } else {
            showToast('工装发放记录添加失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('发放工装失败:', error);
        
        // 恢复按钮状态
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
        
        // 显示更详细的错误信息
        let errorMessage = '工装发放记录添加失败';
        if (error.message) {
            if (error.message.includes('timeout')) {
                errorMessage = '请求超时，请检查网络连接';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = '无法连接到服务器，请检查服务器状态';
            } else {
                errorMessage = `发放失败: ${error.message}`;
            }
        }
        
        showToast(errorMessage, 'error');
    });
}

// 显示批量添加员工模态框
function showBatchAddEmployeeModal() {
    console.log('显示批量添加员工模态框');
    
    try {
        const modal = new bootstrap.Modal(document.getElementById('batchAddEmployeeModal'));
        
        // 重置表单
        const batchEmployeeData = document.getElementById('batchEmployeeData');
        const batchPreviewArea = document.getElementById('batchPreviewArea');
        
        if (batchEmployeeData) batchEmployeeData.value = '';
        if (batchPreviewArea) batchPreviewArea.style.display = 'none';
        
        modal.show();
        console.log('批量添加员工模态框已显示');
    } catch (error) {
        console.error('显示批量添加员工模态框失败:', error);
        showToast('无法打开批量添加员工窗口', 'error');
    }
}

// 显示批量发放工装模态框
function showBatchIssueUniformModal() {
    console.log('显示批量发放工装模态框');
    
    const modal = new bootstrap.Modal(document.getElementById('batchIssueUniformModal'));
    
    // 重置表单
    document.getElementById('batchUniformTypeId').innerHTML = '<option value="">请选择工装类型</option>';
    document.getElementById('batchIssueDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('batchIssueCount').value = 1;
    document.getElementById('batchIssuePreview').style.display = 'none';
    
    // 加载工装类型选项
    loadBatchUniformTypeOptions();
    
    // 加载员工列表
    loadBatchEmployeeList();
    
    modal.show();
}

// 加载批量工装类型选项
function loadBatchUniformTypeOptions() {
    const select = document.getElementById('batchUniformTypeId');
    select.innerHTML = '<option value="">请选择工装类型</option>';
    
    uniformTypes.forEach(uniformType => {
        const option = document.createElement('option');
        option.value = uniformType.id;
        option.textContent = uniformType.name;
        select.appendChild(option);
    });
}

// 加载批量员工列表
function loadBatchEmployeeList() {
    const tbody = document.getElementById('batchEmployeeTableBody');
    
    if (employees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">暂无员工数据</td></tr>';
        return;
    }
    
    let html = '';
    employees.forEach(employee => {
        html += `
            <tr>
                <td>
                    <input type="checkbox" class="form-check-input employee-checkbox" value="${employee.employee_id}">
                </td>
                <td>${employee.employee_id}</td>
                <td>${employee.name}</td>
                <td>${employee.department || '-'}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 显示删除确认对话框
function showDeleteConfirm(type, id, name) {
    console.log('显示删除确认:', type, id, name);
    
    window.currentDeleteType = type;
    window.currentDeleteId = id;
    
    document.getElementById('deleteConfirmMessage').textContent = `确定要删除 ${name} 吗？此操作不可撤销。`;
    
    const modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
    modal.show();
}

// 确认删除
function confirmDelete() {
    const type = window.currentDeleteType;
    const id = window.currentDeleteId;
    
    if (!type || !id) {
        showToast('删除参数错误', 'error');
        return;
    }
    
    let url, message;
    
    if (type === 'employee') {
        url = `/employee_uniform/employees/${id}`;
        message = '员工删除成功';
    } else if (type === 'uniform_type') {
        url = `/employee_uniform/uniform_types/${id}`;
        message = '工装类型删除成功';
    } else if (type === 'record') {
        url = `/employee_uniform/issuance_records/${id}`;
        message = '领取记录删除成功';
    }
    
    fetch(url, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        console.log('删除响应:', data);
        
        if (data.success) {
            showToast(message, 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('confirmDeleteModal'));
            modal.hide();
            
            // 重新加载相应列表
            if (type === 'employee') {
                loadEmployees();
                loadRecords();
                loadSummaryData();
            } else if (type === 'record') {
                loadRecords();
                loadSummaryData();
            } else if (type === 'uniform_type') {
                loadUniformTypes();
            }
        } else {
            showToast('删除失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('删除失败:', error);
        showToast('删除失败', 'error');
    });
}

// 编辑员工
function editEmployee(employeeId, name) {
    console.log('编辑员工:', employeeId, name);
    
    document.getElementById('updateEmployeeId').value = employeeId;
    document.getElementById('updateEmployeeIdDisplay').value = employeeId;
    document.getElementById('updateEmployeeName').value = name;
    
    const modal = new bootstrap.Modal(document.getElementById('updateEmployeeModal'));
    modal.show();
}

// 更新员工
function updateEmployee() {
    const employeeId = document.getElementById('updateEmployeeId').value;
    const name = document.getElementById('updateEmployeeName').value.trim();
    
    if (!name) {
        showToast('请输入员工姓名', 'warning');
        return;
    }
    
    fetch(`/employee_uniform/employees/${employeeId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: name })
    })
    .then(response => response.json())
    .then(data => {
        console.log('更新员工响应:', data);
        
        if (data.success) {
            showToast('员工信息更新成功', 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('updateEmployeeModal'));
            modal.hide();
            
            // 重新加载员工列表
            loadEmployees();
        } else {
            showToast('员工信息更新失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('更新员工失败:', error);
        showToast('员工信息更新失败', 'error');
    });
}

// 显示提示消息
function showToast(message, type = 'info') {
    console.log('显示提示:', message, type);
    
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        console.error('找不到toast容器');
        return;
    }
    
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = `toast fade show align-items-center text-white ${getToastClass(type)}`;
    toast.role = 'alert';
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // 添加到容器
    toastContainer.appendChild(toast);
    
    // 自动关闭
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

// 获取toast样式类
function getToastClass(type) {
    switch (type) {
        case 'success':
            return 'bg-success';
        case 'error':
            return 'bg-danger';
        case 'warning':
            return 'bg-warning';
        case 'info':
        default:
            return 'bg-info';
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 批量发放工装
function batchIssueUniform() {
    console.log('批量发放工装...');
    
    const uniformTypeId = document.getElementById('batchUniformTypeId').value;
    const issueDate = document.getElementById('batchIssueDate').value;
    const issueCount = parseInt(document.getElementById('batchIssueCount').value);
    const checkedBoxes = document.querySelectorAll('#batchEmployeeTableBody input[type="checkbox"]:checked');
    
    console.log('批量发放参数:', { uniformTypeId, issueDate, issueCount, selectedCount: checkedBoxes.length });
    
    if (!uniformTypeId) {
        showToast('请选择工装类型', 'warning');
        return;
    }
    
    if (checkedBoxes.length === 0) {
        showToast('请选择至少一位员工', 'warning');
        return;
    }
    
    if (!issueDate) {
        showToast('请选择发放日期', 'warning');
        return;
    }
    
    if (issueCount < 1) {
        showToast('发放数量必须大于0', 'warning');
        return;
    }
    
    const employeeIds = Array.from(checkedBoxes).map(cb => cb.value);
    
    // 显示加载状态
    const confirmBtn = document.getElementById('confirmBatchIssueBtn');
    const originalText = confirmBtn.textContent;
    confirmBtn.textContent = '发放中...';
    confirmBtn.disabled = true;
    
    fetch('/employee_uniform/issuance_records/batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            uniform_type_id: uniformTypeId,
            employee_ids: employeeIds,
            issue_date: issueDate,
            quantity: issueCount
        })
    })
    .then(response => {
        console.log('批量发放响应状态:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('批量发放响应:', data);
        
        // 恢复按钮状态
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
        
        if (data.success) {
            showToast(data.message, 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('batchIssueUniformModal'));
            if (modal) {
                modal.hide();
            }
            
            // 重新加载数据
            loadRecords();
            loadSummaryData();
            loadEmployees(); // 刷新员工统计
        } else {
            showToast('批量发放失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('批量发放失败:', error);
        
        // 恢复按钮状态
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
        
        // 显示更详细的错误信息
        let errorMessage = '批量发放失败';
        if (error.message) {
            if (error.message.includes('timeout')) {
                errorMessage = '请求超时，请检查网络连接';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = '无法连接到服务器，请检查服务器状态';
            } else {
                errorMessage = `批量发放失败: ${error.message}`;
            }
        }
        
        showToast(errorMessage, 'error');
    });
}

// 更新批量发放预览
function updateBatchIssuePreview() {
    const uniformTypeId = document.getElementById('batchUniformTypeId').value;
    const uniformTypeText = document.getElementById('batchUniformTypeId').selectedOptions[0]?.textContent || '未选择';
    const issueDate = document.getElementById('batchIssueDate').value;
    const issueCount = document.getElementById('batchIssueCount').value;
    const checkedBoxes = document.querySelectorAll('#batchEmployeeTableBody input[type="checkbox"]:checked');
    
    if (checkedBoxes.length === 0 || !uniformTypeId) {
        document.getElementById('batchIssuePreview').style.display = 'none';
        return;
    }
    
    const selectedEmployees = Array.from(checkedBoxes).map(cb => {
        const row = cb.closest('tr');
        const employeeId = row.cells[1].textContent;
        const employeeName = row.cells[2].textContent;
        return `${employeeId} (${employeeName})`;
    }).join(', ');
    
    document.getElementById('previewUniformType').textContent = uniformTypeText;
    document.getElementById('previewIssueDate').textContent = issueDate;
    document.getElementById('previewIssueCount').textContent = issueCount;
    document.getElementById('previewSelectedEmployees').textContent = selectedEmployees;
    document.getElementById('batchIssuePreview').style.display = 'block';
}

// 在主DOMContentLoaded事件中绑定批量发放事件
document.addEventListener('DOMContentLoaded', function() {
    console.log('绑定批量发放事件...');
    
    // 确认批量发放按钮 - 多种绑定方式确保生效
    const confirmBatchIssueBtn = document.getElementById('confirmBatchIssueBtn');
    if (confirmBatchIssueBtn) {
        // 方式1: 直接onclick
        confirmBatchIssueBtn.onclick = batchIssueUniform;
        // 方式2: addEventListener（备用）
        confirmBatchIssueBtn.addEventListener('click', batchIssueUniform);
        console.log('确认批量发放按钮事件绑定成功');
    } else {
        console.error('找不到确认批量发放按钮');
    }
    
    // 全选/取消全选员工
    const selectAllEmployees = document.getElementById('selectAllEmployees');
    if (selectAllEmployees) {
        selectAllEmployees.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('#batchEmployeeTableBody input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = this.checked);
            updateBatchIssuePreview();
        });
    }
    
    // 工装类型和日期变化事件
    const batchUniformTypeId = document.getElementById('batchUniformTypeId');
    if (batchUniformTypeId) {
        batchUniformTypeId.addEventListener('change', updateBatchIssuePreview);
    }
    
    const batchIssueDate = document.getElementById('batchIssueDate');
    if (batchIssueDate) {
        batchIssueDate.addEventListener('change', updateBatchIssuePreview);
    }
    
    const batchIssueCount = document.getElementById('batchIssueCount');
    if (batchIssueCount) {
        batchIssueCount.addEventListener('input', updateBatchIssuePreview);
    }
    
    // 动态添加的员工复选框变化事件
    document.addEventListener('change', function(e) {
        if (e.target && e.target.type === 'checkbox' && e.target.classList.contains('employee-checkbox')) {
            updateBatchIssuePreview();
        }
    });
});

// 查看员工历史记录
function viewEmployeeHistory(employeeId) {
    console.log('查看员工历史记录:', employeeId);
    
    fetch(`/employee_uniform/employees/${employeeId}/uniform_history`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let historyHtml = `
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>工装类型</th>
                                    <th>领取日期</th>
                                    <th>记录时间</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                if (data.records && data.records.length > 0) {
                    data.records.forEach(record => {
                        historyHtml += `
                            <tr>
                                <td>${record.uniform_type_name || '-'}</td>
                                <td>${record.issue_date}</td>
                                <td>${record.recorded_at || '-'}</td>
                            </tr>
                        `;
                    });
                } else {
                    historyHtml += `
                        <tr>
                            <td colspan="3" class="text-center text-muted">暂无领取记录</td>
                        </tr>
                    `;
                }
                
                historyHtml += `
                        </tbody>
                    </table>
                </div>
                `;
                
                // 显示模态框
                const modalHtml = `
                    <div class="modal fade" id="employeeHistoryModal" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header bg-info text-white">
                                    <h5 class="modal-title">
                                        <i class="bi bi-clock-history"></i> 
                                        员工领取历史 - ${employeeId}
                                    </h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    ${historyHtml}
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // 如果模态框已存在，先移除
                const existingModal = document.getElementById('employeeHistoryModal');
                if (existingModal) {
                    existingModal.remove();
                }
                
                // 添加新模态框到页面
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('employeeHistoryModal'));
                modal.show();
                
                // 模态框关闭后移除DOM
                document.getElementById('employeeHistoryModal').addEventListener('hidden.bs.modal', function() {
                    this.remove();
                });
                
            } else {
                showToast('获取员工历史记录失败', 'error');
            }
        })
        .catch(error => {
            console.error('获取员工历史记录失败:', error);
            showToast('获取员工历史记录失败', 'error');
        });
}

// 批量添加员工相关函数
function previewBatchEmployees() {
    const data = document.getElementById('batchEmployeeData').value.trim();
    if (!data) {
        showToast('请输入员工数据', 'warning');
        return;
    }
    
    const lines = data.split('\r\n').filter(line => line.trim());
    const previewData = [];
    
    lines.forEach((line, index) => {
        // 支持逗号或空格分隔，优先处理逗号
        let parts;
        if (line.includes(',')) {
            parts = line.split(',').map(part => part.trim()).filter(part => part);
        } else {
            parts = line.split(/\s+/).map(part => part.trim()).filter(part => part);
        }
        
        if (parts.length >= 2) {
            const employeeId = parts[0];
            const name = parts[1];
            
            // 验证工号和姓名
            if (!employeeId || !name) {
                previewData.push({
                    index: index + 1,
                    employeeId: employeeId || '-',
                    name: name || '-',
                    status: '格式错误'
                });
            } else {
                // 检查员工是否已存在
                const exists = employees.some(emp => emp.employee_id === employeeId);
                previewData.push({
                    index: index + 1,
                    employeeId: employeeId,
                    name: name,
                    status: exists ? '已存在' : '新增'
                });
            }
        } else {
            previewData.push({
                index: index + 1,
                employeeId: '-',
                name: '-',
                status: '格式错误'
            });
        }
    });
    
    // 渲染预览表格
    const tbody = document.querySelector('#batchPreviewArea tbody');
    if (tbody) {
        let html = '';
        previewData.forEach(item => {
            let statusClass = 'bg-secondary';
            if (item.status === '已存在') {
                statusClass = 'bg-warning';
            } else if (item.status === '新增') {
                statusClass = 'bg-success';
            } else if (item.status === '格式错误') {
                statusClass = 'bg-danger';
            }
            
            html += `
                <tr>
                    <td>${item.index}</td>
                    <td>${item.employeeId}</td>
                    <td>${item.name}</td>
                    <td><span class="badge ${statusClass}">${item.status}</span></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }
    
    document.getElementById('batchPreviewArea').style.display = 'block';
}

function saveBatchEmployees() {
    const data = document.getElementById('batchEmployeeData').value.trim();
    if (!data) {
        showToast('请输入员工数据', 'warning');
        return;
    }
    
    const lines = data.split('\r\n').filter(line => line.trim());
    const employeesToAdd = [];
    let hasErrors = false;
    
    lines.forEach((line, index) => {
        // 支持逗号或空格分隔，优先处理逗号
        let parts;
        if (line.includes(',')) {
            parts = line.split(',').map(part => part.trim()).filter(part => part);
        } else {
            parts = line.split(/\s+/).map(part => part.trim()).filter(part => part);
        }
        
        if (parts.length >= 2) {
            const employeeId = parts[0].trim();
            const name = parts[1].trim();
            
            if (!employeeId || !name) {
                hasErrors = true;
                console.error(`第 ${index + 1} 行格式错误: ${line}`);
                return;
            }
            
            // 检查是否重复
            const duplicate = employeesToAdd.some(emp => emp.employee_id === employeeId);
            if (duplicate) {
                console.warn(`重复的工号: ${employeeId}`);
                return;
            }
            
            // 检查是否已存在
            const exists = employees.some(emp => emp.employee_id === employeeId);
            if (!exists) {
                employeesToAdd.push({
                    employee_id: employeeId,
                    name: name
                });
            }
        } else {
            hasErrors = true;
            console.error(`第 ${index + 1} 行格式错误: ${line}`);
        }
    });
    
    if (hasErrors) {
        showToast('数据格式有误，请检查后重试', 'error');
        return;
    }
    
    if (employeesToAdd.length === 0) {
        showToast('没有可添加的新员工', 'warning');
        return;
    }
    
    // 批量添加员工
    fetch('/employee_uniform/employees/batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            employees: employeesToAdd
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const successCount = data.success_count || 0;
            const errorCount = data.error_count || 0;
            
            showToast(`批量添加完成：成功 ${successCount} 人，失败 ${errorCount} 人`, successCount > 0 ? 'success' : 'warning');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('batchAddEmployeeModal'));
            if (modal) {
                modal.hide();
            }
            
            // 重新加载员工列表
            loadEmployees();
        } else {
            showToast('批量添加失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('批量添加员工失败:', error);
        showToast('批量添加员工失败', 'error');
    });
}

// 清空批量数据
function clearBatchData() {
    document.getElementById('batchEmployeeData').value = '';
    document.getElementById('batchPreviewArea').style.display = 'none';
}

// 全局函数，供HTML中的onclick调用
window.editEmployee = editEmployee;
window.showDeleteConfirm = showDeleteConfirm;
window.updateEmployee = updateEmployee;
window.issueUniform = issueUniform;
window.batchIssueUniform = batchIssueUniform;
window.viewEmployeeHistory = viewEmployeeHistory;
window.previewBatchEmployees = previewBatchEmployees;
window.saveBatchEmployees = saveBatchEmployees;
window.clearBatchData = clearBatchData;
window.confirmDelete = confirmDelete;
window.updateBatchIssuePreview = updateBatchIssuePreview;