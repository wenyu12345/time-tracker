# Ollama Chat 配置说明

## 功能特性

✅ **完整的Ollama集成**
- 自动连接本地Ollama服务
- 实时显示模型列表和状态
- 支持所有Ollama API参数
- 错误处理和重连机制

✅ **现代化界面设计**
- 三栏式布局（模型管理 + 聊天 + 参数设置）
- 深色/浅色主题切换
- 响应式设计，适配不同屏幕
- 实时消息流显示

✅ **完整对话管理**
- 多轮对话上下文保持
- 对话历史本地存储
- 新建/切换对话会话
- 对话标题自动生成

## 使用前准备

### 1. 安装Ollama
```bash
# Windows
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. 下载模型
```bash
# 下载常用模型
ollama pull llama2
ollama pull mistral
ollama pull codellama

# 查看已下载模型
ollama list
```

### 3. 启动Ollama服务
```bash
# 启动服务（默认端口11434）
ollama serve
```

### 4. 解决CORS问题（重要）

由于浏览器安全限制，需要配置Ollama允许跨域访问：

**方法1：启动时设置环境变量**
```bash
set OLLAMA_ORIGINS=* && ollama serve
```

**方法2：修改Ollama配置**
1. 找到Ollama配置文件位置
2. 添加或修改配置：
```yaml
# config.yaml
origins:
  - "*"
```

## 界面使用方法

### 1. 连接Ollama
- 界面启动后会自动连接本地Ollama服务
- 连接状态显示在左侧边栏顶部
- 如果连接失败，检查Ollama服务是否运行

### 2. 选择模型
- 在左侧下拉菜单选择已下载的模型
- 模型信息显示在右侧面板
- 支持模型大小和参数显示

### 3. 调整参数
- **温度** (Temperature): 控制回复随机性 (0-1)
- **最大长度** (Max Tokens): 控制回复长度 (0-32768)
- **Top P**: 控制词汇多样性 (0-1)

### 4. 开始对话
- 在中央输入框输入消息
- 按Enter发送，Shift+Enter换行
- AI回复实时显示，支持多轮对话

## 故障排除

### 连接失败
1. **检查Ollama服务状态**
   ```bash
   curl http://localhost:11434/api/tags
   ```
   
2. **检查端口占用**
   ```bash
   netstat -an | findstr :11434
   ```

3. **检查防火墙设置**
   - 确保11434端口未被防火墙阻止
   - 允许Ollama通过防火墙

### CORS错误
如果出现跨域错误，确保已配置Ollama允许跨域访问：

**Windows PowerShell:**
```powershell
$env:OLLAMA_ORIGINS="*"
ollama serve
```

**macOS/Linux:**
```bash
export OLLAMA_ORIGINS="*"
ollama serve
```

### 模型加载失败
1. 检查模型是否已下载：`ollama list`
2. 重新下载模型：`ollama pull <model-name>`
3. 检查磁盘空间是否充足

## API接口说明

界面使用以下Ollama API端点：

- `GET /api/tags` - 获取模型列表
- `POST /api/chat` - 发送聊天消息
- `POST /api/generate` - 生成文本

### 请求示例
```javascript
// 聊天请求
{
  "model": "llama2",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "options": {
    "temperature": 0.7,
    "num_predict": 2048,
    "top_p": 0.9
  },
  "stream": false
}
```

## 开发说明

### 项目结构
```
ollama-chat/
├── ollama-chat.html          # 主界面文件
├── simple-chat.html          # 演示版本
├── README-OLLAMA.md          # 配置说明
└── README.md                 # 项目说明
```

### 技术栈
- 纯HTML/CSS/JavaScript实现
- 使用Fetch API进行HTTP请求
- 本地存储管理对话历史
- 响应式CSS设计

### 自定义配置
可以修改以下配置：

**API地址配置**
```javascript
const OLLAMA_API = {
  baseUrl: 'http://localhost:11434',  // 修改为您的Ollama地址
  // ...
};
```

**界面主题**
- 通过右上角按钮切换主题
- 主题设置自动保存到本地存储

## 更新日志

### v1.0.0
- ✅ 完整的Ollama API集成
- ✅ 实时模型列表加载
- ✅ 参数调优界面
- ✅ 多主题支持
- ✅ 错误处理和重连机制

## 技术支持

如有问题，请检查：
1. Ollama服务是否正常运行
2. 浏览器控制台错误信息
3. 网络连接和防火墙设置
4. CORS配置是否正确

---

**注意**: 确保Ollama服务在本地11434端口运行，并已配置允许跨域访问。