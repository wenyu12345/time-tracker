<template>
  <div class="models-view">
    <div class="models-header">
      <h2>模型管理</h2>
      <p>管理您的本地 AI 模型，支持下载、切换和配置</p>
    </div>

    <div class="models-content">
      <!-- 当前模型状态 -->
      <div class="current-model-section">
        <h3>当前模型</h3>
        <div class="current-model-card">
          <div class="model-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
          </div>
          <div class="model-info">
            <div class="model-name">{{ currentModel.name }}</div>
            <div class="model-details">
              <span class="model-size">{{ currentModel.size }}</span>
              <span class="model-version">{{ currentModel.version }}</span>
              <span class="model-status active">已加载</span>
            </div>
          </div>
          <div class="model-performance">
            <div class="performance-item">
              <span class="label">GPU使用</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: currentModel.gpuUsage + '%' }"></div>
              </div>
              <span class="value">{{ currentModel.gpuUsage }}%</span>
            </div>
            <div class="performance-item">
              <span class="label">内存占用</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: currentModel.memoryUsage + '%' }"></div>
              </div>
              <span class="value">{{ currentModel.memoryUsage }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 本地模型列表 -->
      <div class="local-models-section">
        <div class="section-header">
          <h3>本地模型</h3>
          <button class="refresh-btn" @click="refreshModels">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
            </svg>
            刷新
          </button>
        </div>
        
        <div class="models-grid">
          <div 
            v-for="model in localModels" 
            :key="model.id"
            class="model-card"
            :class="{ active: model.id === currentModel.id }"
            @click="switchModel(model)"
          >
            <div class="model-header">
              <div class="model-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                </svg>
              </div>
              <div class="model-actions">
                <button 
                  class="action-btn"
                  @click.stop="deleteModel(model)"
                  title="删除模型"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <div class="model-name">{{ model.name }}</div>
            <div class="model-details">
              <span class="model-size">{{ model.size }}</span>
              <span class="model-version">{{ model.version }}</span>
            </div>
            
            <div class="model-status" :class="model.status">
              {{ model.status === 'active' ? '已加载' : '可用' }}
            </div>
          </div>
          
          <div class="add-model-card" @click="showAddModelModal = true">
            <div class="add-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
            </div>
            <div class="add-text">添加新模型</div>
          </div>
        </div>
      </div>

      <!-- 模型库 -->
      <div class="model-library-section">
        <div class="section-header">
          <h3>模型库</h3>
          <div class="search-box">
            <input 
              v-model="searchQuery"
              type="text"
              placeholder="搜索模型..."
              class="search-input"
            >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
          </div>
        </div>
        
        <div class="library-grid">
          <div 
            v-for="model in filteredLibraryModels" 
            :key="model.name"
            class="library-model-card"
          >
            <div class="model-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
              </svg>
            </div>
            
            <div class="model-info">
              <div class="model-name">{{ model.name }}</div>
              <div class="model-description">{{ model.description }}</div>
              <div class="model-tags">
                <span v-for="tag in model.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
            
            <div class="model-actions">
              <button 
                class="download-btn"
                @click="downloadModel(model)"
                :disabled="model.downloading"
              >
                <span v-if="model.downloading">下载中...</span>
                <span v-else>下载</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加模型模态框 -->
    <div v-if="showAddModelModal" class="modal-overlay" @click="showAddModelModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>添加新模型</h3>
          <button class="close-btn" @click="showAddModelModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="input-group">
            <label>模型名称</label>
            <input v-model="newModel.name" type="text" placeholder="例如: llama2">
          </div>
          
          <div class="input-group">
            <label>模型版本</label>
            <input v-model="newModel.version" type="text" placeholder="例如: latest">
          </div>
          
          <div class="input-group">
            <label>模型大小</label>
            <input v-model="newModel.size" type="text" placeholder="例如: 3.8GB">
          </div>
          
          <div class="input-group">
            <label>模型描述</label>
            <textarea v-model="newModel.description" placeholder="模型的功能描述..."></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAddModelModal = false">取消</button>
          <button class="btn-primary" @click="addCustomModel">添加模型</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const searchQuery = ref('')
const showAddModelModal = ref(false)
const newModel = ref({
  name: '',
  version: 'latest',
  size: '',
  description: ''
})

// 模拟数据
const currentModel = ref({
  id: 'llama2',
  name: 'Llama 2',
  version: '7b-chat',
  size: '3.8GB',
  status: 'active',
  gpuUsage: 45,
  memoryUsage: 68
})

const localModels = ref([
  { id: 'llama2', name: 'Llama 2', version: '7b-chat', size: '3.8GB', status: 'active' },
  { id: 'codellama', name: 'Code Llama', version: '7b', size: '3.8GB', status: 'available' },
  { id: 'mistral', name: 'Mistral', version: '7b', size: '4.1GB', status: 'available' },
  { id: 'vicuna', name: 'Vicuna', version: '7b', size: '13GB', status: 'available' }
])

const libraryModels = ref([
  { 
    name: 'Llama 2', 
    description: 'Meta 开发的最新开源大语言模型', 
    tags: ['通用', '对话', '最新'],
    downloading: false
  },
  { 
    name: 'Code Llama', 
    description: '专门用于代码生成和编程的模型', 
    tags: ['编程', '代码'],
    downloading: false
  },
  { 
    name: 'Mistral', 
    description: '高效的7B参数模型，性能优异', 
    tags: ['高效', '推理'],
    downloading: false
  },
  { 
    name: 'Vicuna', 
    description: '基于LLaMA的对话优化模型', 
    tags: ['对话', '优化'],
    downloading: false
  },
  { 
    name: 'WizardCoder', 
    description: '专门针对代码任务的 Wizard 模型', 
    tags: ['编程', '代码'],
    downloading: false
  },
  { 
    name: 'Phi-2', 
    description: '微软开发的小型但强大的模型', 
    tags: ['小型', '高效'],
    downloading: false
  }
])

// 计算属性
const filteredLibraryModels = computed(() => {
  if (!searchQuery.value) return libraryModels.value
  
  const query = searchQuery.value.toLowerCase()
  return libraryModels.value.filter(model => 
    model.name.toLowerCase().includes(query) ||
    model.description.toLowerCase().includes(query) ||
    model.tags.some(tag => tag.toLowerCase().includes(query))
  )
})

// 方法
const refreshModels = () => {
  // 模拟刷新模型列表
  console.log('刷新模型列表...')
}

const switchModel = (model) => {
  if (model.id === currentModel.value.id) return
  
  currentModel.value = { ...model, status: 'active', gpuUsage: 45, memoryUsage: 68 }
  chatStore.modelSettings.currentModel = model.name
  
  // 更新其他模型的状态
  localModels.value.forEach(m => {
    m.status = m.id === model.id ? 'active' : 'available'
  })
}

const deleteModel = (model) => {
  if (model.status === 'active') {
    alert('无法删除当前正在使用的模型')
    return
  }
  
  if (confirm(`确定要删除模型 "${model.name}" 吗？`)) {
    localModels.value = localModels.value.filter(m => m.id !== model.id)
  }
}

const downloadModel = (model) => {
  model.downloading = true
  
  // 模拟下载过程
  setTimeout(() => {
    const newModel = {
      id: model.name.toLowerCase().replace(/\s+/g, '-'),
      name: model.name,
      version: 'latest',
      size: '3.8GB',
      status: 'available'
    }
    
    localModels.value.push(newModel)
    model.downloading = false
    
    alert(`模型 "${model.name}" 下载完成！`)
  }, 2000)
}

const addCustomModel = () => {
  if (!newModel.value.name.trim()) {
    alert('请输入模型名称')
    return
  }
  
  const model = {
    id: newModel.value.name.toLowerCase().replace(/\s+/g, '-'),
    name: newModel.value.name,
    version: newModel.value.version || 'latest',
    size: newModel.value.size || '未知',
    status: 'available'
  }
  
  localModels.value.push(model)
  showAddModelModal.value = false
  
  // 重置表单
  newModel.value = {
    name: '',
    version: 'latest',
    size: '',
    description: ''
  }
}

onMounted(() => {
  refreshModels()
})
</script>

<style scoped>
.models-view {
  padding: var(--spacing-l);
  height: 100%;
  overflow-y: auto;
  background-color: var(--white);
}

.models-header {
  margin-bottom: var(--spacing-xl);
}

.models-header h2 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-s);
}

.models-header p {
  color: var(--medium-gray);
  margin: 0;
}

/* 当前模型部分 */
.current-model-section {
  margin-bottom: var(--spacing-xl);
}

.current-model-section h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-m);
}

.current-model-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-l);
  padding: var(--spacing-l);
  background: linear-gradient(135deg, var(--light-blue), var(--white));
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.model-icon {
  color: var(--primary-blue);
}

.model-info {
  flex: 1;
}

.model-name {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-xs);
}

.model-details {
  display: flex;
  gap: var(--spacing-l);
  font-size: var(--text-sm);
  color: var(--medium-gray);
}

.model-status {
  padding: var(--spacing-xs) var(--spacing-s);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.model-status.active {
  background-color: var(--success);
  color: var(--white);
}

.model-performance {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-s);
  min-width: 200px;
}

.performance-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-s);
}

.performance-item .label {
  font-size: var(--text-xs);
  color: var(--medium-gray);
  min-width: 60px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: var(--light-gray);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-blue), var(--secondary-blue));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.performance-item .value {
  font-size: var(--text-xs);
  color: var(--medium-gray);
  min-width: 30px;
  text-align: right;
}

/* 本地模型部分 */
.local-models-section {
  margin-bottom: var(--spacing-xl);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-m);
}

.section-header h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin: 0;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-s) var(--spacing-m);
  border: 1px solid var(--light-gray);
  background-color: var(--white);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--medium-gray);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.refresh-btn:hover {
  border-color: var(--primary-blue);
  color: var(--primary-blue);
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-m);
}

.model-card {
  padding: var(--spacing-l);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  background-color: var(--white);
}

.model-card:hover {
  border-color: var(--primary-blue);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.model-card.active {
  border-color: var(--primary-blue);
  background-color: var(--light-blue);
}

.model-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-m);
}

.model-actions {
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.model-card:hover .model-actions {
  opacity: 1;
}

.action-btn {
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
  transition: all 0.2s ease-in-out;
}

.action-btn:hover {
  background-color: var(--error);
  color: var(--white);
}

.model-card .model-name {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-xs);
}

.model-card .model-details {
  display: flex;
  gap: var(--spacing-m);
  font-size: var(--text-xs);
  color: var(--medium-gray);
  margin-bottom: var(--spacing-m);
}

.model-card .model-status {
  padding: var(--spacing-xs) var(--spacing-s);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  text-align: center;
}

.model-card .model-status.available {
  background-color: var(--light-gray);
  color: var(--medium-gray);
}

.add-model-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  border: 2px dashed var(--medium-gray);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  background-color: var(--light-gray);
}

.add-model-card:hover {
  border-color: var(--primary-blue);
  background-color: var(--light-blue);
}

.add-icon {
  color: var(--medium-gray);
  margin-bottom: var(--spacing-s);
}

.add-model-card:hover .add-icon {
  color: var(--primary-blue);
}

.add-text {
  font-size: var(--text-sm);
  color: var(--medium-gray);
  font-weight: var(--font-medium);
}

.add-model-card:hover .add-text {
  color: var(--primary-blue);
}

/* 模型库部分 */
.model-library-section {
  margin-bottom: var(--spacing-xl);
}

.search-box {
  position: relative;
  width: 300px;
}

.search-input {
  width: 100%;
  padding: var(--spacing-s) var(--spacing-m) var(--spacing-s) var(--spacing-xl);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.search-box svg {
  position: absolute;
  left: var(--spacing-s);
  top: 50%;
  transform: translateY(-50%);
  color: var(--medium-gray);
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing-m);
}

.library-model-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-m);
  padding: var(--spacing-l);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-lg);
  background-color: var(--white);
}

.library-model-card .model-icon {
  color: var(--primary-blue);
  flex-shrink: 0;
}

.library-model-card .model-info {
  flex: 1;
}

.library-model-card .model-name {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-xs);
}

.library-model-card .model-description {
  font-size: var(--text-sm);
  color: var(--medium-gray);
  margin-bottom: var(--spacing-s);
  line-height: 1.4;
}

.model-tags {
  display: flex;
  gap: var(--spacing-xs);
}

.tag {
  padding: 2px 8px;
  background-color: var(--light-gray);
  color: var(--medium-gray);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.download-btn {
  padding: var(--spacing-s) var(--spacing-m);
  background-color: var(--primary-blue);
  color: var(--white);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;
}

.download-btn:hover:not(:disabled) {
  background-color: var(--primary-blue-hover);
}

.download-btn:disabled {
  background-color: var(--light-gray);
  color: var(--medium-gray);
  cursor: not-allowed;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-l);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-l);
}

.modal-header h3 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--dark-gray);
  margin: 0;
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

.modal-body {
  margin-bottom: var(--spacing-l);
}

.input-group {
  margin-bottom: var(--spacing-m);
}

.input-group label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--dark-gray);
  margin-bottom: var(--spacing-xs);
}

.input-group input,
.input-group textarea {
  width: 100%;
  padding: var(--spacing-s) var(--spacing-m);
  border: 1px solid var(--light-gray);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-family: inherit;
}

.input-group textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-footer {
  display: flex;
  gap: var(--spacing-m);
  justify-content: flex-end;
}

.btn-primary,
.btn-secondary {
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

/* 响应式设计 */
@media (max-width: 768px) {
  .models-view {
    padding: var(--spacing-m);
  }
  
  .current-model-card {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-m);
  }
  
  .models-grid,
  .library-grid {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-m);
  }
  
  .search-box {
    width: 100%;
  }
  
  .modal-content {
    width: 95%;
    margin: var(--spacing-m);
  }
}
</style>