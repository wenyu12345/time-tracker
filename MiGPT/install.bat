@echo off

rem MiGPT Node.js 依赖安装脚本

echo ===================================
echo    MiGPT Node.js 依赖安装脚本
 echo ===================================

echo 检查 Node.js 环境...
node -v >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误：未找到 Node.js！
    echo 请先安装 Node.js 14 或更高版本
    pause
    exit /b 1
)

echo 检查 npm 环境...
npm -v >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误：未找到 npm！
    echo npm 通常与 Node.js 一起安装，请检查 Node.js 安装
    pause
    exit /b 1
)

echo 开始安装依赖...
echo npm install
call npm install

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ 依赖安装成功！
    echo 📝 可以通过运行 start.bat 启动 MiGPT
) else (
    echo.
    echo ❌ 依赖安装失败！
    echo 💡 可能的解决方案：
    echo     1. 检查网络连接
    echo     2. 尝试使用管理员权限运行此脚本
    echo     3. 确保 package.json 文件存在且格式正确
)

echo.
pause