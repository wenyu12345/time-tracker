// 项目管理逻辑

// 加载项目列表
async function loadProjects() {
    const user = getCurrentUser();
    if (!user) return;
    
    const projectSelect = document.getElementById('project-select');
    if (!projectSelect) return;
    
    try {
        const projects = await projectAPI.getProjects(user.id);
        
        // 清空现有选项（保留默认选项）
        projectSelect.innerHTML = '<option value="">选择项目</option>';
        
        // 添加项目选项
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            if (project.color) {
                option.style.color = project.color;
            }
            projectSelect.appendChild(option);
        });
    } catch (error) {
        console.error('加载项目失败:', error);
    }
}

// 初始化项目管理功能
function initProjectManagement() {
    // 页面加载时加载项目列表
    loadProjects();
    
    // 监听用户登录状态变化，重新加载项目
    // 这里可以通过事件监听或定期检查来实现
}

// 暴露全局函数
window.initProjectManagement = initProjectManagement;