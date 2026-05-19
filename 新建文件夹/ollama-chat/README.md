# Ollama Chat - 本地大模型聊天界面

一个现代化的 Ollama 本地大模型网页聊天界面，提供直观的交互体验，支持多模型管理、实时对话、参数调优和历史记录管理等核心功能。

## ✨ 功能特性

### 🎯 核心功能
- **智能对话**: 实时消息发送与接收，支持流式输出
- **多模型管理**: 本地模型切换、下载和状态监控
- **参数调优**: 温度、最大长度、Top P 等参数调节
- **对话管理**: 历史记录管理、导出分享功能
- **个性化设置**: 主题切换、快捷键配置、通知设置

### 🎨 界面设计
- **三栏布局**: 左侧模型管理，中央聊天区域，右侧参数设置
- **响应式设计**: 支持桌面端、平板端和移动端
- **主题支持**: 浅色/深色主题，自动跟随系统
- **现代化UI**: 基于 Vue 3 + Tailwind CSS 的现代化设计

### 🔧 技术特性
- **实时通信**: WebSocket 支持，实现实时消息推送
- **性能优化**: 虚拟滚动、懒加载、缓存策略
- **无障碍设计**: 键盘导航、屏幕阅读器支持
- **安全考虑**: 输入验证、本地存储加密

## 🚀 快速开始

### 环境要求
- Node.js 16.0 或更高版本
- Ollama 本地服务（可选，用于真实 AI 对话）

### 安装依赖
```bash
cd ollama-chat
npm install
```

### 启动开发服务器
```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本
```bash
npm run build
```

### 预览生产版本
```bash
npm run preview
```

## 📁 项目结构

```
ollama-chat/
├── src/
│   ├── components/     # 可复用组件
│   ├── views/          # 页面视图
│   ├── layouts/        # 布局组件
│   ├── stores/         # 状态管理
│   ├── router/         # 路由配置
│   ├── styles/         # 样式文件
│   └── main.js         # 应用入口
├── public/             # 静态资源
├── index.html          # HTML 模板
├── vite.config.js      # Vite 配置
└── package.json        # 项目配置
```

## 🎯 主要功能

### 1. 智能对话
- 实时消息发送与接收
- 流式输出，逐字显示
- 多轮对话上下文记忆
- 对话主题智能识别

### 2. 模型管理
- 本地模型列表展示
- 模型快速切换
- 模型状态监控（GPU/CPU 使用率）
- 模型下载和删除

### 3. 参数调优
- **Temperature**: 控制输出随机性 (0.01-1.0)
- **Max Length**: 控制回复长度 (0-32768)
- **Top P**: 控制词汇多样性 (0-1)
- **System Prompt**: 自定义 AI 角色

### 4. 对话管理
- 对话历史列表
- 会话命名和搜索
- 对话导出（Markdown/TXT）
- 截图分享功能

### 5. 个性化设置
- 浅色/深色主题切换
- 字体大小调节
- 快捷键配置
- 通知设置

## 🎨 界面布局

### 整体布局
- **顶部导航栏**: Logo、连接状态、主题切换
- **左侧边栏**: 模型选择、对话历史
- **中央聊天区**: 消息展示、输入区域
- **右侧面板**: 参数设置、模型信息
- **底部状态栏**: 系统信息、快捷操作

### 响应式设计
- **桌面端** (≥1200px): 完整三栏布局
- **平板端** (768px-1199px): 可折叠侧边栏
- **移动端** (<768px): 单栏布局，侧边栏滑出

## 🔧 技术栈

### 前端框架
- **Vue 3**: 渐进式 JavaScript 框架
- **Vue Router**: 官方路由管理器
- **Pinia**: 状态管理库

### UI & 样式
- **Tailwind CSS**: 实用优先的 CSS 框架
- **Lucide Icons**: 精美的图标库
- **自定义设计系统**: 完整的色彩和间距规范

### 工具链
- **Vite**: 下一代前端构建工具
- **TypeScript**: 类型安全的 JavaScript
- **ESLint + Prettier**: 代码质量和格式化

### 功能增强
- **Marked**: Markdown 渲染
- **Prism.js**: 代码语法高亮
- **WebSocket**: 实时通信

## ⚙️ 配置说明

### 环境变量
创建 `.env` 文件配置环境变量：

```env
VITE_OLLAMA_BASE_URL=http://localhost:11434
VITE_APP_TITLE=Ollama Chat
VITE_APP_VERSION=1.0.0
```

### Ollama 集成
要连接真实的 Ollama 服务，需要：

1. 安装并启动 Ollama
2. 下载所需的 AI 模型
3. 配置正确的 API 端点

## 🎮 快捷键

| 功能 | 快捷键 |
|------|--------|
| 发送消息 | `Enter` |
| 换行 | `Shift + Enter` |
| 新建对话 | `Ctrl + N` |
| 切换模型 | `Ctrl + M` |
| 打开设置 | `Ctrl + ,` |
| 切换主题 | `Ctrl + T` |

## 📱 移动端支持

- 触摸友好的界面元素
- 手势操作支持
- 响应式布局适配
- 移动端优化交互

## 🔒 安全特性

- 输入验证和过滤
- XSS 防护
- CSRF 防护
- 本地数据加密存储
- 权限控制机制

## 🚀 部署指南

### 静态部署
```bash
npm run build
# 将 dist 目录部署到静态服务器
```

### Docker 部署
```dockerfile
FROM nginx:alpine
COPY dist /usr/share/nginx/html
EXPOSE 80
```

### 本地部署
支持本地离线使用，所有资源本地化。

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 开发流程
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 代码规范
- 使用 ESLint + Prettier
- 遵循 Vue 3 风格指南
- 编写清晰的注释
- 添加适当的测试

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Ollama](https://ollama.ai/) - 本地 AI 模型运行环境
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的 CSS 框架
- [Lucide](https://lucide.dev/) - 精美的图标库

## 📞 支持与反馈

如果您遇到问题或有建议：

1. 查看 [问题追踪](https://github.com/your-repo/issues)
2. 提交新的 Issue
3. 加入讨论社区

---

**Ollama Chat** - 让本地 AI 对话更简单、更优雅！ 🚀