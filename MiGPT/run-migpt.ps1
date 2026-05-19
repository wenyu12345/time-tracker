# MiGPT PowerShell 启动脚本

# 检查 Node.js 环境
$nodePath = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodePath) {
    Write-Host "错误: 未找到 Node.js 环境，请先安装 Node.js"
    Write-Host "请从 https://nodejs.org 下载并安装"
    Read-Host "按 Enter 键退出"
    exit 1
}

# 检查必要文件
if (-not (Test-Path ".env")) {
    Write-Host "错误: 未找到 .env 配置文件"
    Write-Host "请确保 .env 文件已创建并包含正确的配置"
    Read-Host "按 Enter 键退出"
    exit 1
}

if (-not (Test-Path ".migpt.js")) {
    Write-Host "错误: 未找到 .migpt.js 配置文件"
    Write-Host "请确保 .migpt.js 文件已创建并包含正确的配置"
    Read-Host "按 Enter 键退出"
    exit 1
}

# 创建日志目录
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# 直接运行服务
Clear-Host
Write-Host "正在启动 MiGPT 服务..."
Write-Host "当前目录: $(Get-Location)"
Write-Host "服务日志将保存在 logs 目录下"
Write-Host ""

# 执行 Node.js 应用
node index.js
