@echo off
echo ========================================
echo 天命1.0版本 - GitHub备份指南
echo ========================================
echo.
echo 第一步：在GitHub上创建新仓库
echo 1. 访问 https://github.com/new
echo 2. 仓库名称: time-tracker
echo 3. 选择"Public"或"Private"
echo 4. 点击"Create repository"
echo.
echo 第二步：运行下面的命令（在命令行中执行）
echo.
cd /d "d:\新建文件夹\小工具\time-tracker"
echo.
echo 添加远程仓库:
echo git remote add origin https://github.com/你的用户名/time-tracker.git
echo.
echo 推送代码:
echo git push -u origin master
echo.
echo ========================================
echo 如果需要创建.gitignore文件，可以运行：
echo.
echo echo # 数据库文件 ^>^> .gitignore
echo echo *.db ^>^> .gitignore
echo echo __pycache__/ ^>^> .gitignore
echo echo *.pyc ^>^> .gitignore
echo echo .trae/ ^>^> .gitignore
echo.
echo ========================================
pause
