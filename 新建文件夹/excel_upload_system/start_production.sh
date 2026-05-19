#!/bin/bash

# Excel上传分析系统 - 生产环境启动脚本
# 用于腾讯云服务器部署

echo "=== Excel上传分析系统启动脚本 ==="

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "警告：未检测到虚拟环境"
    echo "请先激活虚拟环境：source venv/bin/activate"
    exit 1
fi

# 设置环境变量
export FLASK_ENV=production
export FLASK_APP=main.py

# 确保必要的目录存在
echo "创建必要的目录..."
mkdir -p data/uploads
mkdir -p logs

# 设置目录权限
echo "设置目录权限..."
chmod -R 755 data/uploads
chmod -R 755 logs

# 检查依赖是否已安装
echo "检查依赖..."
pip list | grep -E "flask|pandas|gunicorn" > /dev/null
if [ $? -ne 0 ]; then
    echo "警告：部分依赖未安装"
    echo "请先安装依赖：pip install -r requirements.txt"
    exit 1
fi

# 启动应用
echo "启动应用服务器..."
echo "服务器配置："
echo "- 绑定地址：127.0.0.1:5001"
echo "- 工作进程：自动检测CPU核心数"
echo "- 日志位置：logs/"
echo ""
echo "按 Ctrl+C 停止服务"
echo "===================================="

# 使用Gunicorn启动应用
gunicorn \
    --bind 127.0.0.1:5001 \
    --workers $(($(nproc) * 2 + 1)) \
    --threads 2 \
    --timeout 300 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    main:app