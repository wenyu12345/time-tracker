@echo off

REM 简化版 MiGPT 启动脚本
SETLOCAL

REM 检查 Node.js 环境
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到 Node.js 环境，请先安装 Node.js
    echo 请从 https://nodejs.org 下载并安装
    pause
    exit /b 1
)

REM 检查必要文件
if not exist .env (
    echo 错误: 未找到 .env 配置文件
    echo 请确保 .env 文件已创建并包含正确的配置
    pause
    exit /b 1
)

if not exist .migpt.js (
    echo 错误: 未找到 .migpt.js 配置文件
    echo 请确保 .migpt.js 文件已创建并包含正确的配置
    pause
    exit /b 1
)

REM 创建日志目录
mkdir logs 2>nul

REM 直接运行服务
cls
echo 正在启动 MiGPT 服务...
echo 当前目录: %cd%
echo 服务日志将保存在 logs 目录下
echo. 

node index.js

ENDLOCAL
