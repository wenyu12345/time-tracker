// MiGPT 数据库初始化脚本
const { execSync } = require('child_process');
const path = require('path');

console.log('=========================================');
console.log('🔄 MiGPT 数据库初始化工具');
console.log('=========================================');

try {
  // 生成 Prisma 客户端
  console.log('📦 正在生成 Prisma 客户端...');
  execSync('npx prisma generate', { stdio: 'inherit', cwd: __dirname });
  console.log('✅ Prisma 客户端生成成功');
  
  // 运行数据库迁移
  console.log('🔄 正在执行数据库迁移...');
  execSync('npx prisma migrate dev --name init', { stdio: 'inherit', cwd: __dirname });
  console.log('✅ 数据库迁移成功完成');
  
  console.log('=========================================');
  console.log('🎉 数据库初始化完成！');
  console.log('🔧 现在可以运行 npm start 启动 MiGPT 服务');
  console.log('=========================================');
} catch (error) {
  console.error('❌ 数据库初始化失败:', error.message);
  console.log('💡 建议检查以下几点:');
  console.log('1. Node.js 环境是否正确安装');
  console.log('2. 是否已经执行过 npm install 安装依赖');
  console.log('3. 数据库文件是否有写入权限');
  console.log('4. Prisma 版本是否兼容');
  process.exit(1);
}