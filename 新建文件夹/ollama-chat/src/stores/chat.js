import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useChatStore = defineStore('chat', () => {
  // 当前对话会话
  const currentSession = ref({
    id: 'default',
    name: '新对话',
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  })
  
  // 所有对话会话
  const sessions = ref([currentSession.value])
  
  // 模型设置
  const modelSettings = ref({
    currentModel: 'llama2',
    temperature: 0.7,
    maxTokens: 2048,
    topP: 0.9,
    systemPrompt: 'You are a helpful AI assistant.',
    contextWindow: 4096
  })
  
  // 当前输入
  const currentInput = ref('')
  
  // 是否正在生成回复
  const isGenerating = ref(false)
  
  // 添加消息到当前会话
  const addMessage = (message) => {
    if (!currentSession.value.messages) {
      currentSession.value.messages = []
    }
    currentSession.value.messages.push({
      id: Date.now().toString(),
      ...message,
      timestamp: new Date().toISOString()
    })
    currentSession.value.updatedAt = new Date().toISOString()
  }
  
  // 创建新会话
  const createNewSession = () => {
    const newSession = {
      id: Date.now().toString(),
      name: '新对话',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    
    sessions.value.unshift(newSession)
    currentSession.value = newSession
  }
  
  // 切换会话
  const switchSession = (sessionId) => {
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      currentSession.value = session
    }
  }
  
  // 删除会话
  const deleteSession = (sessionId) => {
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSession.value.id === sessionId && sessions.value.length > 0) {
      currentSession.value = sessions.value[0]
    }
  }
  
  // 重命名会话
  const renameSession = (sessionId, newName) => {
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      session.name = newName
      session.updatedAt = new Date().toISOString()
    }
  }
  
  // 清空当前会话
  const clearCurrentSession = () => {
    currentSession.value.messages = []
    currentSession.value.updatedAt = new Date().toISOString()
  }
  
  // 发送消息
  const sendMessage = async (content) => {
    if (!content.trim()) return
    
    // 添加用户消息
    addMessage({
      role: 'user',
      content: content.trim(),
      type: 'text'
    })
    
    // 清空输入
    currentInput.value = ''
    
    // 开始生成回复
    isGenerating.value = true
    
    try {
      // 模拟 API 调用
      const response = await simulateAIResponse(content)
      
      // 添加 AI 回复
      addMessage({
        role: 'assistant',
        content: response,
        type: 'text'
      })
      
    } catch (error) {
      console.error('发送消息失败:', error)
      addMessage({
        role: 'assistant',
        content: '抱歉，我遇到了一个错误。请稍后重试。',
        type: 'error'
      })
    } finally {
      isGenerating.value = false
    }
  }
  
  // 模拟 AI 回复
  const simulateAIResponse = async (userMessage) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const responses = [
          `我理解您说的"${userMessage}"。这是一个很好的问题！`,
          `关于"${userMessage}"，我有以下想法...`,
          `感谢您的提问！对于"${userMessage}"，我的回答是...`,
          `这是一个有趣的话题！让我来分享一些关于"${userMessage}"的见解。`
        ]
        resolve(responses[Math.floor(Math.random() * responses.length)])
      }, 1000 + Math.random() * 2000)
    })
  }
  
  // 计算属性
  const messageCount = computed(() => {
    return currentSession.value.messages?.length || 0
  })
  
  const hasMessages = computed(() => {
    return messageCount.value > 0
  })
  
  return {
    // 状态
    currentSession,
    sessions,
    modelSettings,
    currentInput,
    isGenerating,
    
    // 方法
    addMessage,
    createNewSession,
    switchSession,
    deleteSession,
    renameSession,
    clearCurrentSession,
    sendMessage,
    
    // 计算属性
    messageCount,
    hasMessages
  }
})