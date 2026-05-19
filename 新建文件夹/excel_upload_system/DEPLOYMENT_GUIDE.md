# Excel上传分析系统部署指南

## 文档概述

本文档提供Excel上传分析系统在腾讯云服务器上的完整部署指南、服务管理方法和故障排查步骤。本指南适用于系统管理员和开发人员，确保系统能够稳定、安全地运行。

## 目录

1. [系统概述](#系统概述)
2. [部署前准备](#部署前准备)
3. [环境配置](#环境配置)
4. [项目部署](#项目部署)
5. [服务管理](#服务管理)
6. [故障排查](#故障排查)
7. [性能优化](#性能优化)
8. [安全配置](#安全配置)
9. [备份与恢复](#备份与恢复)
10. [常见问题](#常见问题)

## 系统概述

### 系统架构

Excel上传分析系统采用以下架构：

- **前端**：HTML, CSS, JavaScript
- **后端**：Flask (Python 3)
- **数据处理**：pandas, openpyxl
- **服务部署**：Gunicorn + Supervisor
- **反向代理**：Nginx
- **数据存储**：JSON文件存储 + 会话存储

### 核心功能

- Excel文件上传和处理
- 型号映射规则管理
- 数据格式转换和分析
- 开红莲模式特殊处理
- 钉钉机器人通知集成

## 部署前准备

### 硬件要求

- **CPU**：至少2核
- **内存**：至少4GB RAM
- **磁盘**：至少20GB可用空间
- **网络**：公网IP地址（建议带宽1Mbps以上）

### 软件要求

- **操作系统**：Ubuntu 20.04 LTS 或 CentOS 7/8
- **Python**：3.8 或更高版本
- **Web服务器**：Nginx 1.18 或更高版本
- **进程管理**：Supervisor 4.2 或更高版本
- **依赖包管理器**：pip 20.0 或更高版本

### 防火墙配置

确保以下端口开放：
- **80/tcp**：HTTP服务
- **443/tcp**：HTTPS服务（可选，推荐）
- **5000/tcp**：Gunicorn服务（仅内网访问）

## 环境配置

### 1. 服务器初始配置

#### Ubuntu系统

```bash
# 更新系统包
apt update && apt upgrade -y

# 安装必要的系统包
apt install -y python3 python3-dev python3-pip python3-venv nginx supervisor git unzip curl

# 配置防火墙（UFW）
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp  # SSH访问
ufw enable
```

#### CentOS系统

```bash
# 更新系统包
yum update -y

# 安装必要的系统包
yum install -y epel-release
yum install -y python3 python3-devel python3-pip nginx supervisor git unzip curl

# 配置防火墙（Firewalld）
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ssh
firewall-cmd --reload
```

### 2. Python虚拟环境创建

```bash
# 创建项目目录
mkdir -p /opt/excel_upload_system
cd /opt/excel_upload_system

# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip和setuptools
pip install --upgrade pip setuptools
```

### 3. 上传项目代码

可以通过以下方式上传代码：

#### 方法1：使用Git克隆（推荐）

```bash
cd /opt/excel_upload_system
git clone [您的Git仓库URL] .
```

#### 方法2：使用SCP上传本地代码

在本地执行：

```bash
scp -r /path/to/local/excel_upload_system username@server_ip:/opt/
```

## 项目部署

### 1. 安装项目依赖

```bash
cd /opt/excel_upload_system
source venv/bin/activate

# 安装基础依赖
pip install -r requirements.txt

# 安装生产环境依赖
pip install gunicorn==21.2.0 supervisor==4.2.5 gevent==23.9.1
```

### 2. 配置Gunicorn

创建Gunicorn配置文件：

```bash
cat > /opt/excel_upload_system/gunicorn_config.py << 'EOF'
# Gunicorn配置文件
import multiprocessing

# 绑定地址和端口
bind = '127.0.0.1:5000'

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作类型
worker_class = 'gevent'

# 每个工作进程的最大请求数
after_requests = 1000

# 超时设置
timeout = 60

# 访问日志
accesslog = '/opt/excel_upload_system/logs/gunicorn_access.log'

# 错误日志
errorlog = '/opt/excel_upload_system/logs/gunicorn_error.log'

# 日志级别
loglevel = 'info'

# 进程ID文件
pidfile = '/opt/excel_upload_system/gunicorn.pid'

# 守护进程模式
daemon = False

# Flask应用对象
wsgi_app = 'main:app'
EOF

# 创建日志目录
mkdir -p /opt/excel_upload_system/logs
```

### 3. 配置Supervisor

创建Supervisor配置文件：

```bash
cat > /etc/supervisor/conf.d/excel_upload_system.conf << 'EOF'
[program:excel_upload_system]
# 命令
command=/opt/excel_upload_system/venv/bin/gunicorn -c /opt/excel_upload_system/gunicorn_config.py

# 工作目录
directory=/opt/excel_upload_system

# 启动用户
user=www-data

# 自动启动和重启
autostart=true
autorestart=true

# 启动延迟
startsecs=5

# 启动重试次数
startretries=3

# 退出代码视为正常退出
exitcodes=0,1

# 停止信号
stopsignal=TERM

# 停止等待时间
stopwaitsecs=10

# 重定向标准输出和错误
syslog=true
syslogpriority=info

# 环境变量
environment=
    PATH="/opt/excel_upload_system/venv/bin:$PATH",
    FLASK_ENV="production",
    SECRET_KEY="your_secret_key_here",
    TEMPLATES_AUTO_RELOAD="false"

# 进程控制
numprocs=1
process_name=%(program_name)s_%(process_num)02d

# 日志配置
stdout_logfile=/opt/excel_upload_system/logs/supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
stderr_logfile=/opt/excel_upload_system/logs/supervisor_error.log
stderr_logfile_maxbytes=10MB
stderr_logfile_backups=5
EOF
```

### 4. 配置Nginx

创建Nginx配置文件：

```bash
cat > /etc/nginx/sites-available/excel_upload_system << 'EOF'
server {
    listen 80;
    server_name _;  # 替换为您的域名或IP地址
    
    # 静态文件服务
    location /static/ {
        alias /opt/excel_upload_system/app/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # 上传文件临时目录
    location /uploads/ {
        alias /opt/excel_upload_system/app/uploads/;
        internal;
    }
    
    # 反向代理到Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 连接设置
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
        proxy_buffers 4 32k;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 请求限制
    limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;
    location / {
        limit_req zone=mylimit burst=20 nodelay;
    }
    
    # 错误页面
    error_page 500 502 503 504 /500.html;
    location = /500.html {
        root /opt/excel_upload_system/app/static/error;
    }
}
EOF

# 启用站点
ln -s /etc/nginx/sites-available/excel_upload_system /etc/nginx/sites-enabled/

# 删除默认配置
rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
nginx -t
```

### 5. 创建必要的目录和设置权限

```bash
# 创建上传目录
mkdir -p /opt/excel_upload_system/app/uploads

# 设置目录权限
chown -R www-data:www-data /opt/excel_upload_system
chmod -R 755 /opt/excel_upload_system
chmod -R 775 /opt/excel_upload_system/app/uploads
chmod -R 775 /opt/excel_upload_system/logs
```

### 6. 初始化和启动服务

```bash
# 重新加载Supervisor配置
supervisorctl reread
supervisorctl update
supervisorctl start excel_upload_system

# 重启Nginx
nginx -s reload
```

## 服务管理

### 使用一键管理脚本

系统提供了`service_manager.sh`脚本来简化服务管理操作：

```bash
cd /opt/excel_upload_system
chmod +x service_manager.sh

# 查看服务状态
./service_manager.sh status

# 启动服务
./service_manager.sh start

# 停止服务
./service_manager.sh stop

# 重启服务
./service_manager.sh restart

# 查看日志
./service_manager.sh logs

# 查看实时日志
./service_manager.sh logs --follow

# 检查服务健康状态
./service_manager.sh health
```

### 直接使用Supervisor命令

```bash
# 查看服务状态
supervisorctl status excel_upload_system

# 启动服务
supervisorctl start excel_upload_system

# 停止服务
supervisorctl stop excel_upload_system

# 重启服务
supervisorctl restart excel_upload_system

# 查看服务日志
supervisorctl tail -f excel_upload_system stdout
```

### 检查Nginx状态

```bash
# 查看Nginx状态
systemctl status nginx

# 启动Nginx
systemctl start nginx

# 停止Nginx
systemctl stop nginx

# 重启Nginx
systemctl restart nginx

# 查看Nginx错误日志
cat /var/log/nginx/error.log
```

## 故障排查

### 1. 服务无法启动

**排查步骤：**

1. 检查Supervisor日志：
   ```bash
   cat /opt/excel_upload_system/logs/supervisor_error.log
   ```

2. 检查Gunicorn日志：
   ```bash
   cat /opt/excel_upload_system/logs/gunicorn_error.log
   ```

3. 检查端口占用情况：
   ```bash
   netstat -tulpn | grep 5000
   ```

4. 手动测试启动Gunicorn：
   ```bash
   cd /opt/excel_upload_system
source venv/bin/activate
gunicorn -b 127.0.0.1:5000 main:app
   ```

### 2. 页面无法访问

**排查步骤：**

1. 检查Nginx配置和日志：
   ```bash
   nginx -t
   cat /var/log/nginx/error.log
   ```

2. 检查防火墙设置：
   ```bash
   # Ubuntu
   ufw status
   
   # CentOS
   firewall-cmd --list-all
   ```

3. 检查Gunicorn服务状态：
   ```bash
   supervisorctl status excel_upload_system
   ```

4. 测试直接访问Gunicorn：
   ```bash
   curl http://127.0.0.1:5000
   ```

### 3. 文件上传失败

**排查步骤：**

1. 检查上传目录权限：
   ```bash
   ls -la /opt/excel_upload_system/app/uploads
   ```

2. 检查Nginx客户端最大值设置：
   ```bash
   cat /etc/nginx/nginx.conf | grep client_max_body_size
   ```

3. 检查应用日志：
   ```bash
   cat /opt/excel_upload_system/logs/gunicorn_error.log
   ```

4. 确认上传文件格式是否符合要求（.xls或.xlsx）

### 4. 数据处理错误

**排查步骤：**

1. 检查Excel文件格式是否符合预期
2. 查看应用日志中的错误信息
3. 检查映射规则文件是否存在且格式正确
4. 确认系统资源是否充足（内存、CPU）

## 性能优化

### 1. Gunicorn优化

- 根据服务器CPU核心数调整工作进程数
- 调整超时设置以适应大文件处理
- 启用工作进程的自动重启以防止内存泄漏

### 2. Nginx优化

- 启用Gzip压缩
- 配置适当的缓存策略
- 调整worker_processes和worker_connections
- 优化keepalive设置

### 3. 应用优化

- 使用分页处理大数据集
- 优化Excel文件处理逻辑
- 考虑使用异步处理大文件

## 安全配置

### 1. HTTPS配置

1. 获取SSL证书（可以使用Let's Encrypt）：

   ```bash
   apt install certbot python3-certbot-nginx -y
   certbot --nginx -d your_domain.com
   ```

2. 配置Nginx强制HTTPS：

   ```nginx
   server {
       listen 80;
       server_name your_domain.com;
       return 301 https://$host$request_uri;
   }
   
   server {
       listen 443 ssl;
       server_name your_domain.com;
       
       ssl_certificate /etc/letsencrypt/live/your_domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your_domain.com/privkey.pem;
       
       # SSL优化配置
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_prefer_server_ciphers on;
       ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
       ssl_session_timeout 1d;
       ssl_session_cache shared:SSL:10m;
       ssl_stapling on;
       ssl_stapling_verify on;
       
       # 其他配置保持不变
       # ...
   }
   ```

### 2. 安全加固

- 配置适当的文件权限
- 启用DDoS保护
- 配置请求速率限制
- 定期更新系统和依赖包

## 备份与恢复

### 1. 备份策略

创建自动化备份脚本：

```bash
cat > /opt/excel_upload_system/backup.sh << 'EOF'
#!/bin/bash

# 备份脚本
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/opt/backups/excel_upload_system"
PROJECT_DIR="/opt/excel_upload_system"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份项目文件
tar -czf "$BACKUP_DIR/project_backup_$TIMESTAMP.tar.gz" -C $PROJECT_DIR .

# 备份配置文件
cp /etc/nginx/sites-available/excel_upload_system "$BACKUP_DIR/nginx_config_$TIMESTAMP.conf"
cp /etc/supervisor/conf.d/excel_upload_system.conf "$BACKUP_DIR/supervisor_config_$TIMESTAMP.conf"

# 清理7天前的备份
find $BACKUP_DIR -type f -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -type f -name "*.conf" -mtime +7 -delete

echo "备份完成: $TIMESTAMP"
EOF

chmod +x /opt/excel_upload_system/backup.sh
```

配置定时备份：

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨3点备份
0 3 * * * /opt/excel_upload_system/backup.sh >> /opt/excel_upload_system/logs/backup.log 2>&1
```

### 2. 恢复步骤

1. 停止服务：
   ```bash
   supervisorctl stop excel_upload_system
   systemctl stop nginx
   ```

2. 恢复项目文件：
   ```bash
   rm -rf /opt/excel_upload_system
   mkdir -p /opt/excel_upload_system
   tar -xzf /opt/backups/excel_upload_system/project_backup_TIMESTAMP.tar.gz -C /opt/excel_upload_system
   ```

3. 恢复配置文件：
   ```bash
   cp /opt/backups/excel_upload_system/nginx_config_TIMESTAMP.conf /etc/nginx/sites-available/excel_upload_system
   cp /opt/backups/excel_upload_system/supervisor_config_TIMESTAMP.conf /etc/supervisor/conf.d/excel_upload_system.conf
   ```

4. 重启服务：
   ```bash
   supervisorctl reread
   supervisorctl update
   supervisorctl start excel_upload_system
   systemctl start nginx
   ```

## 常见问题

### Q1: 为什么上传的Excel文件没有被正确处理？

**A1:** 请检查以下几点：
- Excel文件格式是否为.xls或.xlsx
- 文件大小是否超过了Nginx的`client_max_body_size`限制
- 上传目录权限是否正确
- Excel文件内容是否符合系统要求的格式

### Q2: 如何修改默认的上传大小限制？

**A2:** 修改Nginx配置文件：

```bash
# 编辑Nginx配置
nano /etc/nginx/nginx.conf

# 在http块中添加或修改
http {
    client_max_body_size 100M;  # 调整为需要的大小
    # ...
}

# 重启Nginx
nginx -s reload
```

### Q3: 如何查看详细的应用日志？

**A3:** 使用以下命令查看不同级别的日志：

```bash
# Gunicorn访问日志
cat /opt/excel_upload_system/logs/gunicorn_access.log

# Gunicorn错误日志
cat /opt/excel_upload_system/logs/gunicorn_error.log

# Supervisor日志
cat /opt/excel_upload_system/logs/supervisor.log

# Nginx错误日志
cat /var/log/nginx/error.log
```

### Q4: 系统运行一段时间后变得很慢，如何解决？

**A4:** 可能是内存泄漏导致的，建议：
- 配置Gunicorn的`max_requests`参数自动重启工作进程
- 定期重启服务
- 检查是否有长时间运行的进程占用资源

### Q5: 如何更新系统代码？

**A5:** 按照以下步骤更新代码：

```bash
# 停止服务
./service_manager.sh stop

# 拉取最新代码（如果使用Git）
cd /opt/excel_upload_system
git pull

# 安装新的依赖（如果有变化）
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
./service_manager.sh start
```

## 附录

### 一键部署脚本使用说明

系统提供了`deploy_to_cloud.sh`脚本，可以简化整个部署流程：

```bash
chmod +x deploy_to_cloud.sh
./deploy_to_cloud.sh --host <服务器IP> --user <用户名> --port <SSH端口>
```

### 部署测试脚本

使用`DEPLOYMENT_TESTS.py`脚本进行部署后的功能和性能测试：

```bash
cd /opt/excel_upload_system
source venv/bin/activate
python DEPLOYMENT_TESTS.py --host <服务器IP> --port 80
```

---

**文档版本**: 1.0.0
**创建日期**: 2024年
**维护人**: 系统管理员
