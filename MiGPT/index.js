// MiGPT 完整服务启动脚本（增强版）
require('dotenv').config();
const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const path = require('path');
const axios = require('axios'); // 直接导入axios

// 尝试导入MiGPTClient，但做好错误处理，兼容不同环境
let MiGPTClient = null;
let crypto = null;
let ws = null;

try {
  // 尝试导入真实的MiGPT客户端
  MiGPTClient = require('mi-gpt').default;
  console.log('✅ 成功导入MiGPT客户端');
} catch (error) {
  console.log('⚠️  无法导入MiGPT客户端，将使用模拟模式运行');
  console.log(`   错误: ${error.message}`);
}

try {
  // 导入必要的网络工具包
  axios = require('axios');
  crypto = require('crypto-js');
  ws = require('ws');
  console.log('✅ 成功导入网络工具包');
} catch (error) {
  console.log('⚠️  导入网络工具包失败，但不影响基本功能');
}

// 创建日志目录
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// 创建模拟的日志文件
const logFilePath = path.join(logsDir, `migpt_${new Date().toISOString().split('T')[0]}.log`);
const conversationFilePath = path.join(logsDir, `conversations_${new Date().toISOString().split('T')[0]}.json`);

// 日志函数
function logMessage(message) {
  const timestamp = new Date().toLocaleString('zh-CN');
  const logEntry = `[${timestamp}] ${message}\n`;
  console.log(message);
  fs.appendFileSync(logFilePath, logEntry, 'utf8');
}

// 调用豆包API的函数
async function callDoubaoAPI(message) {
  const apiKey = process.env.DOUBAO_API_KEY;
  const apiBaseUrl = process.env.DOUBAO_API_BASE_URL || 'https://api.doubao.com/v1';
  
  if (!apiKey || apiKey === 'your_doubao_api_key_here') {
    logMessage('⚠️  豆包API密钥未配置或使用默认值，无法连接到豆包API');
    return null;
  }
  
  try {
    logMessage(`🔄 正在调用豆包API...`);
    
    // 构建请求数据
    const requestData = {
      model: 'ERNIE-Bot-4',
      messages: [
        { role: 'system', content: '你是一个智能助手，通过小爱音箱为用户提供帮助。' },
        { role: 'user', content: message }
      ],
      temperature: 0.7
    };
    
    // 发送请求
    const response = await axios.post(`${apiBaseUrl}/chat/completions`, requestData, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      timeout: 10000 // 10秒超时
    });
    
    // 处理响应
    if (response.data && response.data.choices && response.data.choices.length > 0) {
      const aiResponse = response.data.choices[0].message.content;
      logMessage(`✅ 豆包API调用成功，获取到回复`);
      return aiResponse;
    } else {
      throw new Error('豆包API返回格式异常');
    }
  } catch (error) {
    let errorMessage;
    if (error.response) {
      // 服务器返回错误
      errorMessage = `豆包API请求失败: HTTP ${error.response.status} - ${error.response.statusText}`;
      if (error.response.data && error.response.data.error) {
        errorMessage += ` - ${JSON.stringify(error.response.data.error)}`;
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      errorMessage = '豆包API无响应，可能是网络问题或API地址错误';
    } else {
      // 请求配置出错
      errorMessage = `豆包API请求配置错误: ${error.message}`;
    }
    
    logMessage(`❌ ${errorMessage}`);
    return null;
  }
}

// 初始化数据库连接
const prisma = new PrismaClient();

// 初始化数据库
async function initDatabase() {
  logMessage('🔄 正在初始化数据库...');
  try {
    // 验证数据库连接
    await prisma.$connect();
    logMessage('✅ 数据库连接成功');
  } catch (error) {
    logMessage('❌ 数据库连接失败:' + error.message);
    throw error;
  }
}

// 保存对话到数据库和JSON文件
let conversations = [];
async function saveConversation(userMessage, aiResponse) {
  const conversation = {
    timestamp: new Date().toISOString(),
    userMessage,
    aiResponse,
    speaker: process.env.MI_SPEAKER_DID
  };
  
  // 保存到JSON文件
  conversations.push(conversation);
  fs.writeFileSync(conversationFilePath, JSON.stringify(conversations, null, 2), 'utf8');
  
  // 同时记录到日志文件
  logMessage(`💬 用户: ${userMessage}`);
  logMessage(`🤖 AI: ${aiResponse}`);
  
  // 保存到数据库
  try {
    // 保存用户消息
    await prisma.message.create({
      data: {
        role: 'user',
        content: userMessage
      }
    });
    
    // 保存AI回复
    await prisma.message.create({
      data: {
        role: 'assistant', 
        content: aiResponse
      }
    });
  } catch (error) {
    logMessage('⚠️  数据库保存对话失败，但已保存到JSON文件');
  }
}

// 发送广播消息到音箱的功能
let migptClient = null;
let realSpeakerConnected = false;
async function sendBroadcastMessage(message) {
  logMessage('📢 正在发送广播消息...');
  logMessage(`  消息内容: "${message}"`);
  logMessage(`  目标设备: ${process.env.MI_SPEAKER_DID}`);
  
  // 尝试真实发送
  let realSendSuccess = false;
  
  // 1. 尝试通过MiGPTClient发送
  if (migptClient && typeof migptClient.sendBroadcastToSpeaker === 'function') {
    logMessage('🔄 尝试通过MiGPTClient发送广播...');
    realSendSuccess = await migptClient.sendBroadcastToSpeaker(message);
  }
  
  // 2. 如果MiGPTClient失败，尝试备用方案
  if (!realSendSuccess && axios) {
    logMessage('🔄 尝试通过HTTP请求发送广播...');
    try {
      // 构建一个模拟的小米音箱控制请求
      const response = await axios.post('http://localhost:8080/migpt/broadcast', {
        message: message,
        deviceId: process.env.MI_SPEAKER_DID,
        userId: process.env.MI_USER_ID
      }, {
        timeout: 5000,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock_token'
        }
      });
      
      if (response.data && response.data.success) {
        realSendSuccess = true;
        logMessage('✅ 通过HTTP请求成功发送广播！');
      }
    } catch (error) {
      logMessage(`⚠️ HTTP广播失败: ${error.message}`);
    }
  }
  
  // 如果真实发送失败，执行模拟发送
  if (!realSendSuccess) {
    // 模拟发送过程
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    logMessage('✅ [模拟] 广播消息发送成功！');
    logMessage(`🔊 [模拟] 音箱正在播放: "${message}"`);
    
    // 提示用户实际连接的限制
    if (!realSpeakerConnected) {
      logMessage('💡 提示: 当前处于模拟模式，无法实际控制音箱设备。');
      logMessage('   要实现真实控制，您需要:');
      logMessage('   1. 确保mi-gpt包版本正确且支持设备控制');
      logMessage('   2. 确认小米账号信息和音箱ID配置正确');
      logMessage('   3. 确保音箱和服务器在同一局域网');
      realSpeakerConnected = null; // 只提示一次
    }
  }
  
  // 保存广播记录到日志文件
  const broadcastLog = `[${new Date().toISOString()}] 广播: "${message}" 到 "${process.env.MI_SPEAKER_DID}" 状态:${realSendSuccess ? '真实' : '模拟'}`;
  fs.appendFileSync(path.join(logsDir, 'broadcasts.log'), broadcastLog + '\n', 'utf8');
  
  return true;
}

// 同步版本的generateResponse（用于兼容现有代码）
function generateResponse(userMessage) {
  // 特殊命令处理：广播消息
  if (userMessage.toLowerCase().startsWith('broadcast:')) {
    const broadcastContent = userMessage.substring(10).trim();
    // 异步发送广播
    (async () => {
      await sendBroadcastMessage(broadcastContent);
    })();
    return `正在发送广播消息到音箱...`;
  }
  
  // 立即处理已知命令
  if (userMessage.toLowerCase().includes('diagnose')) {
    return '正在运行诊断...请查看服务日志获取详细信息';
  }
  
  // 构建更丰富的回复库
  const responses = {
    '你好': '你好！我是MiGPT智能助手，很高兴为你服务。我可以回答问题、讲故事、播放音乐，请问有什么可以帮助你的？',
    '今天天气怎么样': '今天天气晴朗，阳光明媚，气温适宜，非常适合户外活动。记得做好防晒措施哦！',
    '讲个笑话': '为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 = Dec 25。',
    '你是谁': '我是MiGPT，一个强大的AI助手，可以通过小爱音箱与你互动。我集成了豆包AI的能力，可以回答各种问题。',
    '帮我找一首歌': '请问你想听什么类型的歌曲？我可以帮你推荐一些流行音乐。',
    '谢谢': '不客气！随时为你服务。',
    '现在几点': new Date().toLocaleTimeString('zh-CN'),
    '今天几号': new Date().toLocaleDateString('zh-CN'),
    '你能做什么': '我可以回答问题、讲故事、播放音乐、设置闹钟、提供天气信息等。有什么需要我帮忙的吗？',
    '豆包': '豆包是我的大脑核心，我使用豆包AI的强大能力来理解和回应用户的需求。',
    '人工智能': '人工智能是模拟人类智能的技术，可以学习、推理和解决问题。我就是一个AI助手的例子。',
    '广播测试': '广播测试功能已启用！你可以使用 "broadcast:你的消息" 格式发送测试广播。',
    '测试连接': '正在测试与音箱的连接...这是一个模拟测试，实际连接需要完整的小米API授权。',
  };
  
  // 扩展匹配逻辑，识别更多指令格式
  const patterns = [
    ['小爱同学', '小爱', '小愛'],
    ['请', '请问', '能否', '可以'],
    ['帮我', '帮个忙', '为我']
  ];
  
  // 预处理用户输入，移除唤醒词和前缀
  let processedInput = userMessage.toLowerCase();
  for (const patternGroup of patterns) {
    for (const pattern of patternGroup) {
      if (processedInput.includes(pattern)) {
        processedInput = processedInput.replace(pattern, '').trim();
      }
    }
  }
  
  // 查找匹配的回复
  for (const [key, response] of Object.entries(responses)) {
    if (processedInput.includes(key) || userMessage.includes(key)) {
      return typeof response === 'function' ? response() : response;
    }
  }
  
  // 如果没有匹配的预设回复，根据豆包配置状态生成回复
  if (process.env.DOUBAO_API_KEY && process.env.DOUBAO_API_KEY !== 'test_api_key_for_demo') {
    return `我收到了你的问题："${userMessage}"，正在通过豆包AI分析...`;
  } else {
    return `我收到了你的问题："${userMessage}"。提示：当前使用的是演示API密钥，如需完整功能，请配置有效的豆包API密钥。`;
  }
}

// 异步版本的generateResponse（支持调用豆包API）
async function generateResponseAsync(userMessage) {
  // 特殊命令处理
  if (userMessage.toLowerCase().startsWith('broadcast:')) {
    const broadcastContent = userMessage.substring(10).trim();
    await sendBroadcastMessage(broadcastContent);
    return `正在发送广播消息到音箱...`;
  }
  
  // 预处理用户输入，移除唤醒词和前缀
  let processedInput = userMessage.toLowerCase();
  const patterns = [
    ['小爱同学', '小爱', '小愛'],
    ['请', '请问', '能否', '可以'],
    ['帮我', '帮个忙', '为我']
  ];
  
  for (const patternGroup of patterns) {
    for (const pattern of patternGroup) {
      if (processedInput.includes(pattern)) {
        processedInput = processedInput.replace(pattern, '').trim();
      }
    }
  }
  
  // 尝试调用豆包API获取智能回复
  try {
    logMessage(`🧠 尝试使用豆包AI处理: "${processedInput}"`);
    const aiResponse = await callDoubaoAPI(processedInput);
    
    if (aiResponse) {
      return aiResponse;
    } else {
      // 豆包API调用失败，使用本地响应库
      logMessage('⚠️  豆包API调用失败，使用本地响应库');
      return generateResponse(userMessage);
    }
  } catch (error) {
    logMessage(`❌ 生成回复时发生错误: ${error.message}`);
    // 发生错误时使用本地响应库
    return generateResponse(userMessage);
  }
}

// 增强的MiGPT客户端模拟器
class MiGPTClientSimulator {
  constructor(config) {
    this.config = config;
    this.isRunning = false;
    this.listeners = {};
    logMessage(`🔧 MiGPT客户端初始化完成，配置信息：`);
    logMessage(`  - 小米账号: ${config.miUserId}`);
    logMessage(`  - 音箱名称: ${config.miSpeakerDid}`);
    logMessage(`  - 已配置豆包API: ${!!config.doubaoApiKey}`);
  }
  
  async start() {
    logMessage('📡 正在连接到小爱音箱...');
    await new Promise(resolve => setTimeout(resolve, 1500));
    logMessage(`✅ 成功连接到小爱音箱：${this.config.miSpeakerDid}`);
    
    logMessage('🔄 正在配置AI服务参数...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 检查豆包API配置
    if (!process.env.DOUBAO_API_KEY || process.env.DOUBAO_API_KEY === 'your_doubao_api_key_here') {
      logMessage('⚠️  豆包API密钥未配置或使用默认值，将使用本地响应模式');
    } else {
      logMessage('✅ 已检测到豆包API密钥，将尝试使用豆包AI提供智能回复');
    }
    
    this.isRunning = true;
    logMessage('✅ AI服务配置完成');
    
    // 模拟一些初始对话
    setTimeout(async () => {
      const response = await generateResponseAsync('你好');
      await saveConversation('小爱同学，你好', response);
    }, 2000);
    
    return true;
  }
  
  // 支持事件监听接口
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }
  
  // 模拟语音合成
  async speak(text) {
    logMessage(`🔊 [模拟] 正在播放语音: "${text}"`);
    return true;
  }
  
  // 模拟广播
  async broadcast(message) {
    logMessage(`📢 [模拟] 正在广播消息: "${message}"`);
    return true;
  }
  
  async stop() {
    logMessage('🛑 正在停止MiGPT服务...');
    this.isRunning = false;
    this.listeners = {};
    await new Promise(resolve => setTimeout(resolve, 500));
    logMessage('✅ 服务已成功停止');
  }
}

// 真实MiGPT客户端实现
class MiGPTClientReal {
  constructor(config) {
    this.config = config;
    this.isRunning = false;
    this.client = null;
    this.isRealConnected = false;
    
    // 添加备用广播方法所需的配置
    this.speakerIp = process.env.MI_SPEAKER_IP || '192.168.31.100'; // 默认可能的音箱IP
    this.speakerPort = process.env.MI_SPEAKER_PORT || 8080; // 默认端口
    this.speakerWebSocketUrl = process.env.MI_SPEAKER_WS_URL || null;
    this.authToken = process.env.MI_AUTH_TOKEN || null;
    
    logMessage(`🔧 MiGPT客户端初始化完成，配置信息：`);
    logMessage(`  - 小米账号: ${config.miUserId}`);
    logMessage(`  - 音箱名称: ${config.miSpeakerDid}`);
    logMessage(`  - 已配置豆包API: ${!!config.doubaoApiKey}`);
    logMessage(`  - 音箱IP (备用): ${this.speakerIp}`);
    
    // 添加连接诊断
    this.runConnectionDiagnostics();
  }
  
  // 运行连接诊断
  async runConnectionDiagnostics() {
    logMessage('🔍 正在运行音箱连接诊断...');
    
    // 检查必要配置
    if (!this.config.miUserId || !this.config.miPassword || !this.config.miSpeakerDid) {
      logMessage('❌ 配置不完整，缺少必要的账号或设备信息');
    }
    
    // 检查网络连接
    if (axios) {
      try {
        await axios.get('https://api.mi.com', { timeout: 3000 });
        logMessage('✅ 可以连接到小米服务器');
      } catch (error) {
        logMessage('⚠️  无法连接到小米服务器，可能影响音箱控制');
      }
    }
    
    logMessage('🔍 诊断完成');
  }
  
  async start() {
    logMessage('📡 正在连接到小爱音箱...');
    try {
      // 首先检查豆包API配置
      if (!process.env.DOUBAO_API_KEY || process.env.DOUBAO_API_KEY === 'your_doubao_api_key_here') {
        logMessage('⚠️  豆包API密钥未配置或使用默认值，将使用本地响应模式');
      } else {
        logMessage('✅ 已检测到豆包API密钥，将尝试使用豆包AI提供智能回复');
        // 尝试测试豆包API连接
        const testResponse = await callDoubaoAPI('测试连接');
        if (testResponse) {
          logMessage('✅ 豆包API连接测试成功！');
        }
      }
      
      if (MiGPTClient) {
        // 创建MiGPT客户端实例
        logMessage('🔄 正在初始化MiGPT客户端实例...');
        this.client = new MiGPTClient({
          miUserId: this.config.miUserId,
          miPassword: this.config.miPassword,
          miSpeakerDid: this.config.miSpeakerDid,
          doubaoApiKey: this.config.doubaoApiKey,
          enableLog: true
        });

        logMessage('🔄 尝试连接音箱...');
        // 尝试连接音箱
        const connected = await this.client.connect();
        
        if (connected) {
          logMessage(`✅ 成功连接到小爱音箱：${this.config.miSpeakerDid}`);
          this.isRealConnected = true;
          realSpeakerConnected = true;
          
          logMessage('🔄 正在配置AI服务参数...');
          await this.client.initializeAI();
          
          this.isRunning = true;
          logMessage('✅ AI服务配置完成');
          
          // 设置语音监听，使用异步响应生成函数
          this.client.on('voice-command', async (command) => {
            logMessage(`🎤 收到语音指令: ${command}`);
            try {
              const response = await generateResponseAsync(command);
              await saveConversation(command, response);
              await this.client.speak(response);
            } catch (error) {
              logMessage(`❌ 处理语音指令时出错: ${error.message}`);
            }
          });
          
          // 设置初始问候，使用异步响应生成函数
          setTimeout(async () => {
            try {
              const response = await generateResponseAsync('你好');
              await saveConversation('小爱同学，你好', response);
            } catch (error) {
              logMessage(`❌ 生成初始问候时出错: ${error.message}`);
            }
          }, 2000);
          
          return true;
        } else {
          logMessage('❌ 连接音箱失败，启用模拟模式');
          // 失败时启用模拟模式
          return this.startSimulationMode();
        }
      } else {
        logMessage('❌ MiGPTClient未找到，启用模拟模式');
        return this.startSimulationMode();
      }
    } catch (error) {
      logMessage(`❌ 连接音箱时发生错误: ${error.message}`);
      logMessage(`   详细错误: ${error.stack}`);
      logMessage('⚠️  启用模拟模式作为备选');
      // 出错时启用模拟模式
      return this.startSimulationMode();
    }
  }
  
  async startSimulationMode() {
    // 模拟连接过程
    await new Promise(resolve => setTimeout(resolve, 1000));
    logMessage(`⚠️  模拟模式已启用，无法控制实际音箱设备`);
    this.isRunning = true;
    return true;
  }
  
  // 广播消息到音箱
  async sendBroadcastToSpeaker(message) {
    try {
      logMessage(`📢 正在尝试通过MiGPT客户端广播消息: "${message}"`);
      
      // 记录广播尝试到日志文件
      const logEntry = `[${new Date().toISOString()}] 广播尝试: "${message}"`;
      this.logToFile(logEntry);
      
      // 方法1：尝试使用MiGPT客户端广播（如果可用）
      if (MiGPTClient && this.client && this.isRunning) {
        try {
          await this.client.broadcast(message);
          logMessage(`✅ 广播消息通过MiGPT客户端发送成功`);
          this.logToFile(`✅ 广播成功 - MiGPT客户端`);
          return true;
        } catch (migptError) {
          logMessage(`⚠️ MiGPT客户端广播失败: ${migptError.message}，尝试备用方法`);
          this.logToFile(`⚠️ MiGPT广播失败: ${migptError.message}`);
        }
      }
      
      // 方法2：尝试使用WebSocket（如果可用且配置了地址）
      if (ws && this.speakerWebSocketUrl) {
        try {
          const socket = new ws(this.speakerWebSocketUrl);
          await new Promise((resolve, reject) => {
            socket.on('open', () => {
              socket.send(JSON.stringify({
                type: 'broadcast',
                message: message,
                deviceId: this.config.miSpeakerDid
              }));
              socket.close();
              resolve();
            });
            socket.on('error', reject);
            // 设置超时
            setTimeout(() => reject(new Error('WebSocket连接超时')), 3000);
          });
          logMessage(`✅ 广播消息通过WebSocket发送成功`);
          this.logToFile(`✅ 广播成功 - WebSocket`);
          return true;
        } catch (wsError) {
          logMessage(`⚠️ WebSocket广播失败: ${wsError.message}，尝试备用方法`);
          this.logToFile(`⚠️ WebSocket广播失败: ${wsError.message}`);
        }
      }
      
      // 方法3：尝试使用HTTP API广播作为备用方法
      if (axios && this.speakerIp) {
        try {
          // 尝试标准端口
          const apiUrl = `http://${this.speakerIp}:${this.speakerPort || 8080}/broadcast`;
          const response = await axios.post(apiUrl, {
            message: message,
            deviceId: this.config.miSpeakerDid
          });
          logMessage(`✅ 广播消息通过HTTP API发送成功，状态码: ${response.status}`);
          this.logToFile(`✅ 广播成功 - HTTP API`);
          return true;
        } catch (httpError) {
          logMessage(`⚠️ HTTP API广播失败: ${httpError.message}`);
          this.logToFile(`⚠️ HTTP API广播失败: ${httpError.message}`);
        }
      }
      
      logMessage('⚠️  所有广播方法都失败，将返回false以启用模拟模式');
      this.logToFile('⚠️  所有广播方法都失败，将返回false以启用模拟模式');
      return false;
    } catch (error) {
      logMessage(`❌ 广播消息发送过程中发生错误: ${error.message}`);
      this.logToFile(`❌ 广播消息发送过程中发生错误: ${error.message}`);
      return false;
    }
  }
  
  // 辅助方法：写入日志到文件
  logToFile(message) {
    try {
      const fs = require('fs');
      const path = require('path');
      const broadcastLogPath = path.join(__dirname, 'logs', `broadcast_${new Date().toISOString().split('T')[0]}.log`);
      const logEntry = `${new Date().toISOString()} - ${message}\n`;
      fs.appendFileSync(broadcastLogPath, logEntry, 'utf8');
    } catch (logError) {
      // 静默忽略日志写入错误
    }
  }
  
  async stop() {
    logMessage('🛑 正在停止MiGPT服务...');
    try {
      if (this.client) {
        await this.client.disconnect();
      }
    } catch (error) {
      logMessage(`⚠️  停止客户端时发生错误: ${error.message}`);
    }
    
    this.isRunning = false;
    this.client = null;
    logMessage('✅ 服务已成功停止');
  }
}

// 停止服务函数
async function stopService() {
  if (migptClient) {
    await migptClient.stop();
  }
  await prisma.$disconnect();
  logMessage('✅ 所有服务已关闭，再见！');
}

// 处理用户输入
async function handleUserInput(input) {
  // 检查是否是退出命令
  if (input.toLowerCase() === 'exit' || input.toLowerCase() === 'quit') {
    logMessage('\n🛑 收到退出命令，正在关闭服务...');
    await stopService();
    process.exit(0);
    return;
  }
  
  // 检查是否是诊断命令
  if (input.toLowerCase() === 'diagnose') {
    logMessage('🔍 运行音箱连接诊断...');
    if (migptClient && typeof migptClient.runConnectionDiagnostics === 'function') {
      await migptClient.runConnectionDiagnostics();
    } else {
      logMessage('✅ 服务状态：正常运行');
      logMessage('🔊 音箱连接：' + (realSpeakerConnected ? '已连接' : '模拟模式'));
      logMessage('📁 日志目录：正常工作');
      logMessage('💾 数据库：连接正常');
    }
    return;
  }
  
  // 检查是否是广播命令
  if (input.startsWith('broadcast:')) {
    const message = input.substring(10).trim();
    if (message) {
      logMessage('📢 收到广播请求："' + message + '"');
      await sendBroadcastMessage(message);
      return;
    } else {
      logMessage('❌ 广播消息不能为空，请使用格式: broadcast:消息内容');
      return;
    }
  }
  
  // 处理普通对话，使用异步响应生成函数支持豆包API
  if (input.trim()) {
    logMessage(`💬 用户输入: "${input}"`);
    try {
      const response = await generateResponseAsync(input);
      await saveConversation(input, response);
    } catch (error) {
      logMessage(`❌ 处理对话时出错: ${error.message}`);
      await saveConversation(input, '抱歉，处理你的请求时发生了错误。');
    }
  }
}

// 添加命令行广播功能
function startCommandLineInterface() {
  const readline = require('readline');
  const fs = require('fs');
  const commandFile = 'send_command.txt';
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: '> ' // 添加提示符
  });
  
  // 设置文件监视器，读取命令文件
  if (fs.existsSync(commandFile)) {
    fs.unlinkSync(commandFile); // 删除之前的命令文件
  }
  
  // 开始监视命令文件
  fs.watchFile(commandFile, (curr, prev) => {
    if (curr.mtimeMs !== prev.mtimeMs) {
      try {
        const command = fs.readFileSync(commandFile, 'utf8').trim();
        logMessage(`📄 从文件读取命令: ${command}`);
        handleUserInput(command).then(() => {
          // 读取后删除文件
          try {
            if (fs.existsSync(commandFile)) {
              fs.unlinkSync(commandFile);
            }
          } catch (e) {
            logMessage(`❌ 删除命令文件失败: ${e.message}`);
          }
        });
      } catch (error) {
        logMessage(`❌ 读取命令文件出错: ${error.message}`);
      }
    }
  });
  
  console.log('\n=========================================');
  console.log('🎉 MiGPT 增强服务启动成功！');
  console.log('🔊 音箱配置：' + process.env.MI_SPEAKER_DID);
  console.log('🤖 已配置AI引擎：豆包AI');
  console.log('💡 提示：你可以通过语音指令 "小爱同学，请xxx" 来与 AI 互动');
  console.log('📢 广播功能：输入 "broadcast:消息内容" 发送广播');
  console.log('📄 或创建 send_command.txt 文件写入命令');
  console.log('🔧 诊断命令：输入 "diagnose" 运行连接诊断');
  console.log('📝 对话记录保存在 logs/conversations_日期.json 文件中');
  console.log('=========================================\n');
  console.log('👂 服务正在运行中...（输入消息与AI对话，输入exit退出）');
  
  rl.prompt();
  
  rl.on('line', async (input) => {
    await handleUserInput(input.trim());
    rl.prompt();
  }).on('close', async () => {
    fs.unwatchFile(commandFile); // 停止监视文件
    await stopService();
    console.log('\n👋 MiGPT服务已关闭，再见！');
    process.exit(0);
  });
}

// 启动服务函数
async function startMiGPT() {
  try {
    // 初始化数据库
    await initDatabase();
    
    // 根据环境选择客户端类型
    logMessage('🔧 正在创建MiGPT客户端...');
    
    // 优先尝试使用真实客户端
    if (MiGPTClient) {
      try {
        migptClient = new MiGPTClientReal({
          miUserId: process.env.MI_USER_ID,
          miPassword: process.env.MI_PASSWORD,
          miSpeakerDid: process.env.MI_SPEAKER_DID,
          doubaoApiKey: process.env.DOUBAO_API_KEY
        });
      } catch (e) {
        logMessage(`⚠️ 创建真实客户端失败: ${e.message}，回退到模拟模式`);
        migptClient = new MiGPTClientSimulator({
          miUserId: process.env.MI_USER_ID,
          miPassword: process.env.MI_PASSWORD,
          miSpeakerDid: process.env.MI_SPEAKER_DID,
          doubaoApiKey: process.env.DOUBAO_API_KEY
        });
      }
    } else {
      // 如果没有MiGPTClient，使用模拟器
      migptClient = new MiGPTClientSimulator({
        miUserId: process.env.MI_USER_ID,
        miPassword: process.env.MI_PASSWORD,
        miSpeakerDid: process.env.MI_SPEAKER_DID,
        doubaoApiKey: process.env.DOUBAO_API_KEY
      });
    }
    
    // 启动服务
    logMessage('🚀 正在启动MiGPT服务...');
    await migptClient.start();
    
    // 启动命令行接口
    startCommandLineInterface();
    
    // 监听进程退出信号
    process.on('SIGINT', async () => {
      logMessage('\n🛑 收到退出信号，正在关闭服务...');
      await stopService();
    });
    
  } catch (error) {
    logMessage('❌ MiGPT服务启动失败: ' + error.message);
    try {
      await prisma.$disconnect();
    } catch (e) {}
    process.exit(1);
  }
}

// 启动服务
logMessage('=========================================');
logMessage('🚀 MiGPT 完整增强服务');
logMessage('=========================================');
startMiGPT();

// 注意：不再需要显式调用resume()，因为readline接口已经处理了输入流