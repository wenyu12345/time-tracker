// MiGPT 音箱测试启动器
const readline = require('readline');
const { execSync, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('=========================================');
console.log('🔊 MiGPT 音箱测试助手');
console.log('=========================================');
console.log('此助手将帮助您测试小爱音箱是否能收到广播消息');
console.log('=========================================\n');

// 检查MiGPT服务是否在运行
function checkMiGPTService() {
  try {
    console.log('🔍 检查MiGPT服务状态...');
    
    // 创建命令行接口
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    // 显示菜单
    function showMenu() {
      console.log('\n=========================================');
      console.log('请选择操作：');
      console.log('1. 发送测试广播消息');
      console.log('2. 运行连接诊断');
      console.log('3. 查看广播日志');
      console.log('4. 退出');
      console.log('=========================================');
      
      rl.question('请输入选择 (1-4): ', (answer) => {
        handleMenuSelection(answer, rl);
      });
    }
    
    // 处理菜单选择
    function handleMenuSelection(choice, rl) {
      switch(choice.trim()) {
        case '1':
          sendTestBroadcast(rl);
          break;
        case '2':
          runDiagnostics(rl);
          break;
        case '3':
          viewBroadcastLogs(rl);
          break;
        case '4':
          console.log('\n👋 感谢使用MiGPT音箱测试助手');
          rl.close();
          break;
        default:
          console.log('\n❌ 无效选择，请重新输入');
          showMenu();
      }
    }
    
    // 发送测试广播消息
    function sendTestBroadcast(rl) {
      rl.question('\n请输入要发送的广播消息内容: ', (message) => {
        if (!message.trim()) {
          message = '你好，这是一条测试广播消息';
        }
        
        try {
          const commandFilePath = path.join(__dirname, 'MiGPT', 'send_command.txt');
          fs.writeFileSync(commandFilePath, `broadcast:${message}`, 'utf8');
          console.log('\n✅ 广播消息已发送！');
          console.log(`📢 消息内容: ${message}`);
          console.log('\n💡 提示: 请检查您的小爱音箱是否播放了此消息');
          console.log('如果音箱没有收到，请尝试运行连接诊断');
          
          setTimeout(() => {
            showMenu();
          }, 2000);
        } catch (error) {
          console.log(`\n❌ 发送广播消息失败: ${error.message}`);
          showMenu();
        }
      });
    }
    
    // 运行连接诊断
    function runDiagnostics(rl) {
      try {
        const commandFilePath = path.join(__dirname, 'MiGPT', 'send_command.txt');
        fs.writeFileSync(commandFilePath, 'diagnose', 'utf8');
        console.log('\n🔍 诊断命令已发送！');
        console.log('请查看MiGPT服务终端的诊断结果');
        
        setTimeout(() => {
          showMenu();
        }, 2000);
      } catch (error) {
        console.log(`\n❌ 运行诊断失败: ${error.message}`);
        showMenu();
      }
    }
    
    // 查看广播日志
    function viewBroadcastLogs(rl) {
      try {
        const today = new Date().toISOString().split('T')[0];
        const logFilePath = path.join(__dirname, 'MiGPT', 'logs', `broadcast_${today}.log`);
        
        if (fs.existsSync(logFilePath)) {
          console.log('\n=========================================');
          console.log(`📋 广播日志 (${today}):`);
          console.log('=========================================');
          
          const logs = fs.readFileSync(logFilePath, 'utf8');
          console.log(logs || '暂无广播记录');
          
          rl.question('\n按回车键返回菜单...', () => {
            showMenu();
          });
        } else {
          console.log('\n❌ 今日广播日志文件不存在');
          setTimeout(() => {
            showMenu();
          }, 1000);
        }
      } catch (error) {
        console.log(`\n❌ 查看日志失败: ${error.message}`);
        showMenu();
      }
    }
    
    // 开始菜单
    showMenu();
    
    // 退出事件
    rl.on('close', () => {
      process.exit(0);
    });
    
  } catch (error) {
    console.log(`❌ 初始化出错: ${error.message}`);
  }
}

// 开始运行
checkMiGPTService();