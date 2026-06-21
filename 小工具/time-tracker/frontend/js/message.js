// 留言墙功能实现
let aiReplyRefreshTimer = null;
let currentUserConfig = null;
let aiChatMessages = [];

// 初始化留言墙功能
async function initMessageWall() {
    // 绑定事件监听器
    bindMessageEvents();
    
    // 加载用户配置
    await loadUserConfig();
    
    // 加载可用模型
    loadAvailableModels();
    
    // 初始加载留言列表
    loadPublicMessages();
    
    // 设置定时刷新留言（每30秒）
    setInterval(loadPublicMessages, 30000);
}

// 绑定留言相关事件监听器
function bindMessageEvents() {
    // 绑定子选项卡事件
    bindSubtabEvents();
    
    // 公共留言事件
    bindPublicMessageEvents();
    
    // AI 聊天事件
    bindAiChatEvents();
    
    // 配置事件
    bindConfigEvents();
}

// ========== 子选项卡功能 ==========
function bindSubtabEvents() {
    const subtabBtns = document.querySelectorAll('.message-subtab-btn');
    subtabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const subtab = this.getAttribute('data-subtab');
            switchSubtab(subtab);
        });
    });
}

function switchSubtab(subtabName) {
    // 移除所有按钮的 active 类
    document.querySelectorAll('.message-subtab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 移除所有子选项卡内容的 active 类
    document.querySelectorAll('.message-subtab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 添加当前按钮的 active 类
    const activeBtn = document.querySelector(`[data-subtab="${subtabName}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // 添加当前内容的 active 类
    const activeContent = document.getElementById(`${subtabName}-subtab`);
    if (activeContent) {
        activeContent.classList.add('active');
    }
}

// ========== 公共留言功能 ==========
function bindPublicMessageEvents() {
    // 发送留言按钮
    const sendBtn = document.getElementById('send-public-message-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendPublicMessage);
    }
    
    // 刷新留言按钮
    const refreshBtn = document.getElementById('refresh-public-message-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadPublicMessages);
    }
    
    // 回车键发送留言
    const input = document.getElementById('public-message-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendPublicMessage();
            }
        });
    }
}

async function loadPublicMessages() {
    const messageList = document.getElementById('public-message-list');
    if (!messageList) return;
    
    try {
        clearMessageCache();
        const response = await messageAPI.getMessages(1, 55);
        const messages = Array.isArray(response) ? response : response.messages || [];
        renderPublicMessageList(messages);
    } catch (error) {
        console.error('加载留言失败:', error);
        messageList.innerHTML = '<div class="error-message">加载留言失败，请稍后重试</div>';
    }
}

function renderPublicMessageList(messages) {
    const messageList = document.getElementById('public-message-list');
    if (!messageList) return;
    
    if (!messages || messages.length === 0) {
        messageList.innerHTML = '<div class="empty-message">暂无留言，快来发表第一条留言吧！</div>';
        return;
    }
    
    const sortedMessages = messages.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    const messagesHTML = sortedMessages.map(message => {
        const displayName = message.is_system ? '系统消息' : (message.username || message.user_id);
        const isAiMessage = message.username === 'AI助手';
        
        let messageClass = '';
        if (message.is_system) {
            messageClass = 'system-message';
        }
        
        let avatar = '👤';
        
        return `
            <div class="message-item ${messageClass}">
                <div class="message-header">
                    <span class="message-avatar">${avatar}</span>
                    <span class="message-username">${displayName}</span>
                    <span class="message-time">${formatDate(message.created_at)}</span>
                    ${!message.is_system ? `<button class="delete-message-btn" data-message-id="${message.id}">删除</button>` : ''}
                </div>
                <div class="message-content">${escapeHtml(message.content)}</div>
                ${message.reply_to ? `<div class="message-reply">回复留言 #${message.reply_to}</div>` : ''}
            </div>
        `;
    }).join('');
    
    messageList.innerHTML = messagesHTML;
    bindDeleteMessageEvents(messageList);
    messageList.scrollTop = messageList.scrollHeight;
}

async function sendPublicMessage() {
    const messageInput = document.getElementById('public-message-input');
    if (!messageInput) return;
    
    const content = messageInput.value.trim();
    if (!content) {
        alert('请输入留言内容');
        return;
    }
    
    try {
        const user = getCurrentUser();
        const userId = user ? user.id : '匿名用户';
        
        await messageAPI.createMessage({
            user_id: userId,
            content: content,
            enable_ai_reply: false
        });
        
        messageInput.value = '';
        loadPublicMessages();
        
    } catch (error) {
        console.error('发送留言失败:', error);
        alert('发送留言失败，请稍后重试');
    }
}

// ========== AI 聊天功能 ==========
function bindAiChatEvents() {
    // 发送 AI 聊天按钮
    const sendBtn = document.getElementById('send-ai-chat-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendAiChatMessage);
    }
    
    // 清空 AI 聊天按钮
    const clearBtn = document.getElementById('clear-ai-chat-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearAiChat);
    }
    
    // 回车键发送 AI 聊天
    const input = document.getElementById('ai-chat-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAiChatMessage();
            }
        });
    }
    
    // 快速指令按钮
    bindQuickCommandEvents();
}

// 绑定快速指令按钮事件
function bindQuickCommandEvents() {
    const quickButtons = document.querySelectorAll('.quick-command-btn');
    quickButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const command = this.getAttribute('data-command');
            if (command) {
                // 设置到输入框
                const messageInput = document.getElementById('ai-chat-input');
                if (messageInput) {
                    messageInput.value = command;
                    messageInput.focus();
                }
                // 立即发送
                sendAiChatMessage();
            }
        });
    });
}

async function sendAiChatMessage() {
    const messageInput = document.getElementById('ai-chat-input');
    if (!messageInput) return;
    
    const content = messageInput.value.trim();
    if (!content) {
        alert('请输入消息内容');
        return;
    }
    
    // 检查是否启用了 AI 聊天
    if (!currentUserConfig || !currentUserConfig.ai_chat_enabled) {
        alert('请先在设置中启用 AI 聊天');
        return;
    }
    
    // 添加用户消息到聊天列表
    addAiChatMessage('user', content);
    
    // 清空输入框
    messageInput.value = '';
    
    // 发送到服务器处理
    const user = getCurrentUser();
    const userId = user ? user.id : '匿名用户';
    
    try {
        // 先添加一个正在加载的消息
        const loadingId = 'ai-loading-' + Date.now();
        addAiChatLoading(loadingId);
        
        const response = await messageAPI.createMessage({
            user_id: userId,
            content: content,
            enable_ai_reply: true,
            is_private_chat: true
        });
        
        // 快速刷新等待 AI 回复
        startAiChatRefresh(userId, loadingId);
        
    } catch (error) {
        console.error('发送消息失败:', error);
        addAiChatMessage('ai', '抱歉，发送失败，请稍后重试');
    }
}

function startAiChatRefresh(userId, loadingId) {
    if (aiReplyRefreshTimer) {
        clearInterval(aiReplyRefreshTimer);
    }
    
    let refreshCount = 0;
    const maxRefreshes = 120;  // 增加到 120 秒（2分钟）
    
    aiReplyRefreshTimer = setInterval(async () => {
        refreshCount++;
        
        try {
            const response = await messageAPI.getMessages(1, 55);
            const messages = Array.isArray(response) ? response : response.messages || [];
            
            // 查找最新的 AI 回复
            const latestAiReply = messages.find(msg => 
                msg.username === 'AI助手' && 
                new Date(msg.created_at) > new Date(Date.now() - 180000)  // 增加到 3 分钟
            );
            
            if (latestAiReply) {
                removeAiChatLoading(loadingId);
                addAiChatMessage('ai', latestAiReply.content);
                clearInterval(aiReplyRefreshTimer);
                aiReplyRefreshTimer = null;
            } else if (refreshCount >= maxRefreshes) {
                removeAiChatLoading(loadingId);
                addAiChatMessage('ai', '抱歉，AI回复超时了，请稍后重试。您也可以检查一下 Ollama 是否正在运行。');
                clearInterval(aiReplyRefreshTimer);
                aiReplyRefreshTimer = null;
            }
        } catch (error) {
            console.error('刷新失败:', error);
        }
    }, 1000);
}

function addAiChatMessage(sender, content) {
    const chatList = document.getElementById('ai-chat-list');
    if (!chatList) return;
    
    aiChatMessages.push({
        sender,
        content,
        time: new Date()
    });
    
    renderAiChatList();
}

function addAiChatLoading(id) {
    const chatList = document.getElementById('ai-chat-list');
    if (!chatList) return;
    
    const loadingDiv = document.createElement('div');
    loadingDiv.id = id;
    loadingDiv.className = 'message-item ai-message';
    loadingDiv.innerHTML = `
        <div class="message-header">
            <span class="message-avatar">🤖</span>
            <span class="message-username">AI助手</span>
            <span class="message-time">正在思考...</span>
        </div>
        <div class="message-content">
            <span class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </span>
        </div>
    `;
    
    chatList.appendChild(loadingDiv);
    chatList.scrollTop = chatList.scrollHeight;
}

function removeAiChatLoading(id) {
    const loadingDiv = document.getElementById(id);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function renderAiChatList() {
    const chatList = document.getElementById('ai-chat-list');
    if (!chatList) return;
    
    if (aiChatMessages.length === 0) {
        chatList.innerHTML = '<div class="empty-message">👋 您好！我是AI助手，有什么可以帮您的吗？</div>';
        return;
    }
    
    const messagesHTML = aiChatMessages.map(msg => {
        const isUser = msg.sender === 'user';
        const avatar = isUser ? '👤' : '🤖';
        const username = isUser ? '您' : 'AI助手';
        const messageClass = isUser ? '' : 'ai-message';
        
        return `
            <div class="message-item ${messageClass}">
                <div class="message-header">
                    <span class="message-avatar">${avatar}</span>
                    <span class="message-username">${username}</span>
                    <span class="message-time">${formatDate(msg.time)}</span>
                </div>
                <div class="message-content">${escapeHtml(msg.content)}</div>
            </div>
        `;
    }).join('');
    
    chatList.innerHTML = messagesHTML;
    chatList.scrollTop = chatList.scrollHeight;
}

function clearAiChat() {
    if (confirm('确定要清空聊天记录吗？')) {
        aiChatMessages = [];
        renderAiChatList();
    }
}

// ========== 通用功能 ==========
function clearMessageCache() {
    if ('caches' in window) {
        caches.keys().then(cacheNames => {
            cacheNames.forEach(cacheName => {
                if (cacheName.includes('message') || cacheName.includes('api')) {
                    caches.delete(cacheName);
                }
            });
        });
    }
    localStorage.removeItem('messages');
    sessionStorage.removeItem('messages');
}

function bindDeleteMessageEvents(container) {
    const deleteBtns = container.querySelectorAll('.delete-message-btn');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const messageId = this.getAttribute('data-message-id');
            deleteMessage(messageId);
        });
    });
}

async function deleteMessage(messageId) {
    if (!confirm('确定要删除这条留言吗？')) {
        return;
    }
    
    try {
        await messageAPI.deleteMessage(messageId);
        loadPublicMessages();
    } catch (error) {
        console.error('删除留言失败:', error);
        alert('删除留言失败，请稍后重试');
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== 用户配置功能 ==========
async function loadUserConfig() {
    const user = getCurrentUser();
    if (!user) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/user-config/${user.id}`);
        if (response.ok) {
            currentUserConfig = await response.json();
            updateConfigUI();
        }
    } catch (error) {
        console.error('加载用户配置失败:', error);
    }
}

async function loadAvailableModels() {
    const modelSelect = document.getElementById('ai-model-select');
    if (!modelSelect) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/user-config/available-models`);
        if (response.ok) {
            const data = await response.json();
            const models = data.models;
            
            modelSelect.innerHTML = '';
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
            
            if (currentUserConfig && currentUserConfig.ai_model) {
                modelSelect.value = currentUserConfig.ai_model;
            }
        }
    } catch (error) {
        console.error('加载可用模型失败:', error);
    }
}

async function updateUserConfig(configData) {
    const user = getCurrentUser();
    if (!user) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/user-config/${user.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        });
        
        if (response.ok) {
            currentUserConfig = await response.json();
            updateConfigUI();
            showToast('设置已保存');
        }
    } catch (error) {
        console.error('更新用户配置失败:', error);
        showToast('保存设置失败');
    }
}

function updateConfigUI() {
    if (!currentUserConfig) return;
    
    const aiChatToggle = document.getElementById('ai-chat-toggle');
    const aiAttendanceToggle = document.getElementById('ai-attendance-toggle');
    const aiViewAttendanceToggle = document.getElementById('ai-view-attendance-toggle');
    const aiAnalyzeAttendanceToggle = document.getElementById('ai-analyze-attendance-toggle');
    const aiSearchToggle = document.getElementById('ai-search-toggle');
    const aiModelSelect = document.getElementById('ai-model-select');
    
    if (aiChatToggle) {
        aiChatToggle.checked = currentUserConfig.ai_chat_enabled;
    }
    if (aiViewAttendanceToggle) {
        aiViewAttendanceToggle.checked = currentUserConfig.ai_can_view_attendance;
    }
    if (aiAnalyzeAttendanceToggle) {
        aiAnalyzeAttendanceToggle.checked = currentUserConfig.ai_can_analyze_attendance;
    }
    if (aiSearchToggle) {
        aiSearchToggle.checked = currentUserConfig.ai_can_search;
    }
    if (aiAttendanceToggle) {
        aiAttendanceToggle.checked = currentUserConfig.ai_can_modify_attendance;
    }
    if (aiModelSelect && currentUserConfig.ai_model) {
        aiModelSelect.value = currentUserConfig.ai_model;
    }
}

function bindConfigEvents() {
    const aiChatToggle = document.getElementById('ai-chat-toggle');
    if (aiChatToggle) {
        aiChatToggle.addEventListener('change', function() {
            updateUserConfig({ ai_chat_enabled: this.checked });
        });
    }
    
    const aiModelSelect = document.getElementById('ai-model-select');
    if (aiModelSelect) {
        aiModelSelect.addEventListener('change', function() {
            updateUserConfig({ ai_model: this.value });
        });
    }
    
    const aiViewAttendanceToggle = document.getElementById('ai-view-attendance-toggle');
    if (aiViewAttendanceToggle) {
        aiViewAttendanceToggle.addEventListener('change', function() {
            updateUserConfig({ ai_can_view_attendance: this.checked });
        });
    }
    
    const aiAnalyzeAttendanceToggle = document.getElementById('ai-analyze-attendance-toggle');
    if (aiAnalyzeAttendanceToggle) {
        aiAnalyzeAttendanceToggle.addEventListener('change', function() {
            updateUserConfig({ ai_can_analyze_attendance: this.checked });
        });
    }
    
    const aiSearchToggle = document.getElementById('ai-search-toggle');
    if (aiSearchToggle) {
        aiSearchToggle.addEventListener('change', function() {
            updateUserConfig({ ai_can_search: this.checked });
        });
    }
    
    const aiAttendanceToggle = document.getElementById('ai-attendance-toggle');
    if (aiAttendanceToggle) {
        aiAttendanceToggle.addEventListener('change', function() {
            updateUserConfig({ ai_can_modify_attendance: this.checked });
        });
    }
}

// 暴露给 tabs.js 切换时调用
window.initMessageWall = initMessageWall;

