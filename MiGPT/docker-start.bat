@echo off

rem MiGPT Docker 启动脚本

echo ===================================
echo       MiGPT Docker 启动脚本
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

rem 创建日志目录
mkdir logs 2>nul

echo 正在启动 MiGPT Docker 容器...
echo 请确保已安装 Docker 并启动 Docker 服务

echo 启动命令：docker-compose up -d
call docker-compose up -d

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ MiGPT Docker 容器启动成功！
    echo 📝 查看日志：docker-compose logs -f
    echo ⚠️  注意：首次启动可能需要下载镜像，请耐心等待
) else (
    echo.
    echo ❌ MiGPT Docker 容器启动失败！
    echo 💡 请检查 Docker 是否正确安装和启动
    echo 💡 也可以尝试直接使用以下命令：
    echo     docker run -d --env-file %cd%\.env -v %cd%\.migpt.js:/app/.migpt.js -v %cd%\logs:/app/logs --name mi-gpt idootop/mi-gpt:latest
)

echo.
pause