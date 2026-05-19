@echo off

REM 简单版 MiGPT 启动脚本
SETLOCAL

REM 显示启动信息
cls
echo =========================================
echo           MiGPT 简易启动器
 echo =========================================
echo 当前目录: %cd%
echo 正在启动 MiGPT 服务...
echo 配置文件: .env 和 .migpt.js

echo.
echo 正在加载环境变量...

REM 手动设置必要的环境变量
SET MI_USER_ID=1487810896
SET MI_PASSWORD=lj199006
SET MI_SPEAKER_DID=小爱音箱Play

REM 检查文件是否存在
if not exist .env (
    echo ⚠️  .env 文件不存在，但已设置环境变量
)

if not exist .migpt.js (
    echo ❌  错误: .migpt.js 文件不存在
    pause
    exit /b 1
)

REM 创建日志目录
mkdir logs 2>nul

REM 启动服务
echo.
echo 🚀 正在启动 MiGPT 服务...
echo 📝 日志输出:
echo ----------------------------------------

REM 直接用node启动服务
node index.js

REM 检查退出码
if %errorlevel% neq 0 (
    echo ----------------------------------------
    echo ❌ 服务启动失败，请检查错误信息
    pause
    exit /b %errorlevel%
)

ENDLOCAL
