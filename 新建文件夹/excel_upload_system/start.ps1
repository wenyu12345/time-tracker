$ErrorActionPreference = "Continue"
Write-Host "启动服务器中..."
Write-Host "尝试多种方式..."

# 尝试多种 Python 命令
$pythonCmds = @("python", "py", "python3", "py3")
$foundCmd = $null
foreach ($cmd in $pythonCmds) {
    try {
        Write-Host "正在尝试: $cmd
        &amp; $cmd --version 2&gt;&amp;1 | Out-Null
        $foundCmd = $cmd
        Write-Host "找到Python: $foundCmd
        break
    } catch {
        Write-Host "$cmd 未找到，继续尝试...
    }
}

if ($foundCmd) {
    Write-Host "使用 $foundCmd 启动服务器"
    &amp; $foundCmd start_server.py
} else {
    Write-Host "未找到Python命令，尝试查找Python..."
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python*\pythonw.exe",
        "C:\Python*\python.exe"
    )
    $foundPython = $null
    foreach ($path in $possiblePaths) {
        $matches = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($matches) {
            $foundPython = $matches.FullName
            break
        }
    }
    if ($foundPython) {
        Write-Host "找到Python: $foundPython"
        &amp; $foundPython start_server.py
    } else {
        Write-Host "错误：未找到Python解释器！"
        Write-Host "请安装Python 3.7+，并添加到PATH环境变量。"
        Read-Host "按回车键退出"
    }
}
