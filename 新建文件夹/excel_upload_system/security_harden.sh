#!/bin/bash
# -*- coding: utf-8 -*-
"""
Excel上传分析系统 - 安全加固与HTTPS配置脚本

用途：为Excel上传系统配置全面的安全加固措施和HTTPS加密
使用方法：bash security_harden.sh [--domain 域名] [--email 邮箱] [--force]

功能包括：
1. HTTPS配置（使用Let's Encrypt证书）
2. Nginx安全头配置
3. 防火墙规则优化
4. SSH安全加固
5. 防暴力破解配置
6. 系统安全更新
7. 文件权限修复
"""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DOMAIN=""
EMAIL=""
FORCE=false
LOG_FILE="security_harden.log"
PROJECT_DIR="/opt/excel_upload_system"
NGINX_CONFIG="/etc/nginx/sites-available/excel_upload_system"

# 检查脚本是否以root权限运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}错误：请以root用户权限运行此脚本${NC}"
        exit 1
    fi
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --force)
                FORCE=true
                shift
                ;;
            *)
                echo -e "${RED}未知参数: $1${NC}"
                echo "使用方法: bash security_harden.sh [--domain 域名] [--email 邮箱] [--force]"
                exit 1
                ;;
        esac
done

# 如果没有提供域名和邮箱，提示用户输入
if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ] && [ "$FORCE" = false ]; then
    echo -e "${YELLOW}注意：要配置HTTPS，需要提供域名和邮箱信息${NC}"
    read -p "请输入您的域名（例如：example.com）: " DOMAIN
    read -p "请输入您的邮箱（用于Let's Encrypt通知）: " EMAIL
    
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        echo -e "${YELLOW}未提供域名和邮箱，将跳过HTTPS配置，仅进行安全加固${NC}"
        sleep 2
    fi
fi
}

# 初始化日志
init_log() {
    echo -e "${BLUE}正在初始化安全加固日志...${NC}"
    echo "===== Excel上传系统安全加固日志 =====