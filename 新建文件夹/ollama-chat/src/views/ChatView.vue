<template>
  <div class="chat-view">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <div class="chat-title">
        <h2>{{ chatStore.currentSession.name }}</h2>
        <div class="chat-actions">
          <button 
            class="action-btn"
            @click="clearChat"
            :disabled="!chatStore.hasMessages"
            title="清空对话"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
          <button 
            class="action-btn"
            @click="exportChat"
            :disabled="!chatStore.hasMessages"
            title="导出对话"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="chat-info">
        <span class="message-count">{{ chatStore.messageCount }} 条消息</span>
        <span class="model-info">{{ chatStore.modelSettings.currentModel }}</span>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="messages-container" ref="messagesContainer">
      <!-- 欢迎消息 -->
      <div v-if="!chatStore.hasMessages" class="welcome-message">
        <div class="welcome-content">
          <div class="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <h3>欢迎使用 Ollama Chat</h3>
          <p>开始与您的本地 AI 模型对话吧！</p>
          <div class="quick-prompts">
            <button 
              v-for="prompt in quickPrompts" 
              :key="prompt.id"
              class="quick-prompt-btn"
              @click="useQuickPrompt(prompt.text)"
            >
              {{ prompt.text }}
            </button>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div 
        v-for="message in chatStore.currentSession.messages" 
        :key="message.id"
        class="message"
        :class="message.role"
      >
        <div class="message-avatar">
          <div class="avatar" :class="message.role">
            <svg v-if="message.role === 'user'" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">{{ message.role === 'user' ? '您' : 'AI助手' }}</span>
            <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
          </div>
          <div class="message-text">
            <div v-if="message.type === 'text'" class="message-markdown">
              <div v-html="renderMarkdown(message.content)"></div>
            </div>
            <div v-else-if="message.type === 'error'" class="message-error">
              <div class="error-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                </svg>
              </div>
              <span>{{ message.content }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 正在生成指示器 -->
      <div v-if="chatStore.isGenerating" class="message assistant">
        <div class="message-avatar">
          <div class="avatar assistant">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">AI助手</span>
            <span class="message-time">正在思考...</span>
          </div>
          <div class="thinking-indicator">
            <div class="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-container">
        <div class="input-actions">
          <button 
            class="action-btn"
            @click="toggleVoiceInput"
            :class="{ active: isVoiceInputActive }"
            title="语音输入"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          </button>
          <button 
            class="action-btn"
            @click="toggleImageInput"
            title="图片上传"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
            </svg>
          </button>
          <button 
            class="action-btn"
            @click="insertEmoji"
            title="插入表情"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"/>
            </svg>
          </button>
        </div>
        
        <textarea
          ref="messageInput"
          v-model="chatStore.currentInput"
          @keydown="handleKeydown"
          @input="handleInput"
          placeholder="输入您的问题..."
          class="message-input"
          rows="1"
        ></textarea>
        
        <button 
          class="send-btn"
          @click="sendMessage"
          :disabled="!canSend"
          :class="{ disabled: !canSend }"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
      
      <div class="input-footer">
        <span class="hint-text">按 Enter 发送，Shift + Enter 换行</span>
        <div class="parameter-hints">
          <span class="parameter-hint">温度: {{ chatStore.modelSettings.temperature.toFixed(2) }}</span>
          <span class="parameter-hint">最大长度: {{ chatStore.modelSettings.maxTokens }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUpdated } from 'vue'
import { marked } from 'marked'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const messagesContainer = ref(null)
const messageInput = ref(null)
const isVoiceInputActive = ref(false)

// 快速提示
const quickPrompts = ref([
  { id: 1, text: '你好！请介绍一下你自己。' },
  { id: 2, text: '帮我写一段简单的Python代码。' },
  { id: 3, text: '解释一下什么是人工智能。' },
  { id: 4, text: '给我一些学习建议。' }
])

// 计算属性
const canSend = computed(() => {
  return chatStore.currentInput.trim().length > 0 && !chatStore.isGenerating
})

// 发送消息
const sendMessage = async () => {
  if (!canSend.value) return
  
  await chatStore.sendMessage(chatStore.currentInput)
  scrollToBottom()
}

// 处理键盘事件
const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 处理输入框调整
const handleInput = () => {
  // 自动调整输入框高度
  const textarea = messageInput.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 格式化消息时间
const formatMessageTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 渲染 Markdown
const renderMarkdown = (content) => {
  return marked(content, {
    breaks: true,
    gfm: true
  })
}

// 快速提示
const useQuickPrompt = (text) => {
  chatStore.currentInput = text
  messageInput.value?.focus()
}

// 清空对话
const clearChat = () => {
  if (confirm('确定要清空当前对话吗？')) {
    chatStore.clearCurrentSession()
  }
}

// 导出对话
const exportChat = () => {
  const content = chatStore.currentSession.messages
    .map(msg => `${msg.role === 'user' ? '您' : 'AI助手'}: ${msg.content}`)
    .join('\n\n')
  
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat-${chatStore.currentSession.id}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// 语音输入
const toggleVoiceInput = () => {
  isVoiceInputActive.value = !isVoiceInputActive.value
  // 这里可以添加语音识别功能
  if (isVoiceInputActive.value) {
    alert('语音输入功能正在开发中...')
  }
}

// 图片上传
const toggleImageInput = () => {
  alert('图片上传功能正在开发中...')
}

// 插入表情
const insertEmoji = () => {
  const emojis = ['😊', '😂', '🤔', '👍', '❤️', '🎉', '🚀', '💡']
  const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)]
  chatStore.currentInput += randomEmoji
  messageInput.value?.focus()
}

// 生命周期
onMounted(() => {
  scrollToBottom()
  messageInput.value?.focus()
})

onUpdated(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--white);
}

/* 聊天头部 */
.chat-header {
  padding: var(--spacing-l);
  border-bottom: 1px solid var(--light-gray);
  background-color: var(--white);
}

.chat-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-s);
}

.chat-title h2 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin: 0;
}

.chat-actions {
  display: flex;
  gap: var(--spacing-s);
}

.action-btn {
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

.action-btn:hover:not(:disabled) {
  background-color: var(--light-gray);
  color: var(--dark-gray);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.active {
  background-color: var(--primary-blue);
  color: var(--white);
}

.chat-info {
  display: flex;
  gap: var(--spacing-l);
  font-size: var(--text-sm);
  color: var(--medium-gray);
}

.message-count,
.model-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-l);
  background-color: var(--light-gray);
}

/* 欢迎消息 */
.welcome-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.welcome-content {
  max-width: 400px;
}

.welcome-icon {
  margin-bottom: var(--spacing-l);
  color: var(--primary-blue);
}

.welcome-content h3 {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-s);
}

.welcome-content p {
  color: var(--medium-gray);
  margin-bottom: var(--spacing-l);
}

.quick-prompts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-s);
}

.quick-prompt-btn {
  padding: var(--spacing-m);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-md);
  background-color: var(--white);
  color: var(--dark-gray);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  font-size: var(--text-sm);
  text-align: left;
}

.quick-prompt-btn:hover {
  border-color: var(--primary-blue);
  background-color: var(--light-blue);
}

/* 消息样式 */
.message {
  display: flex;
  margin-bottom: var(--spacing-xl);
  gap: var(--spacing-m);
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.avatar.user {
  background-color: var(--primary-blue);
  color: var(--white);
}

.avatar.assistant {
  background-color: var(--success);
  color: var(--white);
}

.message-content {
  flex: 1;
  max-width: calc(100% - 48px);
}

.message-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
  margin-bottom: var(--spacing-xs);
}

.message-role {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
}

.message-time {
  font-size: var(--text-xs);
  color: var(--medium-gray);
}

.message-text {
  background-color: var(--white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-m);
  box-shadow: var(--shadow-sm);
  position: relative;
}

.message.user .message-text {
  background-color: var(--primary-blue);
  color: var(--white);
}

.message-markdown {
  line-height: 1.6;
}

.message-markdown :deep(p) {
  margin: 0 0 var(--spacing-s) 0;
}

.message-markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.message-markdown :deep(code) {
  background-color: var(--light-gray);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
}

.message-markdown :deep(pre) {
  background-color: var(--light-gray);
  padding: var(--spacing-m);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--spacing-s) 0;
}

.message-markdown :deep(pre code) {
  background: none;
  padding: 0;
}

.message-error {
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
  color: var(--error);
  font-size: var(--text-sm);
}

.error-icon {
  display: flex;
  align-items: center;
}

/* 正在思考指示器 */
.thinking-indicator {
  padding: var(--spacing-m);
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--medium-gray);
  animation: thinking 1.4s infinite ease-in-out;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes thinking {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入区域 */
.input-area {
  padding: var(--spacing-l);
  border-top: 1px solid var(--light-gray);
  background-color: var(--white);
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-m);
  margin-bottom: var(--spacing-s);
}

.input-actions {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-s);
}

.message-input {
  flex: 1;
  min-height: 40px;
  max-height: 120px;
  padding: var(--spacing-m);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.2s ease-in-out;
}

.message-input:focus {
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background-color: var(--primary-blue);
  color: var(--white);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  flex-shrink: 0;
}

.send-btn:hover:not(.disabled) {
  background-color: var(--primary-blue-hover);
  transform: translateY(-1px);
}

.send-btn.disabled {
  background-color: var(--light-gray);
  color: var(--medium-gray);
  cursor: not-allowed;
  transform: none;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint-text {
  font-size: var(--text-xs);
  color: var(--medium-gray);
}

.parameter-hints {
  display: flex;
  gap: var(--spacing-l);
}

.parameter-hint {
  font-size: var(--text-xs);
  color: var(--medium-gray);
  font-family: 'Fira Code', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-header {
    padding: var(--spacing-m);
  }
  
  .messages-container {
    padding: var(--spacing-m);
  }
  
  .input-area {
    padding: var(--spacing-m);
  }
  
  .quick-prompts {
    grid-template-columns: 1fr;
  }
  
  .input-footer {
    flex-direction: column;
    gap: var(--spacing-s);
    align-items: flex-start;
  }
}
</style>