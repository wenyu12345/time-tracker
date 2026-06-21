// 管理系统JavaScript

// 全局变量
let currentAdmin = null;
let currentPage = 'dashboard';

// DOM元素
const loginPage = document.getElementById('login-page');
const adminContent = document.querySelector('.admin-content');
const adminUsername = document.getElementById('admin-username');
const logoutBtn = document.getElementById('logout-btn');
const adminLoginForm = document.getElementById('admin-login-form');
const navLinks = document.querySelectorAll('.nav-link');
const pages = document.querySelectorAll('.page');
const modal = document.getElementById('admin-modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const closeBtn = document.querySelector('.close-btn');

// 初始化
function initAdminSystem() {
    // 检查本地存储中是否有管理员信息
    const savedAdmin = localStorage.getItem('admin');
    if (savedAdmin) {
        currentAdmin = JSON.parse(savedAdmin);
        showAdminContent();
        loadPage(currentPage);
    } else {
        showLoginPage();
    }
    
    // 绑定事件
    bindEvents();
}

// 绑定事件
function bindEvents() {
    // 登录表单提交
    adminLoginForm.addEventListener('submit', handleLogin);
    
    // 退出登录
    logoutBtn.addEventListener('click', handleLogout);
    
    // 导航链接点击
    navLinks.forEach(link => {
        link.addEventListener('click', handleNavClick);
    });
    
    // 模态框关闭
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // 窗口点击关闭模态框
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // 添加用户按钮
    document.getElementById('add-user-btn')?.addEventListener('click', showAddUserModal);
    
    // 添加角色按钮
    document.getElementById('add-role-btn')?.addEventListener('click', showAddRoleModal);
    
    // 添加权限按钮
    document.getElementById('add-permission-btn')?.addEventListener('click', showAddPermissionModal);
    
    // 添加排班按钮
        document.getElementById('add-schedule-btn')?.addEventListener('click', showAddScheduleModal);
        
        // 批量排班按钮
        document.getElementById('batch-schedule-btn')?.addEventListener('click', showBatchScheduleModal);
        
        // 批量安排调休按钮
        document.getElementById('arrange-leave-btn')?.addEventListener('click', showArrangeLeaveModal);
        
        // 删除过期排班按钮
        document.getElementById('delete-expired-schedules-btn')?.addEventListener('click', handleDeleteExpiredSchedules);
        
        // 一键生成工时记录按钮
        document.getElementById('schedules-to-time-records-btn')?.addEventListener('click', handleSchedulesToTimeRecords);
    
    // 重置工资配置按钮
    document.getElementById('reset-salary-config-btn')?.addEventListener('click', handleResetSalaryConfig);
    
    // 计算工资按钮
    document.getElementById('calculate-salary-btn')?.addEventListener('click', handleCalculateSalary);
    
    // 检查重复记录按钮
    document.getElementById('check-duplicate-records-btn')?.addEventListener('click', handleCheckDuplicateRecords);
    
    // Excel导入工时记录按钮
    document.getElementById('import-excel-btn')?.addEventListener('click', showImportExcelModal);
    
    // 创建备份按钮
    document.getElementById('create-backup-btn')?.addEventListener('click', handleCreateBackup);
    
    // 自动备份按钮
    document.getElementById('auto-backup-btn')?.addEventListener('click', handleAutoBackup);
    
    // 搜索用户按钮
    document.getElementById('search-user-btn')?.addEventListener('click', handleSearchUser);
    
    // 搜索记录按钮
    document.getElementById('search-record-btn')?.addEventListener('click', handleSearchRecord);
    
    // 管理员统计按钮
    document.getElementById('admin-stats-btn')?.addEventListener('click', handleAdminStats);
    
    // 统计类型切换
    document.getElementById('admin-stats-type')?.addEventListener('change', handleStatsTypeChange);
}

// 处理登录
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('admin-username-input').value;
    const password = document.getElementById('admin-password-input').value;
    
    try {
        const response = await api.adminLogin({ username: username, password: password });
        if (response.message === 'Login successful') {
            currentAdmin = response.admin;
            localStorage.setItem('admin', JSON.stringify(currentAdmin));
            showAdminContent();
            loadPage(currentPage);
        } else {
            alert('登录失败: ' + response.error || '未知错误');
        }
    } catch (error) {
        alert('登录失败: ' + error.message);
    }
}

// 处理退出登录
function handleLogout() {
    localStorage.removeItem('admin');
    currentAdmin = null;
    showLoginPage();
}

// 显示登录页面
function showLoginPage() {
    loginPage.classList.add('active');
    pages.forEach(page => page.classList.remove('active'));
    navLinks.forEach(link => link.classList.remove('active'));
}

// 显示管理内容
function showAdminContent() {
    loginPage.classList.remove('active');
    adminUsername.textContent = currentAdmin.username;
}

// 处理导航点击
function handleNavClick(e) {
    e.preventDefault();
    
    // 移除所有活动状态
    navLinks.forEach(link => link.classList.remove('active'));
    pages.forEach(page => page.classList.remove('active'));
    
    // 添加当前活动状态
    const link = e.target;
    link.classList.add('active');
    
    // 获取页面ID
    const pageId = link.dataset.tab;
    currentPage = pageId;
    
    // 显示对应页面
    loadPage(pageId);
}

// 加载页面内容
function loadPage(pageId) {
    const page = document.getElementById(pageId);
    if (page) {
        page.classList.add('active');
        
        // 根据页面ID加载对应内容
        switch (pageId) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'users':
                loadUsers();
                break;
            case 'roles':
                loadRoles();
                break;
            case 'permissions':
                loadPermissions();
                break;
            case 'schedules':
                loadSchedules();
                break;
            case 'salary-config':
                loadSalaryConfig();
                break;
            case 'salary-calculation':
                loadSalaryCalculation();
                break;
            case 'stats':
                loadAdminStats();
                break;
            case 'time-records':
                loadTimeRecords();
                break;
            case 'operation-logs':
                loadOperationLogs();
                break;
            case 'scheduler':
                loadScheduler();
                break;
            case 'backup':
                loadBackupList();
                break;
            case 'daily-attendance-report':
                loadDailyAttendanceReport();
                break;
            case 'personal-attendance-report':
                loadPersonalAttendanceReport();
                break;
            case 'scheduler-report':
                loadSchedulerReport();
                break;
            case 'login-report':
                loadLoginReport();
                break;
            case 'online-users-report':
                loadOnlineUsersReport();
                break;
        }
    }
}

// 显示模态框
function showModal(title, content) {
    modalTitle.textContent = title;
    modalBody.innerHTML = content;
    modal.classList.add('show');
}

// 关闭模态框
function closeModal() {
    modal.classList.remove('show');
    modalBody.innerHTML = '';
}

// 加载仪表盘
async function loadDashboard() {
    try {
        // 获取今日统计数据
        const todayStats = await api.getAdminStats('today');
        // 获取本月统计数据
        const monthStats = await api.getAdminStats('month');
        // 获取角色总数
        const roles = await api.getRoles();
        // 获取用户总数
        const users = await api.getUsers();
        
        // 更新统计卡片
        document.getElementById('total-users').textContent = users.length || 0;
        document.getElementById('today-users').textContent = todayStats.working_users || 0;
        document.getElementById('monthly-hours').textContent = (monthStats.total_hours || 0).toFixed(2);
        document.getElementById('active-roles').textContent = roles.length || 0;
        
        // 加载最近操作日志
        loadRecentLogs();
    } catch (error) {
        console.error('加载仪表盘失败:', error);
    }
}

// 加载最近操作日志
async function loadRecentLogs() {
    try {
        const logs = await api.getOperationLogs(5);
        const recentLogs = document.getElementById('recent-logs');
        
        if (logs.length === 0) {
            recentLogs.innerHTML = '<p>暂无操作日志</p>';
            return;
        }
        
        recentLogs.innerHTML = logs.map(log => `
            <div class="log-item">
                <div class="log-time">${new Date(log.created_at).toLocaleString()}</div>
                <div class="log-details">${log.admin_id} - ${log.action} - ${log.module}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载最近操作日志失败:', error);
    }
}

// 加载用户列表
async function loadUsers() {
    try {
        const users = await api.getUsers();
        const userList = document.getElementById('user-list');
        
        if (users.length === 0) {
            userList.innerHTML = '<div class="list-item">暂无用户</div>';
            return;
        }
        
        userList.innerHTML = users.map(user => `
            <div class="list-item">
                <div>
                    <h4>${user.username}</h4>
                    <p>邮箱: ${user.email || '未设置'}</p>
                    <p>入职日期: ${user.hire_date || '未设置'}</p>
                </div>
                <div class="item-actions">
                    <button class="btn secondary" onclick="editUser(${user.id})">编辑</button>
                    <button class="btn danger" onclick="deleteUser(${user.id})">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载用户列表失败:', error);
    }
}

// 显示添加用户模态框
function showAddUserModal() {
    const content = `
        <form id="add-user-form">
            <div class="form-group">
                <label for="new-username">用户名</label>
                <input type="text" id="new-username" required>
            </div>
            <div class="form-group">
                <label for="new-password">密码</label>
                <input type="password" id="new-password" required>
            </div>
            <div class="form-group">
                <label for="new-email">邮箱</label>
                <input type="email" id="new-email">
            </div>
            <div class="form-group">
                <label for="new-hire-date">入职日期</label>
                <input type="date" id="new-hire-date">
            </div>
            <div class="form-group">
                <label for="new-roles">角色</label>
                <select id="new-roles" multiple style="height: 100px;">
                    <!-- 角色选项将通过JavaScript动态生成 -->
                </select>
                <small>按住Ctrl键可选择多个角色</small>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn primary">添加</button>
                <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
            </div>
        </form>
    `;
    
    showModal('添加用户', content);
    
    // 加载角色选项
    loadRoleOptions();
    
    // 绑定表单提交事件
    document.getElementById('add-user-form').addEventListener('submit', handleAddUser);
}

// 加载角色选项
async function loadRoleOptions() {
    try {
        const roles = await api.getRoles();
        const select = document.getElementById('new-roles');
        select.innerHTML = roles.map(role => `
            <option value="${role.id}">${role.name}</option>
        `).join('');
    } catch (error) {
        console.error('加载角色选项失败:', error);
    }
}

// 处理添加用户
let isAddingUser = false;

async function handleAddUser(e) {
    e.preventDefault();
    
    if (isAddingUser) {
        return;
    }
    isAddingUser = true;
    
    const submitBtn = document.querySelector('#add-user-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '添加中...';
    }
    
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-password').value;
    const email = document.getElementById('new-email').value;
    const hireDate = document.getElementById('new-hire-date').value;
    const roleIds = Array.from(document.getElementById('new-roles').selectedOptions).map(option => parseInt(option.value));
    
    try {
        await api.addUser({ username, password, email, hire_date: hireDate, role_ids: roleIds });
        closeModal();
        loadUsers();
        alert('用户添加成功');
    } catch (error) {
        alert('添加用户失败: ' + error.message);
    } finally {
        isAddingUser = false;
    }
}

// 编辑用户
async function editUser(userId) {
    try {
        const user = await api.getUser(userId);
        const roles = await api.getRoles();
        
        const content = `
            <form id="edit-user-form">
                <input type="hidden" id="edit-user-id" value="${user.id}">
                <div class="form-group">
                    <label for="edit-username">用户名</label>
                    <input type="text" id="edit-username" value="${user.username}" required>
                </div>
                <div class="form-group">
                    <label for="edit-email">邮箱</label>
                    <input type="email" id="edit-email" value="${user.email || ''}">
                </div>
                <div class="form-group">
                    <label for="edit-hire-date">入职日期</label>
                    <input type="date" id="edit-hire-date" value="${user.hire_date || ''}">
                </div>
                <div class="form-group">
                    <label for="edit-roles">角色</label>
                    <select id="edit-roles" multiple style="height: 100px;">
                        ${roles.map(role => `
                            <option value="${role.id}" ${user.roles?.includes(role.id) ? 'selected' : ''}>${role.name}</option>
                        `).join('')}
                    </select>
                    <small>按住Ctrl键可选择多个角色</small>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('编辑用户', content);
        
        // 绑定表单提交事件
        document.getElementById('edit-user-form').addEventListener('submit', handleEditUser);
    } catch (error) {
        alert('获取用户信息失败: ' + error.message);
    }
}

// 处理编辑用户
async function handleEditUser(e) {
    e.preventDefault();
    
    const userId = document.getElementById('edit-user-id').value;
    const username = document.getElementById('edit-username').value;
    const email = document.getElementById('edit-email').value;
    const hireDate = document.getElementById('edit-hire-date').value;
    const roleIds = Array.from(document.getElementById('edit-roles').selectedOptions).map(option => parseInt(option.value));
    
    try {
        // 先更新用户基本信息
        await api.updateUser(userId, { username, email, hire_date: hireDate });
        // 然后更新用户角色
        await api.assignRoles(userId, roleIds);
        closeModal();
        loadUsers();
        alert('用户更新成功');
    } catch (error) {
        alert('更新用户失败: ' + error.message);
    }
}

// 删除用户
async function deleteUser(userId) {
    if (confirm('确定要删除这个用户吗？')) {
        try {
            await api.deleteUser(userId);
            loadUsers();
            alert('用户删除成功');
        } catch (error) {
            alert('删除用户失败: ' + error.message);
        }
    }
}

// 加载角色列表
async function loadRoles() {
    try {
        const roles = await api.getRoles();
        const roleList = document.getElementById('role-list');
        
        if (roles.length === 0) {
            roleList.innerHTML = '<div class="list-item">暂无角色</div>';
            return;
        }
        
        roleList.innerHTML = roles.map(role => `
            <div class="list-item">
                <div>
                    <h4>${role.name}</h4>
                    <p>${role.description || '无描述'}</p>
                </div>
                <div class="item-actions">
                    <button class="btn secondary" onclick="editRoleUsers(${role.id}, '${role.name}')">修改用户</button>
                    <button class="btn secondary" onclick="editRole(${role.id})">编辑</button>
                    <button class="btn danger" onclick="deleteRole(${role.id})">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载角色列表失败:', error);
    }
}

// 显示添加角色模态框
function showAddRoleModal() {
    const content = `
        <form id="add-role-form">
            <div class="form-group">
                <label for="new-role-name">角色名称</label>
                <input type="text" id="new-role-name" required>
            </div>
            <div class="form-group">
                <label for="new-role-description">角色描述</label>
                <textarea id="new-role-description" rows="3"></textarea>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn primary">添加</button>
                <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
            </div>
        </form>
    `;
    
    showModal('添加角色', content);
    
    // 绑定表单提交事件
    document.getElementById('add-role-form').addEventListener('submit', handleAddRole);
}

// 处理添加角色
async function handleAddRole(e) {
    e.preventDefault();
    
    const name = document.getElementById('new-role-name').value;
    const description = document.getElementById('new-role-description').value;
    
    try {
        await api.addRole({ name, description });
        closeModal();
        loadRoles();
        alert('角色添加成功');
    } catch (error) {
        alert('添加角色失败: ' + error.message);
    }
}

// 编辑角色
async function editRole(roleId) {
    try {
        const role = await api.getRole(roleId);
        
        const content = `
            <form id="edit-role-form">
                <input type="hidden" id="edit-role-id" value="${role.id}">
                <div class="form-group">
                    <label for="edit-role-name">角色名称</label>
                    <input type="text" id="edit-role-name" value="${role.name}" required>
                </div>
                <div class="form-group">
                    <label for="edit-role-description">角色描述</label>
                    <textarea id="edit-role-description" rows="3">${role.description || ''}</textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('编辑角色', content);
        
        // 绑定表单提交事件
        document.getElementById('edit-role-form').addEventListener('submit', handleEditRole);
    } catch (error) {
        alert('获取角色信息失败: ' + error.message);
    }
}

// 处理编辑角色
async function handleEditRole(e) {
    e.preventDefault();
    
    const roleId = document.getElementById('edit-role-id').value;
    const name = document.getElementById('edit-role-name').value;
    const description = document.getElementById('edit-role-description').value;
    
    try {
        await api.updateRole(roleId, { name, description });
        closeModal();
        loadRoles();
        alert('角色更新成功');
    } catch (error) {
        alert('更新角色失败: ' + error.message);
    }
}

// 修改角色用户
async function editRoleUsers(roleId, roleName) {
    try {
        // 获取所有用户和该角色已分配的用户
        const [allUsers, roleUsers] = await Promise.all([
            api.getAllUsers(),
            api.getUsersByRole(roleId)
        ]);
        
        // 提取已分配用户的ID集合
        const assignedUserIds = new Set(roleUsers.map(user => user.id));
        
        // 生成用户选择列表
        const usersOptions = allUsers.map(user => `
            <div class="checkbox-item">
                <input type="checkbox" id="user-${user.id}" value="${user.id}" ${assignedUserIds.has(user.id) ? 'checked' : ''}>
                <label for="user-${user.id}">${user.username}</label>
            </div>
        `).join('');
        
        const content = `
            <form id="edit-role-users-form">
                <input type="hidden" id="edit-role-id" value="${roleId}">
                <h4>${roleName}</h4>
                <div class="form-group">
                    <label>选择用户</label>
                    <div class="checkbox-group">
                        ${usersOptions}
                    </div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('修改角色用户', content);
        
        // 绑定表单提交事件
        document.getElementById('edit-role-users-form').addEventListener('submit', handleEditRoleUsers);
    } catch (error) {
        console.error('加载角色用户失败:', error);
        alert('加载角色用户失败: ' + error.message);
    }
}

// 处理修改角色用户
async function handleEditRoleUsers(e) {
    e.preventDefault();
    
    const roleId = document.getElementById('edit-role-id').value;
    
    // 获取选中的用户ID
    const checkboxes = document.querySelectorAll('#edit-role-users-form input[type="checkbox"]');
    const userIds = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => parseInt(checkbox.value));
    
    try {
        await api.assignRoles(roleId, userIds);
        closeModal();
        alert('角色用户修改成功');
    } catch (error) {
        console.error('修改角色用户失败:', error);
        alert('修改角色用户失败: ' + error.message);
    }
}

// 删除角色
async function deleteRole(roleId) {
    if (confirm('确定要删除这个角色吗？')) {
        try {
            await api.deleteRole(roleId);
            loadRoles();
            alert('角色删除成功');
        } catch (error) {
            alert('删除角色失败: ' + error.message);
        }
    }
}

// 加载权限列表
async function loadPermissions() {
    try {
        const permissions = await api.getPermissions();
        const permissionList = document.getElementById('permission-list');
        
        if (permissions.length === 0) {
            permissionList.innerHTML = '<div class="list-item">暂无权限</div>';
            return;
        }
        
        permissionList.innerHTML = permissions.map(permission => `
            <div class="list-item">
                <div>
                    <h4>${permission.name}</h4>
                    <p>${permission.description || '无描述'}</p>
                </div>
                <div class="item-actions">
                    <button class="btn secondary" onclick="editPermission(${permission.id})">编辑</button>
                    <button class="btn danger" onclick="deletePermission(${permission.id})">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载权限列表失败:', error);
    }
}

// 显示添加权限模态框
function showAddPermissionModal() {
    const content = `
        <form id="add-permission-form">
            <div class="form-group">
                <label for="new-permission-name">权限名称</label>
                <input type="text" id="new-permission-name" required>
            </div>
            <div class="form-group">
                <label for="new-permission-description">权限描述</label>
                <textarea id="new-permission-description" rows="3"></textarea>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn primary">添加</button>
                <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
            </div>
        </form>
    `;
    
    showModal('添加权限', content);
    
    // 绑定表单提交事件
    document.getElementById('add-permission-form').addEventListener('submit', handleAddPermission);
}

// 处理添加权限
async function handleAddPermission(e) {
    e.preventDefault();
    
    const name = document.getElementById('new-permission-name').value;
    const description = document.getElementById('new-permission-description').value;
    
    try {
        await api.addPermission({ name, description });
        closeModal();
        loadPermissions();
        alert('权限添加成功');
    } catch (error) {
        alert('添加权限失败: ' + error.message);
    }
}

// 编辑权限
async function editPermission(permissionId) {
    try {
        const permission = await api.getPermission(permissionId);
        
        const content = `
            <form id="edit-permission-form">
                <input type="hidden" id="edit-permission-id" value="${permission.id}">
                <div class="form-group">
                    <label for="edit-permission-name">权限名称</label>
                    <input type="text" id="edit-permission-name" value="${permission.name}" required>
                </div>
                <div class="form-group">
                    <label for="edit-permission-description">权限描述</label>
                    <textarea id="edit-permission-description" rows="3">${permission.description || ''}</textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('编辑权限', content);
        
        // 绑定表单提交事件
        document.getElementById('edit-permission-form').addEventListener('submit', handleEditPermission);
    } catch (error) {
        alert('获取权限信息失败: ' + error.message);
    }
}

// 处理编辑权限
async function handleEditPermission(e) {
    e.preventDefault();
    
    const permissionId = document.getElementById('edit-permission-id').value;
    const name = document.getElementById('edit-permission-name').value;
    const description = document.getElementById('edit-permission-description').value;
    
    try {
        await api.updatePermission(permissionId, { name, description });
        closeModal();
        loadPermissions();
        alert('权限更新成功');
    } catch (error) {
        alert('更新权限失败: ' + error.message);
    }
}

// 删除权限
async function deletePermission(permissionId) {
    if (confirm('确定要删除这个权限吗？')) {
        try {
            await api.deletePermission(permissionId);
            loadPermissions();
            alert('权限删除成功');
        } catch (error) {
            alert('删除权限失败: ' + error.message);
        }
    }
}

// 加载排班列表
async function loadSchedules() {
    try {
        const schedules = await api.getSchedules();
        const scheduleList = document.getElementById('schedule-list');
        
        if (schedules.length === 0) {
            scheduleList.innerHTML = '<div class="list-item">暂无排班</div>';
            return;
        }
        
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
        
        // 获取所有用户信息
        const users = await api.getAllUsers();
        const usersDict = {};
        for (const user of users) {
            usersDict[user.id] = user;
        }
        
        scheduleList.innerHTML = schedules.map(schedule => `
            <div class="list-item">
                <div>
                    <h4>${usersDict[schedule.user_id]?.username || `用户ID: ${schedule.user_id}`}</h4>
                    <p>日期范围: ${formatDateRange(schedule.start_date, schedule.end_date)}</p>
                    <p>班别: ${schedule.shift_type}</p>
                    <p>工时: ${schedule.hours} 小时</p>
                    <p>描述: ${schedule.description || '无'}</p>
                </div>
                <div class="item-actions">
                    <button class="btn secondary" onclick="editSchedule(${schedule.id})">编辑</button>
                    <button class="btn danger" onclick="deleteSchedule(${schedule.id})">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载排班列表失败:', error);
    }
}

// 显示添加排班模态框
function showAddScheduleModal() {
    // 获取所有用户
    api.getAllUsers().then(users => {
        const usersOptions = users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
        
        const content = `
            <form id="add-schedule-form">
                <div class="form-group">
                    <label for="schedule-user-id">用户名</label>
                    <select id="schedule-user-id" required>
                        <option value="">请选择用户</option>
                        ${usersOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label for="schedule-start-date">开始日期</label>
                    <input type="date" id="schedule-start-date" required>
                </div>
                <div class="form-group">
                    <label for="schedule-end-date">结束日期</label>
                    <input type="date" id="schedule-end-date" required>
                </div>
                <div class="form-group">
                    <label for="schedule-shift-type">班别</label>
                    <select id="schedule-shift-type" required>
                        <option value="白班">白班</option>
                        <option value="夜班">夜班</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="schedule-hours">工时</label>
                    <input type="number" id="schedule-hours" step="0.5" required>
                </div>
                <div class="form-group">
                    <label for="schedule-description">描述</label>
                    <textarea id="schedule-description" rows="3"></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">添加</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('添加排班', content);
        
        // 绑定表单提交事件
        document.getElementById('add-schedule-form').addEventListener('submit', handleAddSchedule);
    }).catch(error => {
        alert('获取用户列表失败: ' + error.message);
    });
}

// 处理添加排班
async function handleAddSchedule(e) {
    e.preventDefault();
    
    const userId = document.getElementById('schedule-user-id').value;
    const startDate = document.getElementById('schedule-start-date').value;
    const endDate = document.getElementById('schedule-end-date').value;
    const shiftType = document.getElementById('schedule-shift-type').value;
    const hours = document.getElementById('schedule-hours').value;
    const description = document.getElementById('schedule-description').value;
    
    try {
        await api.addSchedule({ user_id: parseInt(userId), start_date: startDate, end_date: endDate, shift_type: shiftType, hours: parseFloat(hours), description });
        closeModal();
        loadSchedules();
        alert('排班添加成功');
    } catch (error) {
        alert('添加排班失败: ' + error.message);
    }
}

// 显示批量排班模态框
function showBatchScheduleModal() {
    // 同时获取所有角色和用户
    Promise.all([
        api.getRoles(),
        api.getAllUsers()
    ]).then(([roles, users]) => {
        const rolesOptions = roles.map(role => `<option value="${role.id}">${role.name}</option>`).join('');
        const usersOptions = users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
        
        const content = `
            <form id="batch-schedule-form">
                <div class="form-group">
                    <label for="batch-role-id">角色</label>
                    <select id="batch-role-id">
                        <option value="">请选择角色</option>
                        ${rolesOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-user-id">用户名</label>
                    <select id="batch-user-id" multiple style="height: 150px;">
                        <option value="">请选择用户（可多选）</option>
                        ${usersOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-start-date">开始日期</label>
                    <input type="date" id="batch-start-date" required>
                </div>
                <div class="form-group">
                    <label for="batch-end-date">结束日期</label>
                    <input type="date" id="batch-end-date" required>
                </div>
                <div class="form-group">
                    <label for="batch-shift-type">班别</label>
                    <select id="batch-shift-type" required>
                        <option value="白班">白班</option>
                        <option value="夜班">夜班</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-hours">工时</label>
                    <input type="number" id="batch-hours" step="0.5" required>
                </div>
                <div class="form-group">
                    <label for="batch-description">描述</label>
                    <textarea id="batch-description" rows="3"></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">批量添加</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('批量排班', content);
        
        // 绑定表单提交事件
        document.getElementById('batch-schedule-form').addEventListener('submit', handleBatchSchedule);
    }).catch(error => {
        alert('获取角色和用户列表失败: ' + error.message);
    });
}

// 处理批量排班
async function handleBatchSchedule(e) {
    e.preventDefault();
    
    const roleId = document.getElementById('batch-role-id').value;
    const startDate = document.getElementById('batch-start-date').value;
    const endDate = document.getElementById('batch-end-date').value;
    const shiftType = document.getElementById('batch-shift-type').value;
    const hours = document.getElementById('batch-hours').value;
    const description = document.getElementById('batch-description').value;
    
    try {
        // 获取该角色下的所有用户
        const users = await api.getUsersByRole(roleId);
        // 构建批量排班数据
        const batchData = {
            schedules: users.map(user => ({
                user_id: user.id,
                start_date: startDate,
                end_date: endDate,
                shift_type: shiftType,
                hours: parseFloat(hours),
                description
            }))
        };
        await api.batchSchedule(batchData);
        closeModal();
        loadSchedules();
        alert('批量排班添加成功');
    } catch (error) {
        alert('批量排班失败: ' + error.message);
    }
}

// 显示批量安排调休模态框
function showArrangeLeaveModal() {
    // 获取所有用户
    api.getAllUsers().then(users => {
        const usersOptions = users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
        
        const content = `
            <form id="arrange-leave-form">
                <div class="form-group">
                    <label for="leave-user-ids">用户名（可多选）</label>
                    <select id="leave-user-ids" multiple style="height: 150px;" required>
                        ${usersOptions}
                    </select>
                    <small>按住Ctrl键可选择多个用户</small>
                </div>
                <div class="form-group">
                    <label>调休日期（可多选）</label>
                    <div id="leave-dates-container" style="margin-top: 8px;">
                        <!-- 日期组件将通过JavaScript动态生成 -->
                    </div>
                    <button type="button" id="add-date-btn" class="btn small secondary" style="margin-top: 8px;">添加日期</button>
                    <input type="hidden" id="selected-dates" required>
                    <small style="display: block; margin-top: 8px;">点击日期组件选择调休日期，可添加多个日期</small>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">安排调休</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('批量安排调休', content);
        
        // 初始化日期组件
        initDateComponents();
        
        // 绑定表单提交事件
        document.getElementById('arrange-leave-form').addEventListener('submit', handleArrangeLeave);
    }).catch(error => {
        alert('获取用户列表失败: ' + error.message);
    });
}

// 初始化日期组件
function initDateComponents() {
    // 添加一个初始日期组件
    addDateComponent();
    
    // 绑定添加日期按钮事件
    document.getElementById('add-date-btn').addEventListener('click', addDateComponent);
}

// 添加日期组件
function addDateComponent() {
    const container = document.getElementById('leave-dates-container');
    const componentIndex = container.children.length;
    
    // 创建日期组件容器
    const componentDiv = document.createElement('div');
    componentDiv.className = 'date-component';
    componentDiv.style.display = 'flex';
    componentDiv.style.alignItems = 'center';
    componentDiv.style.marginBottom = '8px';
    
    // 创建日期输入框
    const dateInput = document.createElement('input');
    dateInput.type = 'date';
    dateInput.id = `leave-date-${componentIndex}`;
    dateInput.className = 'leave-date-input';
    dateInput.required = true;
    
    // 创建删除按钮
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'btn small danger';
    deleteBtn.textContent = '删除';
    deleteBtn.style.marginLeft = '8px';
    deleteBtn.addEventListener('click', () => {
        componentDiv.remove();
        updateSelectedDates();
    });
    
    // 添加事件监听，更新隐藏字段
    dateInput.addEventListener('change', updateSelectedDates);
    
    // 组装组件
    componentDiv.appendChild(dateInput);
    componentDiv.appendChild(deleteBtn);
    container.appendChild(componentDiv);
    
    // 更新隐藏字段
    updateSelectedDates();
}

// 更新选中的日期到隐藏字段
function updateSelectedDates() {
    const dateInputs = document.querySelectorAll('.leave-date-input');
    const selectedDates = Array.from(dateInputs)
        .map(input => input.value)
        .filter(date => date !== '');
    
    document.getElementById('selected-dates').value = JSON.stringify(selectedDates);
}

// 处理批量安排调休
async function handleArrangeLeave(e) {
    e.preventDefault();
    
    const userSelect = document.getElementById('leave-user-ids');
    const userIds = Array.from(userSelect.selectedOptions).map(option => parseInt(option.value));
    const selectedDatesJson = document.getElementById('selected-dates').value;
    
    // 解析日期列表
    const dates = JSON.parse(selectedDatesJson);
    
    if (userIds.length === 0) {
        alert('请选择至少一个用户');
        return;
    }
    
    if (dates.length === 0) {
        alert('请选择至少一个调休日期');
        return;
    }
    
    try {
        // 调用后端API安排调休
        await api.arrangeLeave({ user_ids: userIds, dates: dates });
        closeModal();
        loadSchedules();
        alert('批量安排调休成功');
    } catch (error) {
        alert('批量安排调休失败: ' + error.message);
    }
}

// 编辑排班
async function editSchedule(scheduleId) {
    try {
        const schedule = await api.getSchedule(scheduleId);
        
        const content = `
            <form id="edit-schedule-form">
                <input type="hidden" id="edit-schedule-id" value="${schedule.id}">
                <div class="form-group">
                    <label for="edit-schedule-user-id">用户ID</label>
                    <input type="number" id="edit-schedule-user-id" value="${schedule.user_id}" required>
                </div>
                <div class="form-group">
                    <label for="edit-schedule-start-date">开始日期</label>
                    <input type="date" id="edit-schedule-start-date" value="${schedule.start_date}" required>
                </div>
                <div class="form-group">
                    <label for="edit-schedule-end-date">结束日期</label>
                    <input type="date" id="edit-schedule-end-date" value="${schedule.end_date}" required>
                </div>
                <div class="form-group">
                    <label for="edit-schedule-shift-type">班别</label>
                    <select id="edit-schedule-shift-type" required>
                        <option value="白班" ${schedule.shift_type === '白班' ? 'selected' : ''}>白班</option>
                        <option value="夜班" ${schedule.shift_type === '夜班' ? 'selected' : ''}>夜班</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="edit-schedule-hours">工时</label>
                    <input type="number" id="edit-schedule-hours" step="0.5" value="${schedule.hours}" required>
                </div>
                <div class="form-group">
                    <label for="edit-schedule-description">描述</label>
                    <textarea id="edit-schedule-description" rows="3">${schedule.description || ''}</textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('编辑排班', content);
        
        // 绑定表单提交事件
        document.getElementById('edit-schedule-form').addEventListener('submit', handleEditSchedule);
    } catch (error) {
        alert('获取排班信息失败: ' + error.message);
    }
}

// 处理编辑排班
async function handleEditSchedule(e) {
    e.preventDefault();
    
    const scheduleId = document.getElementById('edit-schedule-id').value;
    const userId = document.getElementById('edit-schedule-user-id').value;
    const startDate = document.getElementById('edit-schedule-start-date').value;
    const endDate = document.getElementById('edit-schedule-end-date').value;
    const shiftType = document.getElementById('edit-schedule-shift-type').value;
    const hours = document.getElementById('edit-schedule-hours').value;
    const description = document.getElementById('edit-schedule-description').value;
    
    try {
        await api.updateSchedule(scheduleId, {
            user_id: parseInt(userId),
            start_date: startDate,
            end_date: endDate,
            shift_type: shiftType,
            hours: parseFloat(hours),
            description
        });
        closeModal();
        loadSchedules();
        alert('排班更新成功');
    } catch (error) {
        alert('更新排班失败: ' + error.message);
    }
}

// 删除排班
async function deleteSchedule(scheduleId) {
    if (confirm('确定要删除这个排班吗？')) {
        try {
            await api.deleteSchedule(scheduleId);
            loadSchedules();
            alert('排班删除成功');
        } catch (error) {
            alert('删除排班失败: ' + error.message);
        }
    }
}

// 处理删除过期排班
async function handleDeleteExpiredSchedules() {
    if (confirm('确定要删除所有过期排班吗？')) {
        try {
            await api.deleteExpiredSchedules();
            loadSchedules();
            alert('过期排班删除成功');
        } catch (error) {
            alert('删除过期排班失败: ' + error.message);
        }
    }
}

// 一键生成工时记录
async function handleSchedulesToTimeRecords() {
    if (confirm('确定要将所有没有工时记录的排班写入工时记录吗？')) {
        try {
            const response = await api.schedulesToTimeRecords();
            alert(response.message);
        } catch (error) {
            alert('生成工时记录失败: ' + error.message);
        }
    }
}

// 加载工资算法配置
async function loadSalaryConfig() {
    try {
        const configs = await api.getSalaryConfig();
        const configList = document.getElementById('salary-config-list');
        
        if (configs.length === 0) {
            configList.innerHTML = '<div class="config-item">暂无配置</div>';
            return;
        }
        
        configList.innerHTML = configs.map(config => `
            <div class="config-item">
                <div class="config-header">
                    <div class="config-key">${config.config_key}</div>
                    <div class="config-value">${config.config_value}</div>
                </div>
                <div class="config-description">${config.description || '无描述'}</div>
                <div class="config-actions">
                    <button class="btn secondary" onclick="editSalaryConfig(${config.id})">编辑</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载工资算法配置失败:', error);
    }
}

// 处理重置工资配置
async function handleResetSalaryConfig() {
    if (confirm('确定要重置工资算法配置为默认值吗？')) {
        try {
            await api.resetSalaryConfig();
            loadSalaryConfig();
            alert('工资算法配置已重置为默认值');
        } catch (error) {
            alert('重置工资算法配置失败: ' + error.message);
        }
    }
}

// 加载工资计算页面
async function loadSalaryCalculation() {
    try {
        // 加载用户列表
        const users = await api.getUsers();
        const userSelect = document.getElementById('salary-user-select');
        
        // 清空现有选项
        userSelect.innerHTML = '';
        
        // 添加用户选项
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.username}`;
            userSelect.appendChild(option);
        });
        
        // 设置默认月份为当前月份
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
        document.getElementById('personal-report-start-date').value = firstDay;
        document.getElementById('personal-report-end-date').value = lastDay;
        
        // 绑定事件
        document.getElementById('generate-personal-report-btn').addEventListener('click', generatePersonalAttendanceReport);
    } catch (error) {
        console.error('加载工资计算页面失败:', error);
    }
}

// 处理计算工资
async function handleCalculateSalary() {
    const userId = document.getElementById('salary-user-select').value;
    const month = document.getElementById('salary-month-input').value;
    
    try {
        const result = await api.calculateSalary(userId, month);
        const salaryResult = document.getElementById('salary-result');
        
        salaryResult.innerHTML = `
            <h3>${month} 工资计算结果</h3>
            <div class="salary-details">
                <div class="salary-item">
                    <div class="label">底薪</div>
                    <div class="value">${result.salary_details.base_salary}</div>
                </div>
                <div class="salary-item">
                    <div class="label">满勤奖</div>
                    <div class="value">${result.salary_details.attendance_bonus}</div>
                </div>
                <div class="salary-item">
                    <div class="label">加班费</div>
                    <div class="value">${result.salary_details.overtime_pay}</div>
                </div>
                <div class="salary-item">
                    <div class="label">夜班补贴</div>
                    <div class="value">${result.salary_details.night_shift_allowance}</div>
                </div>
                <div class="salary-item">
                    <div class="label">工龄奖</div>
                    <div class="value">${result.salary_details.seniority_bonus}</div>
                </div>
                <div class="salary-item">
                    <div class="label">税前工资</div>
                    <div class="value">${result.salary_details.pre_tax_salary}</div>
                </div>
                <div class="salary-item">
                    <div class="label">水电费</div>
                    <div class="value">${result.salary_details.utility_fee}</div>
                </div>
                <div class="salary-item">
                    <div class="label">五险一金</div>
                    <div class="value">${result.salary_details.insurance}</div>
                </div>
                <div class="salary-item">
                    <div class="label">个人所得税</div>
                    <div class="value">${result.salary_details.tax}</div>
                </div>
            </div>
            <div class="salary-total">
                <div class="label">实发工资</div>
                <div class="value">${result.salary_details.net_salary}</div>
            </div>
            <div class="salary-meta">
                <p>总工时: ${result.total_hours} 小时</p>
                <p>夜班次数: ${result.night_shifts} 次</p>
            </div>
        `;
    } catch (error) {
        alert('计算工资失败: ' + error.message);
    }
}

// 处理统计类型切换
function handleStatsTypeChange() {
    const statsType = document.getElementById('admin-stats-type').value;
    const customDateRange = document.getElementById('admin-custom-date-range');
    
    if (statsType === 'custom') {
        customDateRange.style.display = 'flex';
    } else {
        customDateRange.style.display = 'none';
    }
}

// 处理管理员统计
async function handleAdminStats() {
    const statsType = document.getElementById('admin-stats-type').value;
    let startDate, endDate;
    
    if (statsType === 'custom') {
        startDate = document.getElementById('admin-start-date').value;
        endDate = document.getElementById('admin-end-date').value;
        
        if (!startDate || !endDate) {
            alert('请选择完整的日期范围');
            return;
        }
    }
    
    try {
        const stats = await api.getAdminStats(statsType, startDate, endDate);
        renderStatsChart(stats);
    } catch (error) {
        alert('获取统计数据失败: ' + error.message);
    }
}

// 加载管理员统计
async function loadAdminStats() {
    try {
        const stats = await api.getAdminStats('today');
        renderStatsChart(stats);
    } catch (error) {
        console.error('加载管理员统计失败:', error);
    }
}

// 渲染统计图表
function renderStatsChart(stats) {
    const ctx = document.getElementById('admin-chart-canvas').getContext('2d');
    
    // 销毁现有图表
    if (window.adminChart) {
        window.adminChart.destroy();
    }
    
    // 准备图表数据
    const labels = stats.dates || ['今日', '昨日', '前日'];
    const data = stats.hours || [0, 0, 0];
    
    // 创建新图表
    window.adminChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '工时统计',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
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
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '工时统计图表'
                }
            }
        }
    });
}

// 加载工时记录管理
async function loadTimeRecords() {
    try {
        const records = await api.getTimeRecords();
        const recordList = document.getElementById('admin-record-list');
        
        if (records.length === 0) {
            recordList.innerHTML = '<div class="record-item">暂无工时记录</div>';
            return;
        }
        
        recordList.innerHTML = records.map(record => `
            <div class="record-item">
                <div class="record-header">
                    <div class="record-user">用户ID: ${record.user_id} (${record.username || '未知用户'})</div>
                    <div class="record-date">${new Date(record.start_time).toLocaleString()}</div>
                </div>
                <div class="record-details">
                    <div>班别: <span class="record-shift ${record.shift_type === '白班' ? 'day' : 'night'}">${record.shift_type}</span></div>
                    <div>工时: ${record.duration / 60} 小时</div>
                    <div>是否请假: ${record.is_leave ? '是' : '否'}</div>
                    <div>描述: ${record.description || '无'}</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载工时记录失败:', error);
    }
}

// 处理检查重复工时记录
async function handleCheckDuplicateRecords() {
    try {
        const duplicates = await api.checkDuplicateTimeRecords();
        
        if (duplicates.length === 0) {
            alert('未发现重复工时记录');
        } else {
            const content = `
                <h4>发现 ${duplicates.length} 条重复工时记录:</h4>
                <div class="duplicate-list">
                    ${duplicates.map(dup => `
                        <div class="duplicate-item">
                            <p>用户: ${dup.username || '未知用户'} (ID: ${dup.user_id})</p>
                            <p>日期: ${dup.record_date}</p>
                            <p>记录数量: ${dup.record_count} 条</p>
                        </div>
                    `).join('')}
                </div>
            `;
            showModal('重复工时记录', content);
        }
    } catch (error) {
        alert('检查重复工时记录失败: ' + error.message);
    }
}

function showImportExcelModal() {
    modalTitle.textContent = 'Excel导入工时记录';
    
    const content = `
        <div class="import-excel-form">
            <div class="form-group">
                <label for="import-user-select">选择用户</label>
                <select id="import-user-select" required>
                    <option value="">请选择用户</option>
                </select>
            </div>
            <div class="form-group">
                <label for="import-excel-file">选择Excel文件</label>
                <input type="file" id="import-excel-file" accept=".xlsx" required>
                <p class="hint">支持 .xlsx 格式，列顺序：日期、班次、上班时间、下班时间、工时(小时)</p>
            </div>
            <div class="form-group">
                <label for="import-sheet-select">选择工作表</label>
                <select id="import-sheet-select" disabled>
                    <option value="">请先选择Excel文件</option>
                </select>
            </div>
            <div class="form-group">
                <button id="submit-import-btn" class="btn primary">开始导入</button>
                <button id="cancel-import-btn" class="btn secondary">取消</button>
            </div>
        </div>
    `;
    
    modalBody.innerHTML = content;
    
    // 加载用户列表
    loadUsersForImport();
    
    // 绑定事件
    document.getElementById('submit-import-btn').addEventListener('click', handleImportExcel);
    document.getElementById('cancel-import-btn').addEventListener('click', closeModal);
    document.getElementById('import-excel-file').addEventListener('change', handleExcelFileSelect);
    
    modal.style.display = 'block';
}

async function loadUsersForImport() {
    try {
        const users = await api.getUsers();
        const select = document.getElementById('import-user-select');
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.username;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载用户列表失败:', error);
    }
}

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
        
        const response = await fetch('/api/time-records/import-excel/sheets', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
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

async function handleImportExcel() {
    const userId = document.getElementById('import-user-select').value;
    const fileInput = document.getElementById('import-excel-file');
    const sheetSelect = document.getElementById('import-sheet-select');
    
    if (!userId) {
        alert('请选择用户');
        return;
    }
    
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
        formData.append('user_id', userId);
        if (sheetName) {
            formData.append('sheet_name', sheetName);
        }
        
        const result = await api.importExcelTimeRecords(formData);
        
        const content = `
            <div class="import-result">
                <h4>导入结果</h4>
                <p>总记录数: ${result.total_rows}</p>
                <p>成功导入: ${result.success_count}</p>
                <p>重复跳过: ${result.duplicate_count}</p>
                <p>导入失败: ${result.error_count}</p>
                ${result.errors && result.errors.length > 0 ? `
                    <h5>错误详情:</h5>
                    <ul>
                        ${result.errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
        
        showModal('导入完成', content);
    } catch (error) {
        alert('导入失败: ' + error.message);
    }
}

// 加载操作日志
async function loadOperationLogs() {
    try {
        const logs = await api.getOperationLogs();
        const logList = document.getElementById('operation-log-list');
        
        if (logs.length === 0) {
            logList.innerHTML = '<div class="log-item">暂无操作日志</div>';
            return;
        }
        
        logList.innerHTML = logs.map(log => `
            <div class="log-item">
                <div class="log-header">
                    <div class="log-admin">管理员: ${log.admin_id}</div>
                    <div class="log-time">${new Date(log.created_at).toLocaleString()}</div>
                </div>
                <div class="log-details">
                    <p>模块: ${log.module}</p>
                    <p>操作: ${log.action}</p>
                    <p>目标: ${log.target_type || '无'} - ${log.target_id || '无'}</p>
                    <p>详情: ${log.details || '无'}</p>
                    <p>IP地址: ${log.ip_address || '无'}</p>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载操作日志失败:', error);
    }
}

// 加载自动任务管理器
async function loadScheduler() {
    try {
        // 任务名称中文映射
        const jobNameMap = {
            'auto_add_time_records': '自动添加工时记录',
            'send_system_message': '发送系统消息',
            'delete_expired_schedules': '删除过期排班',
            'check_duplicate_time_records': '检查重复工时记录'
        };
        
        // 任务状态中文映射
        const jobStatusMap = {
            'enabled': '运行中',
            'disabled': '已停止',
            'running': '运行中',
            'stopped': '已停止'
        };
        
        // 加载任务列表
        const jobs = await api.getSchedulerJobs();
        const jobList = document.getElementById('scheduler-job-list');
        
        if (jobs.length === 0) {
            jobList.innerHTML = '<div class="job-item">暂无定时任务</div>';
        } else {
            jobList.innerHTML = jobs.map(job => `
                <div class="job-item">
                    <div class="job-info">
                        <span class="job-name">${jobNameMap[job.job_name] || job.job_name}</span>
                        <span class="job-status ${job.status === 'enabled' || job.status === 'running' ? 'running' : 'stopped'}">${jobStatusMap[job.status] || job.status}</span>
                    </div>
                    <div class="job-schedule">${job.description}</div>
                    <div class="job-actions">
                        <button class="btn secondary" onclick="executeJob('${job.job_name}')">执行</button>
                        <button class="btn ${job.status === 'enabled' || job.status === 'running' ? 'danger' : 'success'}" onclick="toggleJob('${job.job_name}')">${job.status === 'enabled' || job.status === 'running' ? '停止' : '启动'}</button>
                    </div>
                </div>
            `).join('');
        }
        
        // 加载任务日志
        const logsResponse = await api.getSchedulerLogs();
        const logs = logsResponse.logs || [];
        const logList = document.getElementById('scheduler-log-list');
        
        if (logs.length === 0) {
            logList.innerHTML = '<div class="log-item">暂无任务执行日志</div>';
        } else {
            logList.innerHTML = logs.map(log => `
                <div class="log-item">
                    <div class="log-header">
                        <div class="log-admin">任务: ${jobNameMap[log.job_name] || log.job_name}</div>
                        <div class="log-time">${new Date(log.start_time).toLocaleString()}</div>
                    </div>
                    <div class="log-details">
                        <p>状态: ${log.status === 'success' ? '成功' : '失败'}</p>
                        <p>执行时间: ${log.execution_time || 0} 秒</p>
                        <p>消息: ${log.message || '无'}</p>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载自动任务管理器失败:', error);
    }
}

// 执行定时任务
async function executeJob(jobName) {
    try {
        await api.executeSchedulerJob(jobName);
        loadScheduler();
        alert('任务执行成功');
    } catch (error) {
        alert('任务执行失败: ' + error.message);
    }
}

// 切换定时任务状态
async function toggleJob(jobName) {
    try {
        await api.toggleSchedulerJob(jobName);
        loadScheduler();
        alert('任务状态切换成功');
    } catch (error) {
        alert('任务状态切换失败: ' + error.message);
    }
}

// 加载备份列表
async function loadBackupList() {
    try {
        const response = await api.getBackupList();
        const backups = response.backups || [];
        const backupList = document.getElementById('backup-list');
        
        if (backups.length === 0) {
            backupList.innerHTML = '<div class="backup-item">暂无备份</div>';
            return;
        }
        
        backupList.innerHTML = backups.map(backup => `
            <div class="backup-item">
                <div class="backup-info">
                    <div class="backup-date">${new Date(backup.created_at).toLocaleString()}</div>
                    <div class="backup-size">${backup.size} KB</div>
                    <div class="backup-filename">${backup.filename}</div>
                </div>
                <div class="item-actions">
                    <button class="btn secondary" onclick="previewBackup('${backup.filename}')">预览</button>
                    <button class="btn secondary" onclick="downloadBackup('${backup.filename}')">下载</button>
                    <button class="btn danger" onclick="deleteBackup('${backup.filename}')">删除</button>
                    <button class="btn primary" onclick="restoreBackup('${backup.filename}')">恢复</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载备份列表失败:', error);
        const backupList = document.getElementById('backup-list');
        backupList.innerHTML = `<div class="backup-item error">加载备份列表失败: ${error.message}</div>`;
    }
}

// 处理创建备份
async function handleCreateBackup() {
    try {
        await api.createBackup();
        loadBackupList();
        alert('备份创建成功');
    } catch (error) {
        alert('创建备份失败: ' + error.message);
    }
}

// 处理自动备份
async function handleAutoBackup() {
    try {
        await api.autoBackup();
        loadBackupList();
        alert('自动备份执行成功');
    } catch (error) {
        alert('自动备份执行失败: ' + error.message);
    }
}

// 下载备份
function downloadBackup(filename) {
    window.location.href = `/api/backup/${filename}`;
}

// 预览备份
async function previewBackup(filename) {
    try {
        // 获取备份文件内容
        const response = await fetch(`/api/backup/${filename}/preview`);
        const result = await response.json();
        
        if (!response.ok) {
            alert('预览备份失败: ' + (result.error || '未知错误'));
            return;
        }
        
        // 显示预览模态框
        const content = `
            <div class="backup-preview">
                <h4>备份文件预览: ${result.filename}</h4>
                <div class="preview-header">
                    <div class="preview-info">
                        <div>文件大小: ${result.total_length} 字符</div>
                        ${result.total_length > 10000 ? '<div class="warning">内容过长，已截断显示</div>' : ''}
                    </div>
                </div>
                <div class="preview-content">
                    <pre>${result.content}</pre>
                </div>
                <div class="preview-actions">
                    <button class="btn primary" onclick="downloadBackup('${filename}')">下载完整文件</button>
                    <button class="btn secondary" onclick="closeModal()">关闭</button>
                </div>
            </div>
        `;
        
        showModal('备份预览', content);
    } catch (error) {
        alert('预览备份失败: ' + error.message);
        console.error('预览备份错误:', error);
    }
}

// 删除备份
async function deleteBackup(filename) {
    if (confirm('确定要删除这个备份吗？')) {
        try {
            await api.deleteBackup(filename);
            loadBackupList();
            alert('备份删除成功');
        } catch (error) {
            alert('删除备份失败: ' + error.message);
        }
    }
}

// 恢复备份
async function restoreBackup(filename) {
    if (confirm('确定要从这个备份恢复数据吗？这将覆盖当前所有数据！')) {
        try {
            await api.restoreBackup(filename);
            alert('数据恢复成功');
        } catch (error) {
            alert('恢复数据失败: ' + error.message);
        }
    }
}

// 处理搜索用户
async function handleSearchUser() {
    const searchTerm = document.getElementById('user-search').value;
    try {
        const users = await api.searchUsers(searchTerm);
        const userList = document.getElementById('user-list');
        
        if (users.length === 0) {
            userList.innerHTML = '<div class="list-item">未找到匹配的用户</div>';
            return;
        }
        
        userList.innerHTML = users.map(user => `
            <div class="list-item">
                <div>
                    <h4>${user.username}</h4>
                    <p>邮箱: ${user.email || '未设置'}</p>
                    <p>入职日期: ${user.hire_date || '未设置'}</p>
                </div>
                <div class="item-actions">
                    <button class="btn secondary" onclick="editUser(${user.id})">编辑</button>
                    <button class="btn danger" onclick="deleteUser(${user.id})">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        alert('搜索用户失败: ' + error.message);
    }
}

// 处理搜索记录
async function handleSearchRecord() {
    const searchTerm = document.getElementById('record-search').value;
    try {
        const records = await api.searchTimeRecords(searchTerm);
        const recordList = document.getElementById('admin-record-list');
        
        if (records.length === 0) {
            recordList.innerHTML = '<div class="record-item">未找到匹配的记录</div>';
            return;
        }
        
        recordList.innerHTML = records.map(record => `
            <div class="record-item">
                <div class="record-header">
                    <div class="record-user">用户ID: ${record.user_id} (${record.username || '未知用户'})</div>
                    <div class="record-date">${new Date(record.start_time).toLocaleString()}</div>
                </div>
                <div class="record-details">
                    <div>班别: <span class="record-shift ${record.shift_type === '白班' ? 'day' : 'night'}">${record.shift_type}</span></div>
                    <div>工时: ${record.duration / 60} 小时</div>
                    <div>是否请假: ${record.is_leave ? '是' : '否'}</div>
                    <div>描述: ${record.description || '无'}</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        alert('搜索记录失败: ' + error.message);
    }
}

// 编辑工资配置
async function editSalaryConfig(configId) {
    try {
        const config = await api.getSalaryConfigById(configId);
        
        const content = `
            <form id="edit-salary-config-form">
                <input type="hidden" id="edit-config-id" value="${config.id}">
                <div class="form-group">
                    <label for="edit-config-key">配置键</label>
                    <input type="text" id="edit-config-key" value="${config.config_key}" readonly>
                </div>
                <div class="form-group">
                    <label for="edit-config-value">配置值</label>
                    <input type="text" id="edit-config-value" value="${config.config_value}" required>
                </div>
                <div class="form-group">
                    <label for="edit-config-description">描述</label>
                    <textarea id="edit-config-description" rows="3">${config.description || ''}</textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('编辑工资配置', content);
        
        // 绑定表单提交事件
        document.getElementById('edit-salary-config-form').addEventListener('submit', handleEditSalaryConfig);
    } catch (error) {
        alert('获取配置信息失败: ' + error.message);
    }
}

// 处理编辑工资配置
async function handleEditSalaryConfig(e) {
    e.preventDefault();
    
    const configKey = document.getElementById('edit-config-key').value;
    const configValue = document.getElementById('edit-config-value').value;
    const description = document.getElementById('edit-config-description').value;
    
    try {
        await api.updateSalaryConfig({ config_key: configKey, config_value: configValue, description });
        closeModal();
        loadSalaryConfig();
        alert('工资配置更新成功');
    } catch (error) {
        alert('更新工资配置失败: ' + error.message);
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', initAdminSystem);

// 加载每日出勤报表
async function loadDailyAttendanceReport() {
    // 设置默认日期范围为今天
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('daily-report-start-date').value = today;
    document.getElementById('daily-report-end-date').value = today;
    
    // 绑定生成报表按钮事件
    const generateBtn = document.getElementById('generate-daily-report-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateDailyAttendanceReport);
    }
    
    // 绑定批量修改记录按钮事件
    const batchEditBtn = document.getElementById('batch-edit-records-btn');
    if (batchEditBtn) {
        batchEditBtn.addEventListener('click', batchEditRecords);
    }
    
    // 绑定批量删除记录按钮事件
    const batchDeleteBtn = document.getElementById('batch-delete-records-btn');
    if (batchDeleteBtn) {
        batchDeleteBtn.addEventListener('click', batchDeleteRecords);
    }
    
    // 绑定批量添加记录按钮事件
    const batchAddBtn = document.getElementById('batch-add-records-btn');
    if (batchAddBtn) {
        batchAddBtn.addEventListener('click', batchAddRecords);
    }
    
    // 加载角色选项到筛选下拉框
    try {
        const roles = await api.getRoles();
        const roleSelect = document.getElementById('daily-report-role-select');
        roleSelect.innerHTML = '<option value="">所有角色</option>';
        roles.forEach(role => {
            const option = document.createElement('option');
            option.value = role.id;
            option.textContent = role.name;
            roleSelect.appendChild(option);
        });
    } catch (error) {
        console.error('加载角色选项失败:', error);
    }
}

// 批量修改记录
async function batchEditRecords() {
    try {
        // 获取所有角色信息
        const roles = await api.getRoles();
        
        const content = `
            <form id="batch-edit-form">
                <div class="form-group">
                    <label for="batch-role-select">选择角色</label>
                    <select id="batch-role-select" required>
                        <option value="">所有角色</option>
                        ${roles.map(role => `<option value="${role.id}">${role.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-shift-type">班别</label>
                    <select id="batch-shift-type">
                        <option value="">不修改</option>
                        <option value="白班">白班</option>
                        <option value="夜班">夜班</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-hours">工时</label>
                    <input type="number" id="batch-hours" step="0.5" placeholder="不修改">
                </div>
                <div class="form-group">
                    <label for="batch-is-leave">是否请假</label>
                    <select id="batch-is-leave">
                        <option value="">不修改</option>
                        <option value="true">是</option>
                        <option value="false">否</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-leave-hours">请假时间</label>
                    <input type="number" id="batch-leave-hours" step="0.5" placeholder="不修改">
                </div>
                <div class="form-group">
                    <label for="batch-status">状态</label>
                    <input type="text" id="batch-status" placeholder="不修改">
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">执行批量修改</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('批量修改记录', content);
        
        // 绑定表单提交事件
        document.getElementById('batch-edit-form').addEventListener('submit', handleBatchEditRecords);
    } catch (error) {
        alert('获取角色列表失败: ' + error.message);
    }
}

// 处理批量修改记录
async function handleBatchEditRecords(e) {
    e.preventDefault();
    
    const roleId = document.getElementById('batch-role-select').value;
    const shiftType = document.getElementById('batch-shift-type').value;
    const hours = document.getElementById('batch-hours').value;
    const isLeave = document.getElementById('batch-is-leave').value;
    const leaveHours = document.getElementById('batch-leave-hours').value;
    const status = document.getElementById('batch-status').value;
    
    const startDate = document.getElementById('daily-report-start-date').value;
    const endDate = document.getElementById('daily-report-end-date').value;
    
    if (!startDate || !endDate) {
        alert('请先选择日期范围并生成报表');
        return;
    }
    
    try {
        // 构建批量修改数据
        const batchData = {
            role_id: roleId ? parseInt(roleId) : null,
            shift_type: shiftType || null,
            hours: hours ? parseFloat(hours) : null,
            is_leave: isLeave !== '' ? (isLeave === 'true') : null,
            leave_hours: leaveHours ? parseFloat(leaveHours) : null,
            status: status || null,
            start_date: startDate,
            end_date: endDate
        };
        
        // 调用API执行批量修改
        await api.batchUpdateTimeRecords(batchData);
        
        closeModal();
        // 重新生成报表
        generateDailyAttendanceReport();
        alert('批量修改成功');
    } catch (error) {
        alert('批量修改失败: ' + error.message);
    }
}

// 批量删除记录
async function batchDeleteRecords() {
    try {
        // 获取所有角色信息
        const roles = await api.getRoles();
        
        const content = `
            <form id="batch-delete-form">
                <div class="form-group">
                    <label for="batch-delete-role-select">选择角色</label>
                    <select id="batch-delete-role-select">
                        <option value="">所有角色</option>
                        ${roles.map(role => `<option value="${role.id}">${role.name}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-delete-start-date">开始日期</label>
                    <input type="date" id="batch-delete-start-date" required>
                </div>
                <div class="form-group">
                    <label for="batch-delete-end-date">结束日期</label>
                    <input type="date" id="batch-delete-end-date" required>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn danger">执行批量删除</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('批量删除记录', content);
        
        // 设置默认日期范围
        const startDate = document.getElementById('daily-report-start-date').value;
        const endDate = document.getElementById('daily-report-end-date').value;
        document.getElementById('batch-delete-start-date').value = startDate;
        document.getElementById('batch-delete-end-date').value = endDate;
        
        // 绑定表单提交事件
        document.getElementById('batch-delete-form').addEventListener('submit', handleBatchDeleteRecords);
    } catch (error) {
        alert('获取角色列表失败: ' + error.message);
    }
}

// 处理批量删除记录
async function handleBatchDeleteRecords(e) {
    e.preventDefault();
    
    const roleId = document.getElementById('batch-delete-role-select').value;
    const startDate = document.getElementById('batch-delete-start-date').value;
    const endDate = document.getElementById('batch-delete-end-date').value;
    
    if (!startDate || !endDate) {
        alert('请选择开始日期和结束日期');
        return;
    }
    
    if (!confirm('确定要批量删除所选记录吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        // 构建批量删除数据
        const batchData = {
            role_id: roleId ? parseInt(roleId) : null,
            start_date: startDate,
            end_date: endDate
        };
        
        // 调用API执行批量删除
        await api.batchDeleteTimeRecords(batchData);
        
        closeModal();
        // 重新生成报表
        generateDailyAttendanceReport();
        alert('批量删除成功');
    } catch (error) {
        alert('批量删除失败: ' + error.message);
    }
}

// 批量添加记录
async function batchAddRecords() {
    try {
        // 获取所有角色和用户信息
        const [roles, users] = await Promise.all([
            api.getRoles(),
            api.getAllUsers()
        ]);
        
        const rolesOptions = roles.map(role => `<option value="${role.id}">${role.name}</option>`).join('');
        const usersOptions = users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
        
        const content = `
            <form id="batch-add-form">
                <div class="form-group">
                    <label for="batch-add-role-select">选择角色（可选）</label>
                    <select id="batch-add-role-select">
                        <option value="">不按角色选择</option>
                        ${rolesOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-add-user-select">选择用户（可多选）</label>
                    <select id="batch-add-user-select" multiple style="height: 150px;">
                        ${usersOptions}
                    </select>
                    <small>按住Ctrl键可选择多个用户</small>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="batch-add-start-date">开始日期</label>
                        <input type="date" id="batch-add-start-date" required>
                    </div>
                    <div class="form-group">
                        <label for="batch-add-end-date">结束日期</label>
                        <input type="date" id="batch-add-end-date" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="batch-add-shift-type">班别</label>
                        <select id="batch-add-shift-type" required>
                            <option value="白班">白班</option>
                            <option value="夜班">夜班</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="batch-add-hours">工时</label>
                        <input type="number" id="batch-add-hours" step="0.5" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="batch-add-is-leave">是否请假</label>
                    <select id="batch-add-is-leave">
                        <option value="false">否</option>
                        <option value="true">是</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="batch-add-description">描述</label>
                    <textarea id="batch-add-description" rows="3"></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">执行批量添加</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('批量添加记录', content);
        
        // 设置默认日期范围
        const startDate = document.getElementById('daily-report-start-date').value;
        const endDate = document.getElementById('daily-report-end-date').value;
        document.getElementById('batch-add-start-date').value = startDate;
        document.getElementById('batch-add-end-date').value = endDate;
        
        // 绑定表单提交事件
        document.getElementById('batch-add-form').addEventListener('submit', handleBatchAddRecords);
    } catch (error) {
        alert('获取角色和用户列表失败: ' + error.message);
    }
}

// 处理批量添加记录
async function handleBatchAddRecords(e) {
    e.preventDefault();
    
    const roleId = document.getElementById('batch-add-role-select').value;
    const userSelect = document.getElementById('batch-add-user-select');
    const selectedUserIds = Array.from(userSelect.selectedOptions).map(option => parseInt(option.value));
    const startDate = document.getElementById('batch-add-start-date').value;
    const endDate = document.getElementById('batch-add-end-date').value;
    const shiftType = document.getElementById('batch-add-shift-type').value;
    const hours = document.getElementById('batch-add-hours').value;
    const isLeave = document.getElementById('batch-add-is-leave').value === 'true';
    const description = document.getElementById('batch-add-description').value;
    
    if (!startDate || !endDate || !hours) {
        alert('请填写完整的日期范围和工时');
        return;
    }
    
    if (!roleId && selectedUserIds.length === 0) {
        alert('请选择角色或用户');
        return;
    }
    
    try {
        let targetUsers = [];
        
        // 如果选择了角色，获取该角色下的所有用户
        if (roleId) {
            const roleUsers = await api.getUsersByRole(roleId);
            targetUsers = roleUsers.map(user => user.id);
        } else {
            // 否则使用手动选择的用户
            targetUsers = selectedUserIds;
        }
        
        // 去重
        targetUsers = [...new Set(targetUsers)];
        
        if (targetUsers.length === 0) {
            alert('没有找到符合条件的用户');
            return;
        }
        
        // 构建批量添加数据
        const batchData = {
            users: targetUsers,
            start_date: startDate,
            end_date: endDate,
            shift_type: shiftType,
            hours: parseFloat(hours),
            is_leave: isLeave,
            description: description
        };
        
        // 调用API执行批量添加
        await api.batchAddTimeRecords(batchData);
        
        closeModal();
        // 重新生成报表
        generateDailyAttendanceReport();
        alert('批量添加成功');
    } catch (error) {
        alert('批量添加失败: ' + error.message);
    }
}

// 生成每日出勤报表
async function generateDailyAttendanceReport() {
    const startDate = document.getElementById('daily-report-start-date').value;
    const endDate = document.getElementById('daily-report-end-date').value;
    const roleId = document.getElementById('daily-report-role-select').value;
    
    if (!startDate || !endDate) {
        alert('请选择开始日期和结束日期');
        return;
    }
    
    try {
        const reportList = document.getElementById('daily-report-list');
        const generateBtn = document.getElementById('generate-daily-report-btn');
        
        // 显示加载状态
        reportList.innerHTML = '<div class="loading">加载中...</div>';
        generateBtn.disabled = true;
        generateBtn.textContent = '加载中...';
        
        // 获取所有用户
        const users = await api.getAllUsers();
        console.log('获取到的用户列表:', users);
        
        // 获取所有角色信息
        const roles = await api.getRoles();
        const rolesDict = {};
        for (const role of roles) {
            rolesDict[role.id] = role;
        }
        
        // 使用修复后的API方法获取指定日期范围的所有用户工时记录，支持按角色筛选
        console.log('调用API获取工时记录，日期范围:', startDate, '至', endDate, '角色ID:', roleId);
        const timeRecords = await api.getDailyAttendanceReport(startDate, endDate, roleId);
        console.log('获取到的工时记录:', timeRecords);
        
        // 构建用户字典，包含角色信息
        const usersDict = {};
        for (const user of users) {
            // 用户和角色是多对多关系，获取用户的所有角色名称
            const userRoles = user.role_ids || [];
            const roleNames = userRoles
                .map(roleId => rolesDict[roleId]?.name)
                .filter(name => name) // 过滤掉不存在的角色
                .join(', ');
            
            usersDict[user.id] = {
                ...user,
                role_name: roleNames || '无角色'
            };
        }
        
        // 构建工时记录字典，按用户ID和日期分组
        const recordsByUserDate = {};
        for (const record of timeRecords) {
            const recordDate = new Date(record.start_time).toISOString().split('T')[0];
            const key = `${record.user_id}_${recordDate}`;
            recordsByUserDate[key] = record;
        }
        
        // 根据选择的角色筛选用户，用户和角色是多对多关系，检查user.role_ids数组中是否包含所选角色ID
        const filteredUsers = roleId ? users.filter(user => user.role_ids && user.role_ids.includes(parseInt(roleId))) : users;
        
        // 生成报表数据
        let reportHTML = '<table class="report-table">';
        reportHTML += '<thead><tr><th>用户ID</th><th>用户名</th><th>角色</th><th>日期</th><th>班别</th><th>工时</th><th>是否请假</th><th>请假时间</th><th>状态</th><th>操作</th></tr></thead>';
        reportHTML += '<tbody>';
        
        // 直接从工时记录中生成报表，不再遍历所有用户和日期
        // 工时记录已经通过API按角色筛选过，所以只需要遍历这些记录
        for (const record of timeRecords) {
            const recordDate = new Date(record.start_time).toISOString().split('T')[0];
            const user = usersDict[record.user_id];
            
            if (!user) continue;
            
            // 计算工时（小时），将分钟转换为小时
            const hours = record.duration ? (record.duration / 60).toFixed(1) : 0;
            
            reportHTML += `<tr data-user-id="${record.user_id}" data-record-id="${record.id || ''}" data-date="${recordDate}">`;
            reportHTML += `<td>${record.user_id}</td>`;
            reportHTML += `<td>${user.username}</td>`;
            reportHTML += `<td>${user.role_name}</td>`;
            reportHTML += `<td>${recordDate}</td>`;
            reportHTML += `<td>${record.shift_type || ''}</td>`;
            reportHTML += `<td>${hours}</td>`;
            reportHTML += `<td>${record.is_leave ? '是' : '否'}</td>`;
            reportHTML += `<td>${record.leave_hours || 0}</td>`;
            reportHTML += `<td>${record.status || '正常'}</td>`;
            reportHTML += '<td class="action-buttons">';
            reportHTML += `<button class="btn secondary edit-record" onclick="editAttendanceRecord(${record.user_id}, '${recordDate}', ${record.id || 'null'})">编辑</button>`;
            reportHTML += `<button class="btn danger delete-record" onclick="deleteAttendanceRecord(${record.id || 'null'}, ${record.user_id}, '${recordDate}')">删除</button>`;
            reportHTML += '</td>';
            reportHTML += '</tr>';
        }
        
        reportHTML += '</tbody></table>';
        
        // 统计汇总信息
        let dayShiftCount = 0;
        let nightShiftCount = 0;
        let leaveCount = 0;
        
        for (const record of timeRecords) {
            if (record.is_leave) {
                leaveCount++;
            } else if (record.shift_type === '白班') {
                dayShiftCount++;
            } else if (record.shift_type === '夜班') {
                nightShiftCount++;
            }
        }
        
        // 添加汇总信息
        reportHTML += '<div class="report-summary">';
        reportHTML += '<h3>统计汇总</h3>';
        reportHTML += '<div class="summary-stats">';
        reportHTML += `<div class="stat-item"><span class="stat-label">白班人数:</span><span class="stat-value">${dayShiftCount}</span></div>`;
        reportHTML += `<div class="stat-item"><span class="stat-label">夜班人数:</span><span class="stat-value">${nightShiftCount}</span></div>`;
        reportHTML += `<div class="stat-item"><span class="stat-label">请假人数:</span><span class="stat-value">${leaveCount}</span></div>`;
        reportHTML += `<div class="stat-item"><span class="stat-label">总记录数:</span><span class="stat-value">${timeRecords.length}</span></div>`;
        reportHTML += '</div>';
        reportHTML += '</div>';
        
        // 更新报表列表
        reportList.innerHTML = reportHTML;
        
        // 更新报表列表
        reportList.innerHTML = reportHTML;
        
        // 恢复按钮状态
        generateBtn.disabled = false;
        generateBtn.textContent = '生成报表';
        
    } catch (error) {
        console.error('生成每日出勤报表失败:', error);
        alert('生成报表失败: ' + error.message);
        
        // 恢复按钮状态
        const generateBtn = document.getElementById('generate-daily-report-btn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = '生成报表';
        }
    }
}

// 显示添加出勤记录模态框
function showAddAttendanceRecordModal(date) {
    // 获取所有用户
    api.getAllUsers().then(users => {
        const content = `
            <form id="add-attendance-form">
                <input type="hidden" id="add-record-date" value="${date}">
                <div class="form-group">
                    <label for="add-record-user">用户</label>
                    <select id="add-record-user" required>
                        ${users.map(user => `<option value="${user.id}">${user.username}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="add-record-shift">班别</label>
                    <select id="add-record-shift" required>
                        <option value="白班">白班</option>
                        <option value="夜班">夜班</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="add-record-hours">工时</label>
                    <input type="number" id="add-record-hours" step="0.5" required>
                </div>
                <div class="form-group">
                    <label for="add-record-is-leave">是否请假</label>
                    <select id="add-record-is-leave" required>
                        <option value="false">否</option>
                        <option value="true">是</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="add-record-leave-hours">请假时间</label>
                    <input type="number" id="add-record-leave-hours" step="0.5" value="0">
                </div>
                <div class="form-group">
                    <label for="add-record-status">状态</label>
                    <input type="text" id="add-record-status" value="正常">
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('添加出勤记录', content);
        
        // 绑定表单提交事件
        document.getElementById('add-attendance-form').addEventListener('submit', handleAddAttendanceRecord);
    }).catch(error => {
        alert('获取用户列表失败: ' + error.message);
    });
}

// 处理添加出勤记录
async function handleAddAttendanceRecord(e) {
    e.preventDefault();
    
    const date = document.getElementById('add-record-date').value;
    const userId = document.getElementById('add-record-user').value;
    const shiftType = document.getElementById('add-record-shift').value;
    const hours = document.getElementById('add-record-hours').value;
    const isLeave = document.getElementById('add-record-is-leave').value === 'true';
    const leaveHours = document.getElementById('add-record-leave-hours').value;
    const status = document.getElementById('add-record-status').value;
    
    try {
        // 添加新记录前，检查该用户在当天是否已经有出勤记录
        // 使用adminAPI中的getDailyAttendanceReport方法获取指定日期的所有工时记录
        const timeRecords = await api.getDailyAttendanceReport(date, date);
        
        // 检查是否已经存在该用户的记录
        const existingRecord = timeRecords.find(record => record.user_id === parseInt(userId));
        if (existingRecord) {
            alert('该用户在当天已经有出勤记录，不能重复添加');
            return;
        }
        
        // 构建开始时间和结束时间
        const start_time = `${date}T08:00:00`;
        const end_time = `${date}T18:00:00`;
        
        // 调用API添加记录
        await api.createTimeRecord({
            user_id: parseInt(userId),
            start_time: start_time,
            end_time: end_time,
            duration: parseFloat(hours) * 60, // 将小时转换为分钟
            shift_type: shiftType,
            is_leave: isLeave,
            description: status
        });
        
        closeModal();
        // 重新生成报表
        generateDailyAttendanceReport();
        alert('记录添加成功');
    } catch (error) {
        alert('添加记录失败: ' + error.message);
    }
}

// 编辑出勤记录
function editAttendanceRecord(userId, date, recordId) {
    // 获取用户信息和记录信息
    Promise.all([
        api.getAllUsers(),
        recordId ? api.getTimeRecord(recordId) : Promise.resolve(null)
    ]).then(([users, record]) => {
        // 计算工时（小时），将分钟转换为小时
        const recordHours = record ? (record.duration / 60).toFixed(1) : 0;
        
        const content = `
            <form id="edit-attendance-form">
                <input type="hidden" id="edit-record-id" value="${recordId || ''}">
                <input type="hidden" id="edit-record-date" value="${date}">
                <div class="form-group">
                    <label for="edit-record-user">用户</label>
                    <select id="edit-record-user" required>
                        ${users.map(user => `<option value="${user.id}" ${user.id === userId ? 'selected' : ''}>${user.username}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="edit-record-shift">班别</label>
                    <select id="edit-record-shift" required>
                        <option value="白班" ${record && record.shift_type === '白班' ? 'selected' : ''}>白班</option>
                        <option value="夜班" ${record && record.shift_type === '夜班' ? 'selected' : ''}>夜班</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="edit-record-hours">工时</label>
                    <input type="number" id="edit-record-hours" step="0.5" value="${recordHours}" required>
                </div>
                <div class="form-group">
                    <label for="edit-record-is-leave">是否请假</label>
                    <select id="edit-record-is-leave" required>
                        <option value="false" ${!record || !record.is_leave ? 'selected' : ''}>否</option>
                        <option value="true" ${record && record.is_leave ? 'selected' : ''}>是</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="edit-record-leave-hours">请假时间</label>
                    <input type="number" id="edit-record-leave-hours" step="0.5" value="${record ? record.leave_hours : 0}">
                </div>
                <div class="form-group">
                    <label for="edit-record-status">状态</label>
                    <input type="text" id="edit-record-status" value="${record ? record.description : '正常'}">
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn primary">保存</button>
                    <button type="button" class="btn secondary" onclick="closeModal()">取消</button>
                </div>
            </form>
        `;
        
        showModal('编辑出勤记录', content);
        
        // 绑定表单提交事件
        document.getElementById('edit-attendance-form').addEventListener('submit', handleEditAttendanceRecord);
    }).catch(error => {
        alert('获取记录信息失败: ' + error.message);
    });
}

// 处理编辑出勤记录
async function handleEditAttendanceRecord(e) {
    e.preventDefault();
    
    const recordId = document.getElementById('edit-record-id').value;
    const date = document.getElementById('edit-record-date').value;
    const userId = document.getElementById('edit-record-user').value;
    const shiftType = document.getElementById('edit-record-shift').value;
    const hours = document.getElementById('edit-record-hours').value;
    const isLeave = document.getElementById('edit-record-is-leave').value === 'true';
    const leaveHours = document.getElementById('edit-record-leave-hours').value;
    const status = document.getElementById('edit-record-status').value;
    
    try {
        if (recordId) {
            // 更新现有记录
            await api.updateTimeRecord(recordId, {
                shift_type: shiftType,
                duration: parseFloat(hours) * 60, // 将小时转换为分钟
                is_leave: isLeave,
                description: status
            });
        } else {
            // 添加新记录前，检查该用户在当天是否已经有出勤记录
            // 使用adminAPI中的getDailyAttendanceReport方法获取指定日期的所有工时记录
            const timeRecords = await api.getDailyAttendanceReport(date, date);
            
            // 检查是否已经存在该用户的记录
            const existingRecord = timeRecords.find(record => record.user_id === parseInt(userId));
            if (existingRecord) {
                alert('该用户在当天已经有出勤记录，不能重复添加');
                return;
            }
            
            // 构建开始时间和结束时间
            const start_time = `${date}T08:00:00`;
            const end_time = `${date}T18:00:00`;
            
            await api.createTimeRecord({
                user_id: parseInt(userId),
                start_time: start_time,
                end_time: end_time,
                duration: parseFloat(hours) * 60, // 将小时转换为分钟
                shift_type: shiftType,
                is_leave: isLeave,
                description: status
            });
        }
        
        closeModal();
        // 重新生成报表
        generateDailyAttendanceReport();
        alert('记录更新成功');
    } catch (error) {
        alert('更新记录失败: ' + error.message);
    }
}

// 删除出勤记录
async function deleteAttendanceRecord(recordId, userId, date) {
    if (!recordId) {
        alert('没有可删除的记录');
        return;
    }
    
    if (confirm('确定要删除这条记录吗？')) {
        try {
            await api.deleteRecord(recordId, userId);
            // 重新生成报表
            generateDailyAttendanceReport();
            alert('记录删除成功');
        } catch (error) {
            alert('删除记录失败: ' + error.message);
        }
    }
}

// 加载个人出勤报表
async function loadPersonalAttendanceReport() {
    // 设置默认日期为当前月份
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
    document.getElementById('personal-report-start-date').value = firstDay;
    document.getElementById('personal-report-end-date').value = lastDay;
    
    // 加载用户列表到下拉菜单
    try {
        const users = await api.getAllUsers();
        const userSelect = document.getElementById('personal-report-user');
        
        // 清空现有选项
        userSelect.innerHTML = '<option value="">请选择用户</option>';
        
        // 添加用户选项
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.username;
            userSelect.appendChild(option);
        });
    } catch (error) {
        console.error('加载用户列表失败:', error);
        alert('加载用户列表失败: ' + error.message);
    }
    
    // 绑定生成报表按钮事件
    const generateBtn = document.getElementById('generate-personal-report-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generatePersonalAttendanceReport);
    }
}

// 生成个人出勤报表
async function generatePersonalAttendanceReport() {
    const startDate = document.getElementById('personal-report-start-date').value;
    const endDate = document.getElementById('personal-report-end-date').value;
    const userId = document.getElementById('personal-report-user').value;
    
    if (!startDate || !endDate || !userId) {
        alert('请选择完整的日期范围和用户');
        return;
    }
    
    try {
        const reportList = document.getElementById('personal-report-list');
        const generateBtn = document.getElementById('generate-personal-report-btn');
        
        // 显示加载状态
        reportList.innerHTML = '<div class="loading">加载中...</div>';
        generateBtn.disabled = true;
        generateBtn.textContent = '加载中...';
        
        // 获取个人出勤记录
        const records = await api.getPersonalAttendanceReport(userId, startDate, endDate);
        console.log('获取到的个人出勤记录:', records);
        console.log('第一个记录的结构:', records[0]);
        console.log('第一个记录的start_time:', records[0]?.start_time);
        
        // 初始化统计变量
        let dayShiftCount = 0;
        let nightShiftCount = 0;
        let leaveCount = 0;
        
        // 生成报表数据
        let reportHTML = '<table class="report-table">';
        reportHTML += '<thead><tr><th>日期</th><th>班别</th><th>工时</th><th>是否请假</th><th>请假时间</th><th>状态</th></tr></thead>';
        reportHTML += '<tbody>';
        
        // 遍历所有记录，生成报表行
        for (const record of records) {
            // 计算工时（小时），将分钟转换为小时
            const hours = record.duration ? (record.duration / 60).toFixed(1) : 0;
            
            // 从start_time中提取日期，添加错误处理
            let recordDate = '';
            if (record.start_time) {
                try {
                    const dateObj = new Date(record.start_time);
                    if (!isNaN(dateObj.getTime())) {
                        recordDate = dateObj.toISOString().split('T')[0];
                    } else {
                        console.error('无效的日期格式:', record.start_time);
                        recordDate = '无效日期';
                    }
                } catch (e) {
                    console.error('日期解析错误:', e);
                    recordDate = '解析错误';
                }
            } else {
                console.error('记录缺少start_time字段:', record);
                recordDate = '无日期';
            }
            
            // 更新统计数据
            if (record.is_leave) {
                leaveCount++;
            } else if (record.shift_type === '白班') {
                dayShiftCount++;
            } else if (record.shift_type === '夜班') {
                nightShiftCount++;
            }
            
            reportHTML += `<tr>`;
            reportHTML += `<td>${recordDate}</td>`;
            reportHTML += `<td>${record.shift_type || ''}</td>`;
            reportHTML += `<td>${hours}</td>`;
            reportHTML += `<td>${record.is_leave ? '是' : '否'}</td>`;
            reportHTML += `<td>${record.leave_hours || 0}</td>`;
            reportHTML += `<td>${record.description || '正常'}</td>`;
            reportHTML += '</tr>';
        }
        
        reportHTML += '</tbody></table>';
        
        // 更新报表列表
        reportList.innerHTML = reportHTML;
        
        // 恢复按钮状态
        generateBtn.disabled = false;
        generateBtn.textContent = '生成报表';
        
    } catch (error) {
        console.error('生成个人出勤报表失败:', error);
        alert('生成报表失败: ' + error.message);
        
        // 恢复按钮状态
        const generateBtn = document.getElementById('generate-personal-report-btn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = '生成报表';
        }
    }
}

// 加载排班报表
async function loadSchedulerReport() {
    // 设置默认日期为当前月份
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
    document.getElementById('scheduler-report-start-date').value = firstDay;
    document.getElementById('scheduler-report-end-date').value = lastDay;
    
    // 绑定生成报表按钮事件
    const generateBtn = document.getElementById('generate-scheduler-report-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateSchedulerReport);
    }
}

// 生成排班报表
async function generateSchedulerReport() {
    const startDate = document.getElementById('scheduler-report-start-date').value;
    const endDate = document.getElementById('scheduler-report-end-date').value;
    
    if (!startDate || !endDate) {
        alert('请选择完整的日期范围');
        return;
    }
    
    try {
        const reportList = document.getElementById('scheduler-report-list');
        const generateBtn = document.getElementById('generate-scheduler-report-btn');
        
        // 显示加载状态
        reportList.innerHTML = '<div class="loading">加载中...</div>';
        generateBtn.disabled = true;
        generateBtn.textContent = '加载中...';
        
        // 获取排班记录
        const schedules = await api.getSchedulerReport(startDate, endDate);
        
        // 生成报表数据
        let reportHTML = '<table class="report-table">';
        reportHTML += '<thead><tr><th>用户ID</th><th>用户名</th><th>开始日期</th><th>结束日期</th><th>班别</th><th>工时</th><th>描述</th></tr></thead>';
        reportHTML += '<tbody>';
        
        // 遍历所有排班，生成报表行
        for (const schedule of schedules) {
            reportHTML += `<tr>`;
            reportHTML += `<td>${schedule.user_id}</td>`;
            reportHTML += `<td>${schedule.username || '未知用户'}</td>`;
            reportHTML += `<td>${schedule.start_date}</td>`;
            reportHTML += `<td>${schedule.end_date}</td>`;
            reportHTML += `<td>${schedule.shift_type}</td>`;
            reportHTML += `<td>${schedule.hours}</td>`;
            reportHTML += `<td>${schedule.description || '无'}</td>`;
            reportHTML += '</tr>';
        }
        
        reportHTML += '</tbody></table>';
        
        // 更新报表列表
        reportList.innerHTML = reportHTML;
        
        // 恢复按钮状态
        generateBtn.disabled = false;
        generateBtn.textContent = '生成报表';
        
    } catch (error) {
        console.error('生成排班报表失败:', error);
        alert('生成报表失败: ' + error.message);
        
        // 恢复按钮状态
        const generateBtn = document.getElementById('generate-scheduler-report-btn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = '生成报表';
        }
    }
}

// 加载登录报表
async function loadLoginReport() {
    try {
        const reportList = document.getElementById('login-report-list');
        
        // 显示加载状态
        reportList.innerHTML = '<div class="loading">加载中...</div>';
        
        // 获取登录记录
        const response = await api.getUserLoginLogs();
        console.log('获取到的登录记录响应:', response);
        
        // 从响应中提取logs数组，确保logs是可迭代的数组
        const logsArray = Array.isArray(response.logs) ? response.logs : [];
        console.log('处理后的登录记录数组:', logsArray);
        
        // 生成报表数据
        let reportHTML = '<table class="report-table">';
        reportHTML += '<thead><tr><th>用户ID</th><th>用户名</th><th>登录时间</th><th>IP地址</th></tr></thead>';
        reportHTML += '<tbody>';
        
        // 遍历所有登录记录，生成报表行
        for (const log of logsArray) {
            // 处理登录时间
            let loginTime = '未知时间';
            if (log.login_time) {
                try {
                    loginTime = new Date(log.login_time).toLocaleString();
                } catch (e) {
                    loginTime = log.login_time || '未知时间';
                }
            }
            
            reportHTML += `<tr>`;
            reportHTML += `<td>${log.user_id}</td>`;
            reportHTML += `<td>${log.username || '未知用户'}</td>`;
            reportHTML += `<td>${loginTime}</td>`;
            reportHTML += `<td>${log.ip_address || '无'}</td>`;
            reportHTML += '</tr>';
        }
        
        // 如果没有登录记录
        if (logsArray.length === 0) {
            reportHTML += '<tr><td colspan="4" style="text-align: center;">暂无登录记录</td></tr>';
        }
        
        reportHTML += '</tbody></table>';
        
        // 更新报表列表
        reportList.innerHTML = reportHTML;
        
    } catch (error) {
        console.error('加载登录报表失败:', error);
        const reportList = document.getElementById('login-report-list');
        reportList.innerHTML = '<div class="error">加载登录报表失败: ' + error.message + '</div>';
    }
}



// 加载在线用户报表
async function loadOnlineUsersReport() {
    // 绑定刷新按钮事件
    const refreshBtn = document.getElementById('refresh-online-users-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadOnlineUsersReport);
    }
    
    try {
        const reportList = document.getElementById('online-users-list');
        const refreshBtn = document.getElementById('refresh-online-users-btn');
        
        // 显示加载状态
        reportList.innerHTML = '<div class="loading">加载中...</div>';
        refreshBtn.disabled = true;
        refreshBtn.textContent = '刷新中...';
        
        // 获取在线用户
        const onlineUsers = await api.getOnlineUsers();
        
        // 生成报表数据
        let reportHTML = '<table class="report-table">';
        reportHTML += '<thead><tr><th>用户ID</th><th>用户名</th><th>登录时间</th><th>IP地址</th><th>在线时长</th></tr></thead>';
        reportHTML += '<tbody>';
        
        // 遍历所有在线用户，生成报表行
        for (const user of onlineUsers) {
            // 处理登录时间
            let loginTime = '未知时间';
            if (user.last_visit_time) {
                try {
                    loginTime = new Date(user.last_visit_time).toLocaleString();
                } catch (e) {
                    loginTime = user.last_visit_time || '未知时间';
                }
            } else if (user.login_time) {
                try {
                    loginTime = new Date(user.login_time).toLocaleString();
                } catch (e) {
                    loginTime = user.login_time || '未知时间';
                }
            }
            
            reportHTML += `<tr>`;
            reportHTML += `<td>${user.user_id}</td>`;
            reportHTML += `<td>${user.username || '未知用户'}</td>`;
            reportHTML += `<td>${loginTime}</td>`;
            reportHTML += `<td>${user.ip_address || '无'}</td>`;
            reportHTML += `<td>${user.online_duration || '0 分钟'}</td>`;
            reportHTML += '</tr>';
        }
        
        reportHTML += '</tbody></table>';
        
        // 更新报表列表
        reportList.innerHTML = reportHTML;
        
        // 恢复按钮状态
        refreshBtn.disabled = false;
        refreshBtn.textContent = '刷新';
        
    } catch (error) {
        console.error('加载在线用户报表失败:', error);
        alert('加载报表失败: ' + error.message);
        
        // 恢复按钮状态
        const refreshBtn = document.getElementById('refresh-online-users-btn');
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.textContent = '刷新';
        }
    }
}