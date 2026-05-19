<template>
  <div class="settings-view">
    <div class="settings-header">
      <h2>设置</h2>
      <p>个性化您的 Ollama Chat 体验</p>
    </div>

    <div class="settings-content">
      <!-- 主题设置 -->
      <div class="settings-section">
        <h3>外观设置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label class="setting-label">主题模式</label>
            <div class="theme-options">
              <label class="theme-option">
                <input 
                  type="radio" 
                  name="theme" 
                  value="light"
                  v-model="appStore.theme"
                  @change="appStore.setTheme('light')"
                >
                <div class="theme-preview light">
                  <div class="theme-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 8.69V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69zM12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm0-10c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/>
                    </svg>
                  </div>
                  <span>浅色</span>
                </div>
              </label>
              
              <label class="theme-option">
                <input 
                  type="radio" 
                  name="theme" 
                  value="dark"
                  v-model="appStore.theme"
                  @change="appStore.setTheme('dark')"
                >
                <div class="theme-preview dark">
                  <div class="theme-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9.37 5.51A7.35 7.35 0 009.1 7.5c0 4.08 3.32 7.4 7.4 7.4.68 0 1.35-.09 1.99-.27A7.014 7.014 0 0112 19c-3.86 0-7-3.14-7-7 0-2.93 1.81-5.45 4.37-6.49zM12 3a9 9 0 109 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 01-4.4 2.26 5.403 5.403 0 01-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/>
                    </svg>
                  </div>
                  <span>深色</span>
                </div>
              </label>
              
              <label class="theme-option">
                <input 
                  type="radio" 
                  name="theme" 
                  value="auto"
                  v-model="appStore.theme"
                  @change="appStore.setTheme('auto')"
                >
                <div class="theme-preview auto">
                  <div class="theme-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                    </svg>
                  </div>
                  <span>自动</span>
                </div>
              </label>
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">字体大小</label>
            <div class="slider-container">
              <input 
                type="range" 
                min="12" 
                max="20" 
                step="1"
                v-model="fontSize"
                class="slider"
              >
              <span class="slider-value">{{ fontSize }}px</span>
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">界面语言</label>
            <select v-model="language" class="language-select">
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
              <option value="ja-JP">日本語</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 聊天设置 -->
      <div class="settings-section">
        <h3>聊天设置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label class="setting-label">消息气泡样式</label>
            <div class="bubble-options">
              <label class="bubble-option">
                <input type="radio" name="bubble" value="rounded" v-model="bubbleStyle">
                <div class="bubble-preview rounded">圆角</div>
              </label>
              <label class="bubble-option">
                <input type="radio" name="bubble" value="square" v-model="bubbleStyle">
                <div class="bubble-preview square">直角</div>
              </label>
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">自动保存间隔</label>
            <select v-model="autoSaveInterval" class="interval-select">
              <option value="30000">30秒</option>
              <option value="60000">1分钟</option>
              <option value="300000">5分钟</option>
              <option value="0">关闭</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <input type="checkbox" v-model="showTypingIndicator">
              <span>显示打字指示器</span>
            </label>
            <p class="setting-description">显示 AI 正在输入的状态指示器</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <input type="checkbox" v-model="streamResponse">
              <span>流式响应</span>
            </label>
            <p class="setting-description">实时显示 AI 回复内容</p>
          </div>
        </div>
      </div>

      <!-- 快捷键设置 -->
      <div class="settings-section">
        <h3>快捷键</h3>
        <div class="shortcuts-list">
          <div v-for="shortcut in shortcuts" :key="shortcut.action" class="shortcut-item">
            <span class="shortcut-action">{{ shortcut.action }}</span>
            <div class="shortcut-keys">
              <kbd v-for="key in shortcut.keys" :key="key" class="shortcut-key">{{ key }}</kbd>
            </div>
          </div>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="enableShortcuts">
            <span>启用快捷键</span>
          </label>
        </div>
      </div>

      <!-- 通知设置 -->
      <div class="settings-section">
        <h3>通知设置</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label class="setting-label">
              <input type="checkbox" v-model="desktopNotifications">
              <span>桌面通知</span>
            </label>
            <p class="setting-description">在收到新消息时显示桌面通知</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <input type="checkbox" v-model="soundNotifications">
              <span>声音提示</span>
            </label>
            <p class="setting-description">在收到新消息时播放声音提示</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">通知音量</label>
            <div class="slider-container">
              <input 
                type="range" 
                min="0" 
                max="100" 
                step="1"
                v-model="notificationVolume"
                class="slider"
                :disabled="!soundNotifications"
              >
              <span class="slider-value">{{ notificationVolume }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 隐私设置 -->
      <div class="settings-section">
        <h3>隐私与数据</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label class="setting-label">
              <input type="checkbox" v-model="autoClearHistory">
              <span>自动清理历史记录</span>
            </label>
            <p class="setting-description">关闭应用时自动清理聊天历史记录</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <input type="checkbox" v-model="analyticsTracking">
              <span>匿名使用统计</span>
            </label>
            <p class="setting-description">帮助我们改进应用（不包含个人数据）</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">数据存储位置</label>
            <div class="storage-info">
              <span>{{ storageLocation }}</span>
              <button class="change-btn" @click="changeStorageLocation">更改</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="settings-section">
        <h3>系统信息</h3>
        <div class="system-info">
          <div class="info-item">
            <span class="info-label">应用版本</span>
            <span class="info-value">{{ appVersion }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Ollama 版本</span>
            <span class="info-value">{{ ollamaVersion }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">最后更新</span>
            <span class="info-value">{{ lastUpdate }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">数据使用量</span>
            <span class="info-value">{{ dataUsage }}</span>
          </div>
        </div>
        
        <div class="system-actions">
          <button class="btn-secondary" @click="clearCache">清除缓存</button>
          <button class="btn-secondary" @click="checkForUpdates">检查更新</button>
          <button class="btn-primary" @click="exportAllData">导出所有数据</button>
        </div>
      </div>

      <!-- 重置设置 -->
      <div class="settings-section danger-zone">
        <h3>危险区域</h3>
        <div class="danger-actions">
          <button class="btn-danger" @click="resetSettings">重置所有设置</button>
          <button class="btn-danger" @click="clearAllData">清除所有数据</button>
        </div>
        <p class="danger-warning">这些操作不可撤销，请谨慎操作！</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '../stores/app'

const appStore = useAppStore()

// 主题设置
const fontSize = ref(16)
const language = ref('zh-CN')

// 聊天设置
const bubbleStyle = ref('rounded')
const autoSaveInterval = ref('60000')
const showTypingIndicator = ref(true)
const streamResponse = ref(true)

// 快捷键设置
const enableShortcuts = ref(true)
const shortcuts = ref([
  { action: '发送消息', keys: ['Enter'] },
  { action: '换行', keys: ['Shift', 'Enter'] },
  { action: '新建对话', keys: ['Ctrl', 'N'] },
  { action: '切换模型', keys: ['Ctrl', 'M'] },
  { action: '打开设置', keys: ['Ctrl', ','] },
  { action: '切换主题', keys: ['Ctrl', 'T'] }
])

// 通知设置
const desktopNotifications = ref(true)
const soundNotifications = ref(true)
const notificationVolume = ref(50)

// 隐私设置
const autoClearHistory = ref(false)
const analyticsTracking = ref(true)
const storageLocation = ref('本地存储')

// 系统信息
const appVersion = ref('1.0.0')
const ollamaVersion = ref('0.1.20')
const lastUpdate = ref('2024-01-15')
const dataUsage = ref('256 MB')

// 方法
const changeStorageLocation = () => {
  alert('存储位置更改功能正在开发中...')
}

const clearCache = () => {
  if (confirm('确定要清除缓存吗？')) {
    // 模拟清除缓存
    console.log('清除缓存...')
    alert('缓存已清除')
  }
}

const checkForUpdates = () => {
  alert('检查更新功能正在开发中...')
}

const exportAllData = () => {
  alert('数据导出功能正在开发中...')
}

const resetSettings = () => {
  if (confirm('确定要重置所有设置吗？此操作不可撤销！')) {
    // 模拟重置设置
    console.log('重置设置...')
    alert('设置已重置')
  }
}

const clearAllData = () => {
  if (confirm('确定要清除所有数据吗？此操作不可撤销！')) {
    if (confirm('这将删除所有聊天记录和设置，确定要继续吗？')) {
      // 模拟清除数据
      console.log('清除所有数据...')
      alert('所有数据已清除')
    }
  }
}

onMounted(() => {
  // 从本地存储加载设置
  const savedFontSize = localStorage.getItem('ollama-chat-font-size')
  if (savedFontSize) {
    fontSize.value = parseInt(savedFontSize)
  }
  
  const savedLanguage = localStorage.getItem('ollama-chat-language')
  if (savedLanguage) {
    language.value = savedLanguage
  }
})
</script>

<style scoped>
.settings-view {
  padding: var(--spacing-l);
  height: 100%;
  overflow-y: auto;
  background-color: var(--white);
}

.settings-header {
  margin-bottom: var(--spacing-xl);
}

.settings-header h2 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-s);
}

.settings-header p {
  color: var(--medium-gray);
  margin: 0;
}

.settings-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-l);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-lg);
  background-color: var(--white);
}

.settings-section h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-l);
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-l);
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-s);
}

.setting-label {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  color: var(--dark-gray);
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
}

.setting-label input[type="checkbox"] {
  margin: 0;
}

.setting-description {
  font-size: var(--text-sm);
  color: var(--medium-gray);
  margin: 0;
  line-height: 1.4;
}

/* 主题选项 */
.theme-options {
  display: flex;
  gap: var(--spacing-m);
}

.theme-option {
  cursor: pointer;
}

.theme-option input {
  display: none;
}

.theme-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-s);
  padding: var(--spacing-m);
  border: 2px solid var(--light-gray);
  border-radius: var(--radius-md);
  transition: all 0.2s ease-in-out;
}

.theme-option input:checked + .theme-preview {
  border-color: var(--primary-blue);
  background-color: var(--light-blue);
}

.theme-icon {
  color: var(--medium-gray);
}

.theme-option input:checked + .theme-preview .theme-icon {
  color: var(--primary-blue);
}

.theme-preview span {
  font-size: var(--text-sm);
  color: var(--medium-gray);
}

.theme-option input:checked + .theme-preview span {
  color: var(--primary-blue);
  font-weight: var(--font-medium);
}

/* 气泡选项 */
.bubble-options {
  display: flex;
  gap: var(--spacing-m);
}

.bubble-option {
  cursor: pointer;
}

.bubble-option input {
  display: none;
}

.bubble-preview {
  padding: var(--spacing-s) var(--spacing-m);
  border: 1px solid var(--light-gray);
  background-color: var(--light-blue);
  color: var(--primary-blue);
  font-size: var(--text-sm);
  transition: all 0.2s ease-in-out;
}

.bubble-option input:checked + .bubble-preview {
  border-color: var(--primary-blue);
  background-color: var(--primary-blue);
  color: var(--white);
}

.bubble-preview.rounded {
  border-radius: var(--radius-lg);
}

.bubble-preview.square {
  border-radius: var(--radius-xs);
}

/* 选择框 */
.language-select,
.interval-select {
  padding: var(--spacing-s) var(--spacing-m);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  background-color: var(--white);
}

/* 快捷键列表 */
.shortcuts-list {
  margin-bottom: var(--spacing-l);
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-m) 0;
  border-bottom: 1px solid var(--light-gray);
}

.shortcut-item:last-child {
  border-bottom: none;
}

.shortcut-action {
  font-size: var(--text-sm);
  color: var(--dark-gray);
}

.shortcut-keys {
  display: flex;
  gap: var(--spacing-xs);
}

.shortcut-key {
  padding: 2px 6px;
  background-color: var(--light-gray);
  color: var(--dark-gray);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-family: 'Fira Code', monospace;
}

/* 存储信息 */
.storage-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-m);
}

.change-btn {
  padding: var(--spacing-xs) var(--spacing-s);
  border: 1px solid var(--light-gray);
  background-color: var(--white);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.change-btn:hover {
  border-color: var(--primary-blue);
  color: var(--primary-blue);
}

/* 系统信息 */
.system-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-m);
  margin-bottom: var(--spacing-l);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-label {
  font-size: var(--text-sm);
  color: var(--medium-gray);
}

.info-value {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  color: var(--dark-gray);
}

.system-actions {
  display: flex;
  gap: var(--spacing-m);
  flex-wrap: wrap;
}

/* 按钮样式 */
.btn-primary,
.btn-secondary,
.btn-danger {
  padding: var(--spacing-s) var(--spacing-l);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.btn-primary {
  background-color: var(--primary-blue);
  color: var(--white);
}

.btn-primary:hover {
  background-color: var(--primary-blue-hover);
}

.btn-secondary {
  background-color: var(--light-gray);
  color: var(--dark-gray);
}

.btn-secondary:hover {
  background-color: var(--medium-gray);
  color: var(--white);
}

.btn-danger {
  background-color: var(--error);
  color: var(--white);
}

.btn-danger:hover {
  background-color: #dc2626;
}

/* 危险区域 */
.danger-zone {
  border-color: var(--error);
  background-color: #fef2f2;
}

.danger-zone h3 {
  color: var(--error);
}

.danger-actions {
  display: flex;
  gap: var(--spacing-m);
  margin-bottom: var(--spacing-s);
}

.danger-warning {
  font-size: var(--text-sm);
  color: var(--error);
  margin: 0;
}

/* 滑块样式 */
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

.slider:disabled {
  opacity: 0.5;
}

.slider:disabled::-webkit-slider-thumb {
  background: var(--medium-gray);
}

.slider-value {
  font-size: var(--text-sm);
  color: var(--medium-gray);
  min-width: 40px;
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-view {
    padding: var(--spacing-m);
  }
  
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .theme-options,
  .bubble-options {
    flex-direction: column;
  }
  
  .system-info {
    grid-template-columns: 1fr;
  }
  
  .system-actions,
  .danger-actions {
    flex-direction: column;
  }
  
  .danger-actions {
    align-items: stretch;
  }
}
</style>