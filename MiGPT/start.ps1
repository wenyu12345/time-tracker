# 设置环境变量
$env:MI_USER_ID = "1487810896"
$env:MI_PASSWORD = "lj199006"
$env:MI_SPEAKER_DID = "小爱音箱Play"

# 显示启动信息
Write-Host "========================================="
Write-Host "        MiGPT 启动脚本"
Write-Host "========================================="
Write-Host "环境变量已设置："
Write-Host "- MI_USER_ID: $env:MI_USER_ID"
Write-Host "- MI_SPEAKER_DID: $env:MI_SPEAKER_DID"
Write-Host ""
Write-Host "正在启动 MiGPT 服务..."

# 启动服务
node index.js
