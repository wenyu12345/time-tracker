// 工资算法配置模块

// 初始化工资算法配置页面
function initSalaryConfig() {
    // 加载配置列表
    loadConfigList();
    
    // 绑定重置按钮事件（仅当按钮存在时绑定）
    const resetBtn = document.getElementById('reset-config-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetConfig);
    }
}

// 加载配置列表
async function loadConfigList() {
    try {
        const configs = await fetchSalaryConfigs();
        renderConfigList(configs);
    } catch (error) {
        console.error('加载配置列表失败:', error);
        showMessage('加载配置列表失败', 'error');
    }
}

// 获取工资算法配置
async function fetchSalaryConfigs() {
    const response = await fetch('/api/salary/config');
    if (!response.ok) {
        throw new Error('获取配置失败');
    }
    return await response.json();
}

// 渲染配置列表
function renderConfigList(configs) {
    const configList = document.getElementById('config-list');
    if (!configList) return;
    
    // 如果没有配置，显示默认配置
    if (configs.length === 0) {
        configList.innerHTML = '<p class="empty-message">暂无配置项</p>';
        return;
    }
    
    // 渲染配置项
    configList.innerHTML = configs.map(config => `
        <div class="config-item">
            <div class="config-header">
                <h3>${config.config_key}</h3>
                <span class="config-description">${config.description || ''}</span>
            </div>
            <div class="config-content">
                <div class="form-group">
                    <label for="config-${config.config_key}">值</label>
                    <input type="number" id="config-${config.config_key}" 
                           value="${config.config_value}" step="0.01" 
                           class="config-input">
                </div>
                <button class="btn primary save-config-btn" 
                        data-key="${config.config_key}">保存</button>
            </div>
        </div>
    `).join('');
    
    // 绑定保存按钮事件
    document.querySelectorAll('.save-config-btn').forEach(btn => {
        btn.addEventListener('click', saveConfig);
    });
}

// 保存配置
async function saveConfig(event) {
    const btn = event.target;
    const configKey = btn.dataset.key;
    const input = document.getElementById(`config-${configKey}`);
    const configValue = parseFloat(input.value);
    
    // 验证输入
    if (isNaN(configValue)) {
        showMessage('请输入有效的数值', 'error');
        return;
    }
    
    try {
        await updateSalaryConfig(configKey, configValue);
        showMessage('配置保存成功', 'success');
    } catch (error) {
        console.error('保存配置失败:', error);
        showMessage('保存配置失败', 'error');
    }
}

// 更新工资算法配置
async function updateSalaryConfig(configKey, configValue) {
    const response = await fetch('/api/salary/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            config_key: configKey,
            config_value: configValue
        })
    });
    
    if (!response.ok) {
        throw new Error('更新配置失败');
    }
    
    return await response.json();
}

// 重置配置为默认值
async function resetConfig() {
    if (confirm('确定要重置所有配置为默认值吗？')) {
        try {
            await resetSalaryConfig();
            showMessage('配置已重置为默认值', 'success');
            // 重新加载配置列表
            loadConfigList();
        } catch (error) {
            console.error('重置配置失败:', error);
            showMessage('重置配置失败', 'error');
        }
    }
}

// 重置工资算法配置为默认值
async function resetSalaryConfig() {
    const response = await fetch('/api/salary/config/reset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    if (!response.ok) {
        throw new Error('重置配置失败');
    }
    
    return await response.json();
}

// 显示消息
function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    messageEl.textContent = message;
    
    // 添加到页面
    document.body.appendChild(messageEl);
    
    // 3秒后自动移除
    setTimeout(() => {
        messageEl.remove();
    }, 3000);
}

// 导出函数，供其他模块使用
window.initSalaryConfig = initSalaryConfig;