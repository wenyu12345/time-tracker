<template>
  <div class="chat-layout" :class="{ 'sidebar-collapsed': !appStore.sidebarOpen }">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <button class="menu-btn" @click="appStore.toggleSidebar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 6h18M3 12h18M3 18h18"/>
          </svg>
        </button>
        <div class="logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="color: var(--primary-blue)">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          <span class="logo-text">Ollama Chat</span>
        </div>
      </div>
      
      <div class="header-center">
        <div class="connection-status" :class="connectionClass">
          <div class="status-dot"></div>
          <span>{{ connectionText }}</span>
        </div>
        <div class="current-model">
          {{ chatStore.modelSettings.currentModel }}
        </div>
      </div>
      
      <div class="header-right">
        <button class="theme-toggle" @click="toggleTheme">
          <svg v-if="appStore.theme === 'light'" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.46-.04-.92-.1-1.36-.98 1.37-2.58 2.26-4.4 2.26-3.31 0-6-2.69-6-6 0-1.8.8-3.4 2.1-4.4C12.92 3.04 12.46 3 12 3z"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1z"/>
          </svg>
        </button>
        <button class="settings-btn" @click="appStore.toggleSettingsPanel">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.45.17-.49.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.04.24.24.41.48.41h3.84c.24 0 .45-.17.49-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧边栏 -->
      <aside class="sidebar" v-if="appStore.sidebarOpen">
        <div class="sidebar-content">
          <!-- 新建对话按钮 -->
          <button class="new-chat-btn" @click="chatStore.createNewSession">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
            <span>新建对话</span>
          </button>

          <!-- 对话历史列表 -->
          <div class="sessions-section">
            <h3 class="section-title">对话历史</h3>
            <div class="sessions-list">
              <div 
                v-for="session in chatStore.sessions" 
                :key="session.id"
                class="session-item"
                :class="{ active: session.id === chatStore.currentSession.id }"
                @click="chatStore.switchSession(session.id)"
              >
                <div class="session-info">
                  <div class="session-name">{{ session.name }}</div>
                  <div class="session-time">{{ formatTime(session.updatedAt) }}</div>
                </div>
                <button 
                  class="delete-btn"
                  @click.stop="deleteSession(session.id)"
                  v-if="chatStore.sessions.length > 1"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中央聊天区域 -->
      <main class="chat-area">
        <router-view />
      </main>

      <!-- 右侧设置面板 -->
      <aside class="settings-panel" v-if="appStore.settingsPanelOpen">
        <div class="settings-content">
          <div class="settings-header">
            <h3>模型设置</h3>
            <button class="close-btn" @click="appStore.toggleSettingsPanel">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
          
          <div class="settings-section">
            <label class="setting-label">温度 (Temperature)</label>
            <div class="slider-container">
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01"
                v-model="chatStore.modelSettings.temperature"
                class="slider"
              >
              <span class="slider-value">{{ chatStore.modelSettings.temperature.toFixed(2) }}</span>
            </div>
          </div>
          
          <div class="settings-section">
            <label class="setting-label">最大长度 (Max Tokens)</label>
            <div class="slider-container">
              <input 
                type="range" 
                min="0" 
                max="32768" 
                step="1"
                v-model="chatStore.modelSettings.maxTokens"
                class="slider"
              >
              <span class="slider-value">{{ chatStore.modelSettings.maxTokens }}</span>
            </div>
          </div>
          
          <div class="settings-section">
            <label class="setting-label">Top P</label>
            <div class="slider-container">
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01"
                v-model="chatStore.modelSettings.topP"
                class="slider"
              >
              <span class="slider-value">{{ chatStore.modelSettings.topP.toFixed(2) }}</span>
            </div>
          </div>
          
          <div class="settings-section">
            <label class="setting-label">系统提示 (System Prompt)</label>
            <textarea 
              v-model="chatStore.modelSettings.systemPrompt"
              class="system-prompt"
              rows="4"
              placeholder="设置AI的角色和行为准则..."
            ></textarea>
          </div>
        </div>
      </aside>
    </div>

    <!-- 底部状态栏 -->
    <footer class="footer">
      <div class="footer-left">
        <span>Ollama Chat v1.0.0</span>
      </div>
      <div class="footer-right">
        <span>{{ currentTime }}</span>
        <span class="resource-info">CPU: 45% | Mem: 2.3GB</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useChatStore } from '../stores/chat'

const appStore = useAppStore()
const chatStore = useChatStore()

const currentTime = ref('')
let timeInterval = null

// 计算连接状态
const connectionClass = computed(() => ({
  connected: appStore.isConnected,
  disconnected: !appStore.isConnected
}))

const connectionText = computed(() => 
  appStore.isConnected ? '已连接' : '未连接'
)

// 切换主题
const toggleTheme = () => {
  const newTheme = appStore.theme === 'light' ? 'dark' : 'light'
  appStore.setTheme(newTheme)
}

// 删除会话
const deleteSession = (sessionId) => {
  if (confirm('确定要删除这个对话吗？')) {
    chatStore.deleteSession(sessionId)
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleDateString('zh-CN')
}

// 更新时间
const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--light-gray);
}

/* 头部样式 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 var(--spacing-l);
  background-color: var(--white);
  border-bottom: 1px solid var(--light-gray);
  box-shadow: var(--shadow-sm);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-m);
}

.menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--medium-gray);
  transition: all 0.2s ease-in-out;
}

.menu-btn:hover {
  background-color: var(--light-gray);
  color: var(--dark-gray);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--dark-gray);
}

.logo-text {
  background: linear-gradient(135deg, var(--primary-blue), var(--secondary-blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-center {
  display: flex;
  align-items: center;
  gap: var(--spacing-l);
}

.connection-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
  font-size: var(--text-sm);
  color: var(--medium-gray);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--error);
}

.connection-status.connected .status-dot {
  background-color: var(--success);
}

.current-model {
  background-color: var(--light-blue);
  color: var(--primary-blue);
  padding: var(--spacing-xs) var(--spacing-s);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
}

.theme-toggle,
.settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--medium-gray);
  transition: all 0.2s ease-in-out;
}

.theme-toggle:hover,
.settings-btn:hover {
  background-color: var(--light-gray);
  color: var(--dark-gray);
}

/* 主要内容区域 */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--white);
  border-right: 1px solid var(--light-gray);
  overflow-y: auto;
}

.sidebar-content {
  padding: var(--spacing-l);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
  width: 100%;
  padding: var(--spacing-m);
  background-color: var(--primary-blue);
  color: var(--white);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;
}

.new-chat-btn:hover {
  background-color: var(--primary-blue-hover);
}

.sessions-section {
  margin-top: var(--spacing-xl);
}

.section-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--medium-gray);
  margin-bottom: var(--spacing-m);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-m);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;
}

.session-item:hover {
  background-color: var(--light-gray);
}

.session-item.active {
  background-color: var(--light-blue);
  color: var(--primary-blue);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: var(--text-xs);
  color: var(--medium-gray);
  margin-top: 2px;
}

.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--medium-gray);
  opacity: 0;
  transition: all 0.2s ease-in-out;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background-color: var(--error);
  color: var(--white);
}

/* 聊天区域 */
.chat-area {
  flex: 1;
  overflow: hidden;
}

/* 设置面板 */
.settings-panel {
  width: var(--settings-panel-width);
  background-color: var(--white);
  border-left: 1px solid var(--light-gray);
  overflow-y: auto;
}

.settings-content {
  padding: var(--spacing-l);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
}

.settings-header h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--medium-gray);
  transition: all 0.2s ease-in-out;
}

.close-btn:hover {
  background-color: var(--light-gray);
  color: var(--dark-gray);
}

.settings-section {
  margin-bottom: var(--spacing-l);
}

.setting-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-s);
}

.slider-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-m);
}

.slider {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: var(--light-gray);
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-blue);
  cursor: pointer;
}

.slider-value {
  font-size: var(--text-sm);
  color: var(--medium-gray);
  min-width: 40px;
  text-align: right;
}

.system-prompt {
  width: 100%;
  padding: var(--spacing-s);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

.system-prompt:focus {
  outline: none;
  border-color: var(--primary-blue);
}

/* 底部状态栏 */
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--footer-height);
  padding: 0 var(--spacing-l);
  background-color: var(--white);
  border-top: 1px solid var(--light-gray);
  font-size: var(--text-xs);
  color: var(--medium-gray);
}

.footer-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-l);
}

.resource-info {
  font-family: 'Fira Code', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: var(--header-height);
    left: 0;
    height: calc(100vh - var(--header-height) - var(--footer-height));
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease-in-out;
  }
  
  .sidebar.sidebar-open {
    transform: translateX(0);
  }
  
  .settings-panel {
    position: fixed;
    top: var(--header-height);
    right: 0;
    height: calc(100vh - var(--header-height) - var(--footer-height));
    z-index: 1000;
    transform: translateX(100%);
    transition: transform 0.3s ease-in-out;
  }
  
  .settings-panel.settings-open {
    transform: translateX(0);
  }
}
</style>