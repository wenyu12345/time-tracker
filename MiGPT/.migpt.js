// MiGPT 详细配置文件
module.exports = {
  // 小爱音箱配置
  speaker: {
    userId: process.env.MI_USER_ID, // 从环境变量中读取小米账号ID
    password: process.env.MI_PASSWORD, // 从环境变量中读取小米账号密码
    did: '小爱音箱Play', // 小爱音箱名称
    // 以下为可选配置
    // ip: '192.168.1.100', // 可选，指定音箱IP地址
    // port: 54321, // 可选，指定音箱端口
  },
  
  // 大模型配置
  llm: {
    // 支持 'openai' 或 'doubao' 或其他模型
    provider: 'openai', // 默认使用 OpenAI
    
    // OpenAI 配置
    openai: {
      apiKey: '', // 留空则从环境变量获取
      // 可选配置
      model: 'gpt-3.5-turbo', // 使用的模型
      temperature: 0.7, // 生成回复的随机性
    },
    
    // 豆包配置
    doubao: {
      apiKey: '', // 留空则从环境变量获取
      // 可选配置
      model: 'ERNIE-Bot-4', // 使用的豆包模型
    },
  },
  
  // 响应配置
  response: {
    // 是否使用流式响应
    stream: true,
    // 响应前缀，可自定义小爱音箱回答的开头
    prefix: '',
  },
  
  // 记忆配置
  memory: {
    // 是否启用记忆功能
    enabled: true,
    // 短期记忆消息数量
    shortTermLimit: 10,
    // 长期记忆持续时间（小时）
    longTermHours: 24,
  },
  
  // TTS（文本转语音）配置
  tts: {
    // 是否使用自定义 TTS
    custom: false,
    // 自定义 TTS 配置
    // 如果不使用自定义 TTS，则使用小爱音箱默认语音
  },
  
  // 智能家居配置
  smartHome: {
    // 是否启用智能家居功能
    enabled: false,
    // 智能家居设备配置
    devices: [],
  },
  
  // 唤醒配置
  wake: {
    // 自定义唤醒词配置
    keywords: [
      '小爱同学，请',
      '小爱同学，你',
      '小爱同学，召唤',
    ],
  },
  
  // 日志配置
  log: {
    level: 'info', // 日志级别：debug, info, warn, error
    file: './logs/mi-gpt.log', // 日志文件路径
  },
};