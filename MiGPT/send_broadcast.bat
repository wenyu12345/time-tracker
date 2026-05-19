@echo off
cls

:menu
echo =========================================
echo 🔊 MiGPT 广播发送工具
echo =========================================
echo 请输入要发送的广播消息内容，或输入以下命令：
echo 1 - 测试消息1
echo 2 - 测试消息2
echo diagnose - 运行连接诊断
echo exit - 退出工具
echo =========================================
set /p message="请输入: "

if "%message%"=="exit" goto end
if "%message%"=="1" set message=你好，这是测试广播消息1
if "%message%"=="2" set message=测试广播消息2，音箱是否能接收到？
if "%message%"=="diagnose" (
    echo 正在发送诊断命令...
    echo diagnose > send_command.txt
    echo =========================================
    echo ✅ 诊断命令已发送
    echo =========================================
    pause
    goto menu
)

echo broadcast:%message% > send_command.txt
echo =========================================
echo 📢 发送内容：%message%
echo ✅ 广播消息已写入 send_command.txt
echo 系统将自动删除该文件

echo =========================================
pause
goto menu

:end
echo 👋 工具已退出
echo 按任意键继续...
pause >nul