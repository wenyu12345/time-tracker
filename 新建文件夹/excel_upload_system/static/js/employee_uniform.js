/**
 * 员工工装管理前端脚本
 */

// 全局配置
const API_BASE_URL = '/employee_uniform';

// 初始化页面
function initUniformManagement() {
    console.log('初始化员工工装管理系统...');
    
    // 加载页面组件
    loadEmployeesTable();
    loadUniformTypes();
    initEventListeners();
    
    // 监听选项卡切换事件
    const tabTriggerList = [].slice.call(document.querySelectorAll('#uniformTabs button'));
    tabTriggerList.forEach(function (tabTrigger) {
        tabTrigger.addEventListener('shown.bs.tab', function (event) {
            // 如果切换到汇总选项卡，则加载汇总数据
            if (event.target.id === 'summary-tab') {
                loadUniformSummary();
            }
        });
    });
}

// 加载员工列表表格
async function loadEmployeesTable() {
    try {
        const response = await fetch(`${API_BASE_URL}/employees`);
        const data = await response.json();
        
        if (data.success) {
            renderEmployeesTable(data.data);
        } else {
            showError('加载员工列表失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 渲染员工表格
function renderEmployeesTable(employees) {
    const tableBody = document.getElementById('employees-table-body');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    if (employees.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">暂无员工数据</td>
            </tr>
        `;
        return;
    }
    
    employees.forEach(employee => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${employee.employee_id}</td>
            <td>${employee.name}</td>
            <td>${formatDate(employee.created_at)}</td>
            <td>
                <button class="btn btn-info btn-sm view-uniform-history" data-id="${employee.employee_id}">查看工装历史</button>
                <button class="btn btn-primary btn-sm issue-uniform" data-id="${employee.employee_id}" data-name="${employee.name}">发放工装</button>
            </td>
            <td>
                <button class="btn btn-danger btn-sm delete-employee" data-id="${employee.employee_id}">删除</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
    
    // 绑定事件监听器
    bindTableEventListeners();
}

// 加载工装类型
async function loadUniformTypes() {
    try {
        const response = await fetch(`${API_BASE_URL}/uniform_types`);
        const data = await response.json();
        
        if (data.success) {
            renderUniformTypesSelect(data.data);
            renderUniformTypesList(data.data);
        } else {
            showError('加载工装类型失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 渲染工装类型下拉选择框
function renderUniformTypesSelect(types) {
    const select = document.getElementById('uniform-type-select');
    if (!select) return;
    
    select.innerHTML = '';
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '请选择工装类型';
    defaultOption.selected = true;
    defaultOption.disabled = true;
    select.appendChild(defaultOption);
    
    types.forEach(type => {
        const option = document.createElement('option');
        option.value = type.id;
        option.textContent = type.name;
        select.appendChild(option);
    });
}

// 渲染工装类型列表
function renderUniformTypesList(types) {
    const listContainer = document.getElementById('uniform-types-list');
    if (!listContainer) return;
    
    listContainer.innerHTML = '';
    
    if (types.length === 0) {
        listContainer.innerHTML = '<p class="text-center">暂无工装类型</p>';
        return;
    }
    
    types.forEach(type => {
        const typeCard = document.createElement('div');
        typeCard.className = 'uniform-type-card mb-3 p-3 border rounded';
        typeCard.innerHTML = `
            <div class="row">
                <div class="col-md-8">
                    <h5>${type.name}</h5>
                    <p class="text-muted">${type.description || '无描述'}</p>
                </div>
                <div class="col-md-4 text-right">
                    <small class="text-muted">ID: ${type.id}</small>
                    <button class="btn btn-danger btn-sm ml-2 delete-uniform-type" data-id="${type.id}">删除</button>
                </div>
            </div>
        `;
        listContainer.appendChild(typeCard);
    });
    
    // 绑定删除工装类型事件
    bindDeleteUniformTypeEvents();
}

// 初始化事件监听器
function initEventListeners() {
    // 添加员工按钮
    document.getElementById('add-employee-btn')?.addEventListener('click', showAddEmployeeModal);
    
    // 提交添加员工表单
    document.getElementById('add-employee-form')?.addEventListener('submit', handleAddEmployeeSubmit);
    
    // 提交发放工装表单
    document.getElementById('issue-uniform-form')?.addEventListener('submit', handleIssueUniformSubmit);
    
    // 添加工装类型按钮
    document.getElementById('add-uniform-type-btn')?.addEventListener('click', showAddUniformTypeModal);
    
    // 提交添加工装类型表单
    document.getElementById('add-uniform-type-form')?.addEventListener('submit', handleAddUniformTypeSubmit);
    
    // 关闭模态框时重置表单
    const modals = ['add-employee-modal', 'issue-uniform-modal', 'add-uniform-type-modal', 'uniform-history-modal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                const form = modal.querySelector('form');
                if (form) {
                    form.reset();
                }
            });
        }
    });
}

// 加载工装汇总信息
async function loadUniformSummary() {
    const summaryBody = document.getElementById('uniform-summary-body');
    
    // 显示加载状态
    if (summaryBody) {
        summaryBody.innerHTML = '<tr><td colspan="4" class="text-center">加载中...</td></tr>';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/uniform-summary`);
        const data = await response.json();
        
        if (data.success) {
            renderUniformSummary(data.data);
        } else {
            if (summaryBody) {
                summaryBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">${data.error || '获取汇总信息失败'}</td></tr>`;
            }
        }
    } catch (error) {
        console.error('获取汇总信息出错:', error);
        if (summaryBody) {
            summaryBody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">获取汇总信息失败</td></tr>';
        }
    }
}

// 渲染工装汇总信息
function renderUniformSummary(summaryData) {
    const summaryBody = document.getElementById('uniform-summary-body');
    if (!summaryBody) return;
    
    if (!summaryData || summaryData.length === 0) {
        summaryBody.innerHTML = '<tr><td colspan="4" class="text-center">暂无汇总数据</td></tr>';
        return;
    }
    
    // 清空表格内容
    summaryBody.innerHTML = '';
    
    // 添加汇总数据行
    summaryData.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.employee_id || ''}</td>
            <td>${item.employee_name || ''}</td>
            <td>${item.this_year_count || 0}</td>
            <td>${item.days_since_last_issue || '-'}</td>
        `;
        summaryBody.appendChild(row);
    });
}

// 绑定删除工装记录事件
function bindDeleteUniformRecordEvents() {
    document.querySelectorAll('.delete-uniform-record').forEach(btn => {
        btn.addEventListener('click', function() {
            const recordId = this.getAttribute('data-id');
            confirmDeleteUniformRecord(recordId);
        });
    });
}

// 绑定删除工装类型事件
function bindDeleteUniformTypeEvents() {
    document.querySelectorAll('.delete-uniform-type').forEach(btn => {
        btn.addEventListener('click', function() {
            const typeId = this.getAttribute('data-id');
            confirmDeleteUniformType(typeId);
        });
    });
}

// 绑定表格事件监听器
function bindTableEventListeners() {
    // 查看工装历史按钮
    document.querySelectorAll('.view-uniform-history').forEach(btn => {
        btn.addEventListener('click', function() {
            const employeeId = this.getAttribute('data-id');
            showUniformHistory(employeeId);
        });
    });
    
    // 发放工装按钮
    document.querySelectorAll('.issue-uniform').forEach(btn => {
        btn.addEventListener('click', function() {
            const employeeId = this.getAttribute('data-id');
            const employeeName = this.getAttribute('data-name');
            showIssueUniformModal(employeeId, employeeName);
        });
    });
    
    // 删除员工按钮
    document.querySelectorAll('.delete-employee').forEach(btn => {
        btn.addEventListener('click', function() {
            const employeeId = this.getAttribute('data-id');
            confirmDeleteEmployee(employeeId);
        });
    });
}

// 显示添加员工模态框
function showAddEmployeeModal() {
    const modal = new bootstrap.Modal(document.getElementById('add-employee-modal'));
    modal.show();
}

// 处理添加员工表单提交
async function handleAddEmployeeSubmit(event) {
    event.preventDefault();
    
    const name = document.getElementById('employee-name').value.trim();
    const employeeId = document.getElementById('employee-id').value.trim();
    
    // 简单验证
    if (!name) {
        showError('请输入员工姓名');
        return;
    }
    if (!employeeId) {
        showError('请输入员工工号');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/employees`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, employee_id: employeeId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('员工添加成功');
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('add-employee-modal')).hide();
            // 重新加载员工列表
            loadEmployeesTable();
        } else {
            showError('添加失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 显示发放工装模态框
function showIssueUniformModal(employeeId, employeeName) {
    // 设置员工信息
    document.getElementById('issue-employee-info').textContent = `员工: ${employeeName} (${employeeId})`;
    document.getElementById('issue-employee-id').value = employeeId;
    
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('issue-date').value = today;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('issue-uniform-modal'));
    modal.show();
}

// 处理发放工装表单提交
async function handleIssueUniformSubmit(event) {
    event.preventDefault();
    
    const employeeId = document.getElementById('issue-employee-id').value;
    const uniformTypeId = document.getElementById('uniform-type-select').value;
    const issueDate = document.getElementById('issue-date').value;
    
    // 验证
    if (!employeeId) {
        showError('员工信息错误');
        return;
    }
    if (!uniformTypeId) {
        showError('请选择工装类型');
        return;
    }
    if (!issueDate) {
        showError('请选择发放日期');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/records`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                employee_id: employeeId, 
                uniform_type_id: parseInt(uniformTypeId), 
                issue_date: issueDate + 'T00:00:00.000Z'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('工装发放记录添加成功');
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('issue-uniform-modal')).hide();
        } else {
            showError('添加失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 显示添加工装类型模态框
function showAddUniformTypeModal() {
    const modal = new bootstrap.Modal(document.getElementById('add-uniform-type-modal'));
    modal.show();
}

// 处理添加工装类型表单提交
async function handleAddUniformTypeSubmit(event) {
    event.preventDefault();
    
    const name = document.getElementById('uniform-type-name').value.trim();
    const description = document.getElementById('uniform-type-description').value.trim();
    
    // 验证
    if (!name) {
        showError('请输入工装类型名称');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/uniform_types`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('工装类型添加成功');
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('add-uniform-type-modal')).hide();
            // 重新加载工装类型
            loadUniformTypes();
        } else {
            showError('添加失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 确认删除员工
function confirmDeleteEmployee(employeeId) {
    if (confirm('确定要删除该员工吗？删除后将无法恢复。')) {
        deleteEmployee(employeeId);
    }
}

// 删除员工
async function deleteEmployee(employeeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/employees/${employeeId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message || '员工删除成功');
            // 重新加载员工列表
            loadEmployeesTable();
        } else {
            showError('删除失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 确认删除工装记录
function confirmDeleteUniformRecord(recordId) {
    if (confirm('确定要删除该工装领取记录吗？删除后将无法恢复。')) {
        deleteUniformRecord(recordId);
    }
}

// 删除工装记录
async function deleteUniformRecord(recordId) {
    try {
        const response = await fetch(`${API_BASE_URL}/issuance_records/${recordId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message || '工装领取记录删除成功');
            // 重新加载当前员工的工装历史
            const employeeId = document.getElementById('history-employee-id').textContent;
            if (employeeId) {
                showUniformHistory(employeeId);
            }
        } else {
            showError('删除失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 确认删除工装类型
function confirmDeleteUniformType(typeId) {
    if (confirm('确定要删除该工装类型吗？如果有相关的工装领取记录，将无法删除。')) {
        deleteUniformType(typeId);
    }
}

// 删除工装类型
async function deleteUniformType(typeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/uniform_types/${typeId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message || '工装类型删除成功');
            // 重新加载工装类型列表
            loadUniformTypes();
        } else {
            showError('删除失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 显示员工工装历史
async function showUniformHistory(employeeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/employees/${employeeId}/uniform_history`);
        const records = await response.json();
        
        // 由于后端接口简化，我们需要获取员工信息来显示
        const employeeResponse = await fetch(`${API_BASE_URL}/employees/${employeeId}`);
        const employeeData = await employeeResponse.json();
        
        if (employeeData.success) {
            // 构造前端所需的数据格式
            const data = {
                employee: employeeData.data,
                records: records || []
            };
            
            renderUniformHistory(data);
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('uniform-history-modal'));
            modal.show();
        } else {
            showError('加载员工信息失败: ' + (employeeData.error || '未知错误'));
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
    }
}

// 渲染工装历史
function renderUniformHistory(data) {
    // 设置员工信息
    document.getElementById('history-employee-name').textContent = data.employee.name;
    document.getElementById('history-employee-id').textContent = data.employee.employee_id;
    
    // 渲染记录列表
    const historyList = document.getElementById('uniform-history-list');
    if (!historyList) return;
    
    historyList.innerHTML = '';
    
    if (data.records.length === 0) {
        historyList.innerHTML = '<p class="text-center">暂无工装领取记录</p>';
        return;
    }
    
    data.records.forEach(record => {
        // 适配简化后的后端数据格式
        const uniformTypeName = record.uniform_type_name || '未知类型';
        
        const recordItem = document.createElement('div');
        recordItem.className = 'history-record mb-3 p-3 border rounded';
        recordItem.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>工装类型:</strong> ${uniformTypeName}
                </div>
                <div class="col-md-6 text-right">
                    <strong>发放日期:</strong> ${formatDate(record.issue_date)}
                    <button class="btn btn-danger btn-sm ml-2 delete-uniform-record" data-id="${record.id}">删除</button>
                </div>
            </div>
        `;
        historyList.appendChild(recordItem);
    });
    
    // 绑定删除工装记录事件
    bindDeleteUniformRecordEvents();
}

// 辅助函数: 格式化日期
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

// 显示成功消息
function showSuccess(message) {
    const toastEl = document.getElementById('success-toast');
    if (toastEl) {
        const toastBody = toastEl.querySelector('.toast-body');
        if (toastBody) {
            toastBody.textContent = message;
        }
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    } else {
        alert(message);
    }
}

// 显示错误消息
function showError(message) {
    const toastEl = document.getElementById('error-toast');
    if (toastEl) {
        const toastBody = toastEl.querySelector('.toast-body');
        if (toastBody) {
            toastBody.textContent = message;
        }
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    } else {
        alert(message);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查页面是否包含员工工装管理相关元素
    if (document.getElementById('employee-uniform-container')) {
        initUniformManagement();
    }
});