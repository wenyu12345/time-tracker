// 认证相关逻辑

// 本地存储键名
const USER_KEY = 'current_user';

// 获取当前用户
function getCurrentUser() {
    const userJson = localStorage.getItem(USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
}

// 设置当前用户
function setCurrentUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// 移除当前用户
function removeCurrentUser() {
    localStorage.removeItem(USER_KEY);
}

// 检查用户是否已登录
function isLoggedIn() {
    return !!getCurrentUser();
}

// 更新用户信息显示
async function updateUserInfo() {
    const user = getCurrentUser();
    const userInfoDiv = document.getElementById('user-info');
    const authSection = document.querySelector('.auth-section');
    
    if (user && userInfoDiv) {
        try {
            // 从服务器获取最新的用户信息
            const latestUser = await authAPI.getUser(user.id);
            
            // 打印调试信息
            console.log('从服务器获取的最新用户信息:', latestUser);
            
            // 更新本地存储中的用户信息
            setCurrentUser(latestUser);
            
            // 计算实际工龄
            let seniority = 0;
            if (latestUser.hire_date) {
                const hireDate = new Date(latestUser.hire_date);
                const now = new Date();
                let years = now.getFullYear() - hireDate.getFullYear();
                
                // 计算工龄，每年7月加一年
                if (now.getMonth() < 6) {
                    years -= 1;
                } else {
                    if (hireDate.getMonth() > now.getMonth() || 
                        (hireDate.getMonth() === now.getMonth() && hireDate.getDate() > now.getDate())) {
                        years -= 1;
                    }
                }
                
                // 直接使用计算出的工龄，不再减去第一年
                // 确保工龄不为负数
                seniority = Math.max(0, years);
            }
            
            // 显示用户信息
        userInfoDiv.innerHTML = `
                <div class="user-info-item">
                    <span class="user-label">用户名</span>
                    <span class="user-value">${latestUser.username}</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">邮箱</span>
                    <span class="user-value">${latestUser.email || '未设置'}</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">入职日期</span>
                    <span class="user-value">${latestUser.hire_date || '未设置'}</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">工龄</span>
                    <span class="user-value">${seniority}年</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">工龄奖</span>
                    <span class="user-value">${latestUser.seniority_bonus || 0}元/月</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">薪级</span>
                    <div class="salary-level-input">
                        <select id="salary-level-select">
                            <!-- E级薪级（E8到E19） -->
                            ${Array.from({length: 12}, (_, i) => i + 8).map(level => 
                                `<option value="E${level}" ${latestUser.salary_level === `E${level}` ? 'selected' : ''}>E${level}</option>`
                            ).join('')}
                            <!-- D级薪级（D1到D10） -->
                            ${Array.from({length: 10}, (_, i) => i + 1).map(level => 
                                `<option value="D${level}" ${latestUser.salary_level === `D${level}` ? 'selected' : ''}>D${level}</option>`
                            ).join('')}
                        </select>
                        <button id="save-salary-level-btn" class="btn primary small">保存</button>
                    </div>
                </div>
                <button id="change-password-show-btn" class="btn primary small">修改密码</button>
                <button id="logout-btn" class="btn secondary">退出登录</button>
            `;
            
            // 添加保存薪级事件
            const saveSalaryLevelBtn = document.getElementById('save-salary-level-btn');
            if (saveSalaryLevelBtn) {
                saveSalaryLevelBtn.addEventListener('click', async function() {
                    const salaryLevelSelect = document.getElementById('salary-level-select');
                    const newSalaryLevel = salaryLevelSelect.value;
                    
                    try {
                        await authAPI.updateSalaryLevel(latestUser.id, newSalaryLevel);
                        alert('薪级保存成功');
                        // 刷新用户信息
                        await updateUserInfo();
                        // 刷新工资计算页面的薪级
                        if (typeof initSalaryCalculation === 'function') {
                            await initSalaryCalculation();
                        }
                        // 自动更新salary_info表中的薪级
                        if (typeof saveSalaryInfo === 'function') {
                            await saveSalaryInfo();
                        }
                    } catch (error) {
                        console.error('保存薪级失败:', error);
                        alert('保存薪级失败: ' + error.message);
                    }
                });
            }
            
            // 添加修改密码按钮事件
            const changePasswordShowBtn = document.getElementById('change-password-show-btn');
            if (changePasswordShowBtn) {
                changePasswordShowBtn.addEventListener('click', function() {
                    // 显示修改密码表单
                    document.getElementById('change-password-form').style.display = 'block';
                    // 隐藏用户信息
                    userInfoDiv.style.display = 'none';
                });
            }
            
            // 隐藏认证表单
            if (authSection) {
                authSection.style.display = 'none';
            }
            
            // 控制管理系统入口的显示，只有刘建账号显示
            const adminEntrySection = document.querySelector('.admin-entry-section');
            if (adminEntrySection) {
                if (latestUser.username === '刘建') {
                    adminEntrySection.style.display = 'block';
                    // 手动调用initAdminEntry函数，确保按钮点击事件被正确添加
                    if (typeof initAdminEntry === 'function') {
                        initAdminEntry();
                    }
                } else {
                    adminEntrySection.style.display = 'none';
                }
            }
            
            // 添加退出登录事件
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', function() {
                    removeCurrentUser();
                    window.location.reload();
                });
            }
            
            // 初始化修改密码功能
            initChangePassword();
        } catch (error) {
            console.error('获取用户信息失败:', error);
            // 如果获取失败，使用本地存储的用户信息
            const localUser = getCurrentUser();
            
            // 打印调试信息
            console.log('使用本地存储的用户信息:', localUser);
            
            // 计算实际工龄
            let seniority = 0;
            if (localUser.hire_date) {
                const hireDate = new Date(localUser.hire_date);
                const now = new Date();
                let years = now.getFullYear() - hireDate.getFullYear();
                
                // 计算工龄，每年7月加一年
                if (now.getMonth() < 6) {
                    years -= 1;
                } else {
                    if (hireDate.getMonth() > now.getMonth() || 
                        (hireDate.getMonth() === now.getMonth() && hireDate.getDate() > now.getDate())) {
                        years -= 1;
                    }
                }
                
                // 直接使用计算出的工龄，不再减去第一年
                // 确保工龄不为负数
                seniority = Math.max(0, years);
            }
            
            // 显示用户信息
        userInfoDiv.innerHTML = `
                <div class="user-info-item">
                    <span class="user-label">用户名</span>
                    <span class="user-value">${localUser.username}</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">邮箱</span>
                    <span class="user-value">${localUser.email || '未设置'}</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">入职日期</span>
                    <span class="user-value">${localUser.hire_date || '未设置'}</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">工龄</span>
                    <span class="user-value">${seniority}年</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">工龄奖</span>
                    <span class="user-value">${localUser.seniority_bonus || 0}元/月</span>
                </div>
                <div class="user-info-item">
                    <span class="user-label">薪级</span>
                    <div class="salary-level-input">
                        <select id="salary-level-select">
                            <!-- E级薪级（E8到E19） -->
                            ${Array.from({length: 12}, (_, i) => i + 8).map(level => 
                                `<option value="E${level}" ${localUser.salary_level === `E${level}` ? 'selected' : ''}>E${level}</option>`
                            ).join('')}
                            <!-- D级薪级（D1到D10） -->
                            ${Array.from({length: 10}, (_, i) => i + 1).map(level => 
                                `<option value="D${level}" ${localUser.salary_level === `D${level}` ? 'selected' : ''}>D${level}</option>`
                            ).join('')}
                        </select>
                        <button id="save-salary-level-btn" class="btn primary small">保存</button>
                    </div>
                </div>
                <button id="change-password-show-btn" class="btn primary small">修改密码</button>
                <button id="logout-btn" class="btn secondary">退出登录</button>
            `;
            
            // 添加保存薪级事件
            const saveSalaryLevelBtn = document.getElementById('save-salary-level-btn');
            if (saveSalaryLevelBtn) {
                saveSalaryLevelBtn.addEventListener('click', async function() {
                    const salaryLevelSelect = document.getElementById('salary-level-select');
                    const newSalaryLevel = salaryLevelSelect.value;
                    
                    try {
                        await authAPI.updateSalaryLevel(localUser.id, newSalaryLevel);
                        alert('薪级保存成功');
                        // 刷新用户信息
                        await updateUserInfo();
                        // 刷新工资计算页面的薪级
                        if (typeof initSalaryCalculation === 'function') {
                            await initSalaryCalculation();
                        }
                        // 自动更新salary_info表中的薪级
                        if (typeof saveSalaryInfo === 'function') {
                            await saveSalaryInfo();
                        }
                    } catch (error) {
                        console.error('保存薪级失败:', error);
                        alert('保存薪级失败: ' + error.message);
                    }
                });
            }
            
            // 添加修改密码按钮事件
            const changePasswordShowBtn = document.getElementById('change-password-show-btn');
            if (changePasswordShowBtn) {
                changePasswordShowBtn.addEventListener('click', function() {
                    // 显示修改密码表单
                    document.getElementById('change-password-form').style.display = 'block';
                    // 隐藏用户信息
                    userInfoDiv.style.display = 'none';
                });
            }
            
            // 隐藏认证表单
            if (authSection) {
                authSection.style.display = 'none';
            }
            
            // 控制管理系统入口的显示，只有刘建账号显示
            const adminEntrySection = document.querySelector('.admin-entry-section');
            if (adminEntrySection) {
                if (localUser.username === '刘建') {
                    adminEntrySection.style.display = 'block';
                    // 手动调用initAdminEntry函数，确保按钮点击事件被正确添加
                    if (typeof initAdminEntry === 'function') {
                        initAdminEntry();
                    }
                } else {
                    adminEntrySection.style.display = 'none';
                }
            }
            
            // 添加退出登录事件
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', function() {
                    removeCurrentUser();
                    window.location.reload();
                });
            }
            
            // 初始化修改密码功能
            initChangePassword();
        }
    } else {
        // 显示认证表单
        if (authSection) {
            authSection.style.display = 'block';
        }
        
        // 隐藏用户信息
        if (userInfoDiv) {
            userInfoDiv.innerHTML = '<p>请先登录</p>';
        }
        
        // 隐藏管理系统入口
        const adminEntrySection = document.querySelector('.admin-entry-section');
        if (adminEntrySection) {
            adminEntrySection.style.display = 'none';
        }
    }
}

// 注册功能
function initRegister() {
    console.log('初始化注册功能');
    
    // 直接为注册按钮添加点击事件，避免表单submit事件的问题
    const registerBtn = document.getElementById('register-btn');
    if (!registerBtn) {
        console.log('注册按钮未找到');
        return;
    }
    
    console.log('注册按钮找到，添加点击事件监听器');
    registerBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        console.log('注册按钮点击事件触发');
        
        // 获取表单数据
        const username = document.getElementById('reg-username').value;
        const password = document.getElementById('reg-password').value;
        const email = document.getElementById('reg-email').value;
        const hireDate = document.getElementById('reg-hire-date').value;
        
        // 获取选中的角色
        const roleSelect = document.getElementById('reg-roles');
        const selectedRoles = Array.from(roleSelect.selectedOptions).map(option => parseInt(option.value));
        
        console.log('注册信息:', { username, email, hireDate, roles: selectedRoles });
        
        // 验证必填字段
        if (!username || !password) {
            alert('用户名和密码不能为空');
            return;
        }
        
        try {
            console.log('发送注册请求');
            // 只发送必要的注册信息，不包含角色（角色分配应该在注册后由管理员完成）
            const response = await authAPI.register({
                username,
                password,
                email,
                hire_date: hireDate
            });
            
            console.log('注册成功，响应:', response);
            alert('注册成功，请登录');
            // 切换到登录表单
            document.getElementById('register-form').style.display = 'none';
            document.getElementById('login-form').style.display = 'block';
        } catch (error) {
            console.error('注册失败:', error);
            alert('注册失败: ' + error.message);
        }
    });
    
    // 为注册表单显示时加载角色列表
    const showRegisterBtn = document.getElementById('show-register');
    if (showRegisterBtn) {
        showRegisterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // 显示注册表单
            document.getElementById('register-form').style.display = 'block';
            document.getElementById('login-form').style.display = 'none';
            // 加载角色列表
            loadRoles();
        });
    }
}

// 加载角色列表
async function loadRoles() {
    console.log('加载角色列表');
    try {
        const roles = await roleAPI.getRoles();
        console.log('角色列表:', roles);
        
        const roleSelect = document.getElementById('reg-roles');
        if (!roleSelect) {
            console.log('角色选择框未找到');
            return;
        }
        
        // 清空现有选项
        roleSelect.innerHTML = '';
        
        // 添加角色选项
        roles.forEach(role => {
            const option = document.createElement('option');
            option.value = role.id;
            option.textContent = role.name;
            roleSelect.appendChild(option);
        });
    } catch (error) {
        console.error('加载角色列表失败:', error);
        // 忽略错误，不影响注册功能
    }
}

// 登录功能
function initLogin() {
    console.log('初始化登录功能');
    
    // 直接为登录按钮添加点击事件，避免表单submit事件的问题
    const loginBtn = document.getElementById('login-btn');
    if (!loginBtn) {
        console.log('登录按钮未找到');
        return;
    }
    
    console.log('登录按钮找到，添加点击事件监听器');
    loginBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        console.log('登录按钮点击事件触发');
        
        // 获取表单数据
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        console.log('登录信息:', { username });
        
        // 验证必填字段
        if (!username || !password) {
            alert('用户名和密码不能为空');
            return;
        }
        
        try {
            console.log('发送登录请求');
            const user = await authAPI.login({ username, password });
            console.log('登录成功，用户信息:', user);
            setCurrentUser(user);
            alert('登录成功');
            window.location.reload();
        } catch (error) {
            console.error('登录失败:', error);
            alert('登录失败: ' + error.message);
        }
    });
}

// 修改密码功能
function initChangePassword() {
    // 取消修改密码按钮事件
    const cancelBtn = document.getElementById('cancel-change-password');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // 隐藏修改密码表单
            document.getElementById('change-password-form').style.display = 'none';
            // 显示用户信息
            const userInfoDiv = document.getElementById('user-info');
            if (userInfoDiv) {
                userInfoDiv.style.display = 'block';
            }
        });
    }
    
    // 修改密码按钮事件
    const changeBtn = document.getElementById('change-password-btn');
    if (changeBtn) {
        changeBtn.addEventListener('click', async function() {
            const user = getCurrentUser();
            if (!user) {
                alert('请先登录');
                return;
            }
            
            // 获取表单数据
            const oldPassword = document.getElementById('old-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            // 验证表单
            if (!newPassword) {
                alert('请输入新密码');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                alert('新密码和确认密码不一致');
                return;
            }
            
            try {
                // 调用API修改密码
                await authAPI.updatePassword({
                    user_id: user.id,
                    old_password: oldPassword,
                    new_password: newPassword
                });
                
                alert('密码修改成功');
                
                // 重置表单
                document.getElementById('old-password').value = '';
                document.getElementById('new-password').value = '';
                document.getElementById('confirm-password').value = '';
                
                // 隐藏修改密码表单
                document.getElementById('change-password-form').style.display = 'none';
                
                // 显示用户信息
                const userInfoDiv = document.getElementById('user-info');
                if (userInfoDiv) {
                    userInfoDiv.style.display = 'block';
                }
                
            } catch (error) {
                console.error('修改密码失败:', error);
                alert('修改密码失败: ' + error.message);
            }
        });
    }
}

// 初始化认证功能
async function initAuth() {
    await updateUserInfo();
    initRegister();
    initLogin();
    initChangePassword();
}

// 暴露全局函数
window.getCurrentUser = getCurrentUser;
window.setCurrentUser = setCurrentUser;
window.removeCurrentUser = removeCurrentUser;
window.isLoggedIn = isLoggedIn;
window.updateUserInfo = updateUserInfo;
window.initAuth = initAuth;