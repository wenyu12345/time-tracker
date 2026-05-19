#!/bin/bash

# Excel上传分析系统 - 腾讯云一键部署脚本
# 功能：自动化部署Excel上传分析系统到腾讯云服务器

set -e  # 出错时退出

echo "=== Excel上传分析系统 - 腾讯云一键部署脚本 ==="
echo "本脚本将帮助您自动化部署系统到腾讯云服务器"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
SERVER_IP=""
SSH_PORT="22"
SERVER_USER="root"
PROJECT_DIR="/opt/excel_upload_system"
LOCAL_PROJECT_DIR=$(pwd)

# 检查是否在正确的项目目录中
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}错误：请在Excel上传分析系统的根目录下运行此脚本${NC}"
    exit 1
fi

# 获取服务器信息
read -p "请输入腾讯云服务器IP地址: " SERVER_IP
read -p "请输入SSH端口号 [22]: " SSH_PORT
SSH_PORT=${SSH_PORT:-22}
read -p "请输入服务器用户名 [root]: " SERVER_USER
SERVER_USER=${SERVER_USER:-root}

echo ""
echo -e "${GREEN}部署信息确认${NC}"
echo "服务器IP: $SERVER_IP"
echo "SSH端口: $SSH_PORT"
echo "服务器用户: $SERVER_USER"
echo "项目部署目录: $PROJECT_DIR"
echo ""

read -p "确认以上信息正确并继续部署？(y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo -e "${GREEN}开始部署...${NC}"

# 阶段一：服务器环境初始化
echo -e "${YELLOW}1. 服务器环境初始化${NC}"
echo "连接服务器并配置基础环境..."

# 创建初始化脚本
cat > /tmp/init_server.sh << 'EOF'
#!/bin/bash
set -e

echo "=== 服务器环境初始化 ==="

# 更新系统
echo "更新系统软件包..."
apt update && apt upgrade -y

# 安装必要软件
echo "安装必要软件包..."
apt install -y git wget curl unzip build-essential python3.9 python3.9-dev python3.9-venv python3-pip nginx supervisor

# 升级pip
echo "升级pip..."
pip3 install --upgrade pip

# 创建项目目录
echo "创建项目目录..."
mkdir -p /opt/excel_upload_system
chown -R $SERVER_USER:$SERVER_USER /opt/excel_upload_system

# 配置防火墙
echo "配置防火墙..."
ufw allow 22/tcp
echo "y" | ufw enable

echo "=== 服务器环境初始化完成 ==="
EOF

# 替换脚本中的变量
if [ -f "/tmp/init_server.sh" ]; then
    sed -i "s/\$SERVER_USER/$SERVER_USER/g" /tmp/init_server.sh
fi

# 上传并执行初始化脚本
scp -P $SSH_PORT /tmp/init_server.sh $SERVER_USER@$SERVER_IP:/tmp/
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "chmod +x /tmp/init_server.sh && sudo /tmp/init_server.sh"

# 阶段二：创建虚拟环境
echo ""
echo -e "${YELLOW}2. 创建Python虚拟环境${NC}"
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && python3.9 -m venv venv"

# 阶段三：上传项目代码
echo ""
echo -e "${YELLOW}3. 上传项目代码${NC}"
echo "正在上传项目文件..."

# 创建上传排除列表
cat > /tmp/exclude_list.txt << 'EOF'
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
*.log
data/uploads/
excel_upload_system.conf
gunicorn_config.py
nginx_config.conf
deploy_to_cloud.sh
start_production.sh
EOF

# 上传项目文件
scp -P $SSH_PORT -r -p -i /tmp/exclude_list.txt ./ $SERVER_USER@$SERVER_IP:$PROJECT_DIR/

# 阶段四：安装项目依赖
echo ""
echo -e "${YELLOW}4. 安装项目依赖${NC}"
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"

# 阶段五：配置服务
echo ""
echo -e "${YELLOW}5. 配置服务${NC}"

# 配置Gunicorn
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && mkdir -p logs data/uploads"

# 配置Supervisor
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo cp $PROJECT_DIR/excel_upload_system.conf /etc/supervisor/conf.d/"

# 配置Nginx
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo cp $PROJECT_DIR/nginx_config.conf /etc/nginx/sites-available/excel_upload_system"
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo ln -sf /etc/nginx/sites-available/excel_upload_system /etc/nginx/sites-enabled/"
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo rm -f /etc/nginx/sites-enabled/default"

# 阶段六：启动服务
echo ""
echo -e "${YELLOW}6. 启动服务${NC}"

# 重启Supervisor
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo systemctl restart supervisor"
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo supervisorctl reread && sudo supervisorctl update && sudo supervisorctl start excel_upload_system"

# 重启Nginx
ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo nginx -t && sudo systemctl restart nginx"

# 阶段七：验证部署
echo ""
echo -e "${YELLOW}7. 验证部署${NC}"
echo "检查服务状态..."

# 检查应用状态
app_status=$(ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo supervisorctl status excel_upload_system | grep RUNNING || echo 'NOT RUNNING'")

# 检查Nginx状态
nginx_status=$(ssh -p $SSH_PORT $SERVER_USER@$SERVER_IP "sudo systemctl is-active nginx || echo 'inactive'")

# 输出结果
echo ""
if [[ "$app_status" == *"RUNNING"* ]] && [[ "$nginx_status" == "active" ]]; then
    echo -e "${GREEN}恭喜！部署成功！${NC}"
    echo -e "${GREEN}您可以通过 http://$SERVER_IP 访问系统${NC}"
else
    echo -e "${RED}部署遇到问题！${NC}"
    echo "应用状态: $app_status"
    echo "Nginx状态: $nginx_status"
    echo "请检查日志文件以获取详细信息:"
    echo "- 应用日志: $PROJECT_DIR/logs/"
    echo "- Nginx日志: /var/log/nginx/"
fi

echo ""
echo -e "${YELLOW}部署脚本执行完成${NC}"
echo "详细部署文档请参考: $PROJECT_DIR/DEPLOY_TENCENT_CLOUD.md"

# 清理临时文件
rm -f /tmp/init_server.sh /tmp/exclude_list.txt