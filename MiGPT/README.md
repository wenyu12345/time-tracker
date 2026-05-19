# MiGPT 本地部署说明

## 项目简介

MiGPT 是一个开源项目，它将小米智能音箱与 ChatGPT 和豆包等大语言模型连接起来，为小爱同学增添 AI 能力。

## 目录结构

```
MiGPT/
├── package.json         # Node.js 项目配置
├── index.js            # 启动脚本
├── .env                # 环境变量配置（需手动创建）
├── .env.example        # 环境变量示例
├── .migpt.js           # MiGPT 详细配置
├── docker-compose.yml  # Docker Compose 配置
├── docker-start.bat    # Docker 启动脚本
├── install.bat         # Node.js 依赖安装脚本
├── start.bat           # Node.js 启动脚本
└── README.md           # 部署说明文档
```

## 快速开始

### 方法一：Node.js 部署（推荐开发者使用）

1. **前置条件**
   - 已安装 Node.js 14.x 或更高版本
   - 已安装 npm

2. **配置环境变量**
   ```
   # 复制示例文件并编辑
   复制 .env.example 并命名为 .env
   使用文本编辑器打开 .env 文件
   填写小米账户信息和 API 密钥
   ```

3. **安装依赖**
   ```
   双击运行 install.bat
   ```

4. **启动服务**
   ```
   双击运行 start.bat
   ```

### 方法二：Docker 部署（推荐非技术用户使用）

1. **前置条件**
   - 已安装 Docker Desktop
   - Docker 服务已启动

2. **配置环境变量**
   ```
   # 复制示例文件并编辑
   复制 .env.example 并命名为 .env
   使用文本编辑器打开 .env 文件
   填写小米账户信息和 API 密钥
   ```

3. **启动服务**
   ```
   双击运行 docker-start.bat
   ```

## 详细配置说明

### 1. 环境变量配置 (.env)

```
# 小米账户信息（必填）
MI_USER_ID=你的小米账号
MI_PASSWORD=你的小米密码
MI_SPEAKER_DID=你的小爱音箱名称或ID

# OpenAI API 密钥（使用 OpenAI 模型时必填）
# OPENAI_API_KEY=sk-...

# 豆包 API 密钥（使用豆包模型时必填）
# DOUBAO_API_KEY=...

# 日志级别（可选，默认 info）
LOG_LEVEL=info

# 端口（可选，默认 3000）
PORT=3000
```

### 2. MiGPT 配置 (.migpt.js)

主要配置项说明：

- **speaker**: 小爱音箱配置
  - `userId`: 小米账号
  - `password`: 小米密码
  - `did`: 小爱音箱名称或ID

- **llm**: 大模型配置
  - `provider`: 模型提供商，可选 'openai' 或 'doubao'
  - 详细参数可在对应子配置中调整

- **response**: 响应配置
  - `stream`: 是否启用流式响应
  - `prefix`: 响应前缀

- **memory**: 记忆配置
  - `enabled`: 是否启用记忆功能
  - `shortTermLimit`: 短期记忆消息数量
  - `longTermHours`: 长期记忆持续时间

## 使用说明

1. **连接音箱**
   - 确保小爱音箱与计算机在同一局域网内
   - 确保 `.env` 文件中的音箱名称或 ID 正确

2. **唤醒和使用**
   - 正常唤醒小爱同学："小爱同学"
   - 使用 AI 能力："小爱同学，请..."
   - 模型会根据配置自动回复

## 常见问题排查

1. **连接失败**
   - 检查网络连接
   - 确认小米账号密码正确
   - 确认音箱名称或 ID 正确

2. **响应异常**
   - 检查 API 密钥配置
   - 查看 logs 目录下的日志文件
   - 确认模型提供商设置正确

3. **Docker 相关问题**
   - 确保 Docker Desktop 已启动
   - 检查防火墙设置
   - 尝试使用管理员权限运行脚本

## 注意事项

1. 请妥善保管您的账户信息和 API 密钥
2. 首次启动可能需要一些时间连接和初始化
3. 建议定期更新镜像或依赖以获取最新功能
4. 如果出现问题，请先查看日志文件获取详细错误信息

## 技术支持

如有问题，请参考 GitHub 项目页面：https://github.com/idootop/mi-gpt