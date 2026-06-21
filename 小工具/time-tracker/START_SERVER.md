# 服务器启动指南

## 启动前检查
- 确保Python解释器路径：`D:\PYTHON\python.exe`
- 确保后端目录：`d:\新建文件夹\小工具\time-tracker\backend`
- 确保端口5000未被占用

## 启动步骤

### 1. 切换到后端目录
```powershell
cd "d:\新建文件夹\小工具\time-tracker\backend"
```

### 2. 启动服务器
```powershell
D:\PYTHON\python.exe app.py
```

### 3. 验证启动成功
看到以下日志表示启动成功：
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.132:5000
```

## 访问地址
- 本地访问：http://127.0.0.1:5000
- 局域网访问：http://192.168.1.132:5000

## 停止服务器
在运行终端按 `Ctrl + C`

## 注意事项
- Debug模式已开启，代码修改会自动重载
- 如果端口被占用，先停止其他Python进程
