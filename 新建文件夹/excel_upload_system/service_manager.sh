#!/bin/bash

# Excel上传分析系统 - 服务管理脚本
# 功能：监控、检查、重启服务，确保应用稳定运行

set -e

echo "=== Excel上传分析系统 - 服务管理脚本 ==="

echo "使用方法："
echo "  $0 status      - 查看服务状态"
echo "  $0 start       - 启动服务"
echo "  $0 stop        - 停止服务"
echo "  $0 restart     - 重启服务"
echo "  $0 logs        - 查看最新日志"
echo "  $0 monitor     - 监控服务状态（持续）"
echo "  $0 check       - 检查服务健康状态"
echo ""

# 配置变量
PROJECT_DIR="/opt/excel_upload_system"
APP_NAME="excel_upload_system"
LOG_DIR="$PROJECT_DIR/logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否在正确的环境中
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}警告：未检测到标准部署路径 $PROJECT_DIR${NC}"
    echo -e "${YELLOW}使用当前目录作为项目目录${NC}"
    PROJECT_DIR=$(pwd)
    LOG_DIR="$PROJECT_DIR/logs"
fi

# 检查命令参数
if [ $# -eq 0 ]; then
    echo -e "${RED}错误：请指定命令参数${NC}"
    exit 1
fi

# 服务状态检查函数
check_service_status() {
    echo -e "${BLUE}检查服务状态...${NC}"
    
    # 检查Supervisor中的应用状态
    if command -v supervisorctl &> /dev/null; then
        echo -e "${BLUE}应用服务状态:${NC}"
        sudo supervisorctl status $APP_NAME
    else
        echo -e "${YELLOW}Supervisor未安装或未运行${NC}"
    fi
    
    # 检查Gunicorn进程
    echo -e "${BLUE}Gunicorn进程状态:${NC}"
    pgrep -f gunicorn | wc -l
    if pgrep -f gunicorn > /dev/null; then
        echo -e "${GREEN}✓ Gunicorn进程正在运行${NC}"
    else
        echo -e "${RED}✗ Gunicorn进程未运行${NC}"
    fi
    
    # 检查Nginx状态
    echo -e "${BLUE}Nginx服务状态:${NC}"
    if command -v systemctl &> /dev/null; then
        sudo systemctl is-active nginx
    else
        echo -e "${YELLOW}无法检查Nginx状态${NC}"
    fi
    
    # 检查监听端口
    echo -e "${BLUE}监听端口状态:${NC}"
    if command -v netstat &> /dev/null; then
        sudo netstat -tulpn | grep -E '5000|80|443'
    elif command -v ss &> /dev/null; then
        sudo ss -tulpn | grep -E '5000|80|443'
    else
        echo -e "${YELLOW}无法检查端口状态${NC}"
    fi
}

# 启动服务函数
start_service() {
    echo -e "${BLUE}启动服务...${NC}"
    
    # 确保必要目录存在
    echo -e "${BLUE}创建必要目录...${NC}"
    mkdir -p "$LOG_DIR"
    mkdir -p "$PROJECT_DIR/data/uploads"
    
    # 启动Supervisor服务
    if command -v systemctl &> /dev/null; then
        echo -e "${BLUE}启动Supervisor...${NC}"
        sudo systemctl start supervisor || true
    fi
    
    # 启动应用
    echo -e "${BLUE}启动应用服务...${NC}"
    if command -v supervisorctl &> /dev/null; then
        sudo supervisorctl reread
        sudo supervisorctl update
        sudo supervisorctl start $APP_NAME
    else
        echo -e "${YELLOW}Supervisor未安装，尝试直接启动Gunicorn...${NC}"
        cd "$PROJECT_DIR"
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        nohup gunicorn -c gunicorn_config.py main:app > "$LOG_DIR/gunicorn_direct.log" 2>&1 &
    fi
    
    # 启动Nginx
    echo -e "${BLUE}启动Nginx...${NC}"
    if command -v systemctl &> /dev/null; then
        sudo systemctl start nginx || true
    fi
    
    echo -e "${GREEN}服务启动完成！${NC}"
    check_service_status
}

# 停止服务函数
stop_service() {
    echo -e "${BLUE}停止服务...${NC}"
    
    # 停止应用
    echo -e "${BLUE}停止应用服务...${NC}"
    if command -v supervisorctl &> /dev/null; then
        sudo supervisorctl stop $APP_NAME
    else
        echo -e "${BLUE}查找并停止Gunicorn进程...${NC}"
        pkill -f gunicorn || true
    fi
    
    # 停止Nginx（可选）
    # echo -e "${BLUE}停止Nginx...${NC}"
    # if command -v systemctl &> /dev/null; then
    #     sudo systemctl stop nginx || true
    # fi
    
    echo -e "${GREEN}服务停止完成！${NC}"
    check_service_status
}

# 重启服务函数
restart_service() {
    echo -e "${BLUE}重启服务...${NC}"
    
    # 停止服务
    stop_service
    
    # 等待几秒
    echo -e "${BLUE}等待5秒...${NC}"
    sleep 5
    
    # 启动服务
    start_service
    
    echo -e "${GREEN}服务重启完成！${NC}"
}

# 查看日志函数
view_logs() {
    echo -e "${BLUE}查看最新日志...${NC}"
    
    # 查看Gunicorn错误日志
    if [ -f "$LOG_DIR/gunicorn_error.log" ]; then
        echo -e "${YELLOW}=== Gunicorn错误日志 ===${NC}"
        tail -n 50 "$LOG_DIR/gunicorn_error.log"
        echo ""
    fi
    
    # 查看Gunicorn访问日志
    if [ -f "$LOG_DIR/gunicorn_access.log" ]; then
        echo -e "${YELLOW}=== Gunicorn访问日志 ===${NC}"
        tail -n 20 "$LOG_DIR/gunicorn_access.log"
        echo ""
    fi
    
    # 查看Supervisor日志
    if [ -f "$LOG_DIR/supervisor_stderr.log" ]; then
        echo -e "${YELLOW}=== Supervisor错误日志 ===${NC}"
        tail -n 30 "$LOG_DIR/supervisor_stderr.log"
        echo ""
    fi
    
    # 查看Nginx错误日志
    echo -e "${YELLOW}=== Nginx错误日志 ===${NC}"
    sudo tail -n 30 /var/log/nginx/excel_upload_system_error.log 2>/dev/null || echo "无法访问Nginx日志"
    echo ""
}

# 监控服务函数
monitor_service() {
    echo -e "${BLUE}开始监控服务状态...${NC}"
    echo -e "${BLUE}按 Ctrl+C 停止监控${NC}"
    echo ""
    
    while true; do
        clear
        echo -e "${YELLOW}=== Excel上传分析系统 - 服务监控 [$(date)] ===${NC}"
        echo ""
        check_service_status
        echo ""
        echo -e "${BLUE}等待10秒刷新...${NC}"
        sleep 10
    done
}

# 健康检查函数
health_check() {
    echo -e "${BLUE}执行健康检查...${NC}"
    
    # 检查进程状态
    if pgrep -f gunicorn > /dev/null; then
        echo -e "${GREEN}✓ 应用进程运行正常${NC}"
    else
        echo -e "${RED}✗ 应用进程未运行，正在尝试重启...${NC}"
        start_service
        return 1
    fi
    
    # 检查端口监听
    if netstat -tulpn | grep :5000 > /dev/null; then
        echo -e "${GREEN}✓ 端口5000正常监听${NC}"
    else
        echo -e "${RED}✗ 端口5000未监听，正在尝试重启...${NC}"
        start_service
        return 1
    fi
    
    # 检查目录权限
    if [ -w "$PROJECT_DIR/data/uploads" ]; then
        echo -e "${GREEN}✓ 上传目录权限正常${NC}"
    else
        echo -e "${RED}✗ 上传目录权限异常，正在修复...${NC}"
        sudo chown -R www-data:www-data "$PROJECT_DIR/data/uploads"
        sudo chmod -R 755 "$PROJECT_DIR/data/uploads"
    fi
    
    # 检查磁盘空间
    disk_free=$(df -h "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_free" -lt 90 ]; then
        echo -e "${GREEN}✓ 磁盘空间充足: ${disk_free}%${NC}"
    else
        echo -e "${YELLOW}⚠ 磁盘空间警告: ${disk_free}%${NC}"
    fi
    
    echo -e "${GREEN}健康检查完成！${NC}"
    return 0
}

# 根据命令参数执行对应函数
case "$1" in
    status)
        check_service_status
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    logs)
        view_logs
        ;;
    monitor)
        monitor_service
        ;;
    check)
        health_check
        ;;
    *)
        echo -e "${RED}错误：未知命令 '$1'${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}服务管理脚本执行完成${NC}"