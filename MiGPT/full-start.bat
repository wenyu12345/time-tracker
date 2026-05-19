@echo off
chcp 65001 >nul

cls
echo =========================================
echo 🚀 MiGPT 完整服务启动工具
echo =========================================
echo 

REM 检查npm命令是否存在
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误：未找到npm命令，请先安装Node.js
    echo 💡 访问 https://nodejs.org/ 下载并安装Node.js
    pause
    exit /b 1
)

echo 🔍 检查依赖包...
npm install --silent
if %errorlevel% neq 0 (
    echo ❌ 错误：依赖包安装失败
    echo 💡 请检查网络连接或npm配置
    pause
    exit /b 1
)

echo 📦 初始化数据库...
npm run init-db
if %errorlevel% neq 0 (
    echo ❌ 错误：数据库初始化失败
    echo 💡 请查看错误信息并解决问题后重试
    pause
    exit /b 1
)

echo 🚀 启动MiGPT完整服务...
echo =========================================
echo 💡 服务正在启动，请稍候...
echo 🔊 服务启动后，可以通过小爱音箱语音控制
echo 📝 日志将显示在下方，按Ctrl+C停止服务
echo =========================================
echo 

npm start

REM 捕获退出代码
set exit_code=%errorlevel%
if %exit_code% neq 0 (
    echo 
    echo ❌ 服务异常退出，错误代码：%exit_code%
    echo 💡 请查看上方错误信息并解决问题
    pause
    exit /b %exit_code%
)

echo 
echo 🛑 服务已正常停止
pause
