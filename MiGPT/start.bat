@echo off

rem MiGPT Node.js 启动脚本

echo ===================================
echo        MiGPT Node.js 启动脚本
 echo ===================================

rem 检查配置文件是否存在
if not exist .env (
    echo 错误：.env 配置文件不存在！
    echo 请复制 .env.example 为 .env 并填写正确的配置信息
    pause
    exit /b 1
)

if not exist .migpt.js (
    echo 错误：.migpt.js 配置文件不存在！
    pause
    exit /b 1
)

rem 检查是否已安装依赖
if not exist node_modules (
    echo 错误：未检测到依赖！
    echo 请先运行 install.bat 安装依赖
    pause
    exit /b 1
)

rem 创建日志目录
mkdir logs 2>nul

echo 正在启动 MiGPT...
echo 启动命令：npm start
call npm start

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ MiGPT 启动失败！
    echo 💡 请检查配置文件是否正确
    echo 💡 查看 logs 目录下的日志获取更多信息
)

echo.
pause