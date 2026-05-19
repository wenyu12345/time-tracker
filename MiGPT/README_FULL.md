# MiGPT 完整服务使用说明

## 功能介绍

这是MiGPT的完整服务版本，可以通过小爱音箱与豆包、OpenAI等大语言模型进行交互，支持完整的语音对话、上下文记忆和自定义配置功能。

## 系统要求

- Node.js 16.x 或更高版本
- npm 8.x 或更高版本
- 稳定的网络连接
- 已在米家APP中配置的小爱音箱

## 安装步骤

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

编辑 `.env` 文件，填入以下配置信息：

```env
# 小米账号信息 - 请根据实际情况修改
MI_USER_ID=1487810896  # 注意：不是手机号或邮箱，请在「个人信息」-「小米 ID」查看
MI_PASSWORD=your_password
MI_SPEAKER_DID=your_speaker_name  # 小爱音箱 ID 或在米家中设置的名称

# 大模型配置（可选，至少选择一个）
# OPENAI_API_KEY=your_openai_api_key
# DOUBAO_API_KEY=your_doubao_api_key

# 日志级别
LOG_LEVEL=info
```

### 3. 初始化数据库

```bash
npm run init-db
```

## 启动服务

执行以下命令启动MiGPT服务：

```bash
npm start
```

## 使用方法

1. 服务启动后，会自动连接到配置的小爱音箱
2. 通过语音指令 "小爱同学，请xxx" 或 "小爱同学，你xxx" 来与AI互动
3. 支持上下文对话，可以连续提问
4. 对话记录和日志保存在 `logs` 目录中

## 配置说明

### 豆包配置

如果要使用豆包AI，请在.env文件中添加：

```env
DOUBAO_API_KEY=your_doubao_api_key
```

### OpenAI配置

如果要使用OpenAI的API，请在.env文件中添加：

```env
OPENAI_API_KEY=your_openai_api_key
```

## 常见问题

### 连接失败
- 检查小米账号信息是否正确
- 确认小爱音箱处于同一网络环境
- 验证账号密码是否准确

### 数据库初始化失败
- 确保Node.js和npm版本符合要求
- 检查数据库文件是否有写入权限

## 停止服务

在终端中按下 `Ctrl + C` 键停止服务。