// MiGPT 广播测试脚本
const readline = require('readline');
const { exec } = require('child_process');

console.log('=========================================');
console.log('🔍 MiGPT 广播功能测试工具');
console.log('=========================================');
console.log('此工具将直接在MiGPT服务终端中输入命令');
console.log('输入要发送的广播消息，或输入 "diagnose" 运行诊断');
console.log('输入 "exit" 退出测试工具');
console.log('=========================================\n');

// 创建命令行接口
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: '> '
});

// 发送命令到MiGPT服务
function sendCommandToMiGPT(command) {
  console.log(`\n📢 正在发送命令: "${command}"`);
  
  // 使用Windows的SendKeys命令（注意：这只在Windows系统上有效）
  // 假设MiGPT服务在node终端中运行
  const windowsCommand = `powershell -Command "` +
    `$wshell = New-Object -ComObject wscript.shell; ` +
    `Start-Sleep -Milliseconds 500; ` +
    `$wshell.AppActivate('node'); ` +
    `Start-Sleep -Milliseconds 500; ` +
    `$wshell.SendKeys('${command.replace(/'/g, "''")}~'); ` +
    `Start-Sleep -Milliseconds 500; ` +
    `$wshell.AppActivate('${process.title.replace(/'/g, "''")}');` +
    `"`;
  
  // 执行命令
  exec(windowsCommand, (error, stdout, stderr) => {
    if (error) {
      console.log('❌ 发送命令失败:');
      console.log(`  ${error.message}`);
      // 提供替代方案
      console.log('\n💡 替代方法: 请直接在MiGPT服务终端中输入:');
      console.log(`  ${command}`);
    } else {
      console.log('✅ 命令已发送到MiGPT服务终端');
    }
  });
}

// 处理用户输入
rl.prompt();
rl.on('line', (input) => {
  const command = input.trim();
  
  if (command.toLowerCase() === 'exit' || command.toLowerCase() === 'quit') {
    console.log('\n👋 测试工具已退出');
    rl.close();
    return;
  }
  
  if (command.toLowerCase() === 'diagnose') {
    sendCommandToMiGPT('diagnose');
  } else if (command) {
    // 发送广播消息
    sendCommandToMiGPT(`broadcast:${command}`);
  }
  
  rl.prompt();
}).on('close', () => {
  console.log('\n👋 测试工具已退出');
  process.exit(0);
});