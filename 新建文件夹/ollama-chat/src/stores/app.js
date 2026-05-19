import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 主题设置
  const theme = ref('light')
  const setTheme = (newTheme) => {
    theme.value = newTheme
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('ollama-chat-theme', newTheme)
  }
  
  // 初始化主题
  const initTheme = () => {
    const saved = localStorage.getItem('ollama-chat-theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    setTheme(saved || (prefersDark ? 'dark' : 'light'))
  }
  
  // 侧边栏状态
  const sidebarOpen = ref(true)
  const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value
  }
  
  // 设置面板状态
  const settingsPanelOpen = ref(false)
  const toggleSettingsPanel = () => {
    settingsPanelOpen.value = !settingsPanelOpen.value
  }
  
  // 连接状态
  const isConnected = ref(false)
  const connectionStatus = ref('disconnected')
  
  return {
    theme,
    setTheme,
    initTheme,
    sidebarOpen,
    toggleSidebar,
    settingsPanelOpen,
    toggleSettingsPanel,
    isConnected,
    connectionStatus
  }
})