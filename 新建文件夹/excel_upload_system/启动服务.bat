@echo off

REM Excel上传分析系统 - Windows启动脚本

echo ============= Excel上传分析系统 =============
echo 正在启动服务...

REM 检查Python环境
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误：未找到Python。请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查是否安装了依赖
pip list | findstr "Flask pandas" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 警告：未检测到必要的依赖包
    echo 正在安装依赖...
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo 错误：依赖安装失败
        pause
        exit /b 1
    )
)

REM 创建必要的目录
mkdir data\uploads 2>nul
mkdir logs 2>nul

echo 服务配置：
echo - 绑定地址：127.0.0.1:5002
echo - 模式：开发模式

echo.
echo 服务正在启动...
echo 访问地址：http://127.0.0.1:5002
echo 手机访问地址：http://192.168.1.132:5002
echo 按 Ctrl+C 停止服务
echo ============================================
echo.

REM 启动Flask应用
set FLASK_APP=main.py
set FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5002
