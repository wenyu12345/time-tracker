# Excel上传分析系统 - 腾讯云部署指南

## 一、服务器环境准备

### 1. 服务器选型建议
- **推荐配置**：腾讯云轻量应用服务器 2核4G 5M带宽
- **操作系统**：Ubuntu 20.04 LTS 64位
- **存储**：40GB SSD云硬盘（根据数据量可调整）

### 2. 服务器环境初始化

#### 2.1 连接服务器
```bash
# 使用SSH连接服务器
ssh root@您的服务器IP
```

#### 2.2 系统更新
```bash
# 更新系统软件包
sudo apt update && sudo apt upgrade -y

# 安装必要的系统工具
sudo apt install -y git wget curl unzip build-essential
```

#### 2.3 Python环境配置
```bash
# 安装Python 3.9（项目兼容Python 3.7+）
sudo apt install -y python3.9 python3.9-dev python3.9-venv python3-pip

# 设置Python 3.9为默认版本
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

# 升级pip
sudo pip3 install --upgrade pip
```

#### 2.4 创建虚拟环境
```bash
# 创建项目目录
mkdir -p /opt/excel_upload_system
cd /opt/excel_upload_system

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

#### 2.5 防火墙配置
```bash
# 允许SSH连接
sudo ufw allow 22/tcp

# 允许应用访问端口
sudo ufw allow 5000/tcp

# 允许HTTP/HTTPS访问（后续Nginx使用）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

## 二、项目部署

### 1. 上传项目代码
```bash
# 方法一：使用Git克隆（如果代码已托管）
git clone https://您的代码仓库地址 .

# 方法二：使用SCP上传
# 在本地执行：
# scp -r 本地项目目录 root@您的服务器IP:/opt/excel_upload_system/
```

### 2. 安装项目依赖
```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt

# 安装生产环境额外依赖
pip install gunicorn supervisor
```

### 3. 创建Gunicorn配置文件

创建 `/opt/excel_upload_system/gunicorn_config.py`：
```python
# Gunicorn配置文件
import multiprocessing
import os

# 绑定地址和端口
bind = "127.0.0.1:5000"

# 工作进程数量（根据CPU核心数调整）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作线程数
threads = 2

# 最大并发请求数
worker_connections = 1000

# 工作模式
after_worker_init = "app.utils.startup:init_app"

# 日志配置
accesslog = "/opt/excel_upload_system/logs/gunicorn_access.log"
errorlog = "/opt/excel_upload_system/logs/gunicorn_error.log"
loglevel = "info"

# 超时设置
timeout = 300
```

### 4. 创建Supervisor配置

创建 `/etc/supervisor/conf.d/excel_upload_system.conf`：
```ini
[program:excel_upload_system]
# 命令路径
command=/opt/excel_upload_system/venv/bin/gunicorn -c /opt/excel_upload_system/gunicorn_config.py main:app

# 项目目录
directory=/opt/excel_upload_system

# 启动用户
user=www-data

# 自动启动和重启
autostart=true
autorestart=true
startsecs=5

# 日志配置
stdout_logfile=/opt/excel_upload_system/logs/supervisor_stdout.log
stderr_logfile=/opt/excel_upload_system/logs/supervisor_stderr.log
stdout_logfile_maxbytes=50MB
stderr_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_backups=10

# 环境变量
environment=PATH="/opt/excel_upload_system/venv/bin:%(ENV_PATH)s"
```

### 5. 配置Nginx反向代理

创建 `/etc/nginx/sites-available/excel_upload_system`：
```nginx
server {
    listen 80;
    server_name 您的域名或IP地址;

    # 访问日志
    access_log /var/log/nginx/excel_upload_system_access.log;
    error_log /var/log/nginx/excel_upload_system_error.log;

    # 静态文件配置
    location /static/ {
        alias /opt/excel_upload_system/static/;
        expires 30d;
    }

    # 上传文件配置
    location /uploads/ {
        alias /opt/excel_upload_system/data/uploads/;
        internal;
    }

    # 代理到Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 增加超时设置以支持大文件上传
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
```

启用Nginx配置：
```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/excel_upload_system /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

## 三、服务管理

### 1. 启动服务
```bash
# 创建日志目录
mkdir -p /opt/excel_upload_system/logs

# 重启Supervisor
sudo systemctl restart supervisor

# 启动应用
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start excel_upload_system
```

### 2. 查看服务状态
```bash
# 查看应用状态
sudo supervisorctl status excel_upload_system

# 查看Nginx状态
sudo systemctl status nginx
```

### 3. 配置自动备份
创建 `/opt/excel_upload_system/backup.sh`：
```bash
#!/bin/bash

# 备份目录
BACKUP_DIR="/opt/excel_upload_system/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份上传数据
zip -r $BACKUP_DIR/uploads_$TIMESTAMP.zip /opt/excel_upload_system/data/uploads/

# 备份应用配置
zip -r $BACKUP_DIR/config_$TIMESTAMP.zip /opt/excel_upload_system/app/

# 清理7天前的备份
find $BACKUP_DIR -name "*.zip" -type f -mtime +7 -delete

echo "Backup completed at $TIMESTAMP"
```

设置定时任务：
```bash
chmod +x /opt/excel_upload_system/backup.sh
crontab -e
# 添加以下内容（每天凌晨2点执行备份）
0 2 * * * /opt/excel_upload_system/backup.sh >> /opt/excel_upload_system/logs/backup.log 2>&1
```

## 四、安全配置

### 1. 创建专用用户
```bash
# 创建专用用户
sudo useradd -r -s /bin/false www-data

# 设置目录权限
sudo chown -R www-data:www-data /opt/excel_upload_system/data/sudo chmod -R 755 /opt/excel_upload_system
```

### 2. 配置HTTPS（可选）
```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d 您的域名
```

## 五、部署后验证

1. 访问 `http://您的服务器IP` 或 `https://您的域名` 检查服务是否正常运行
2. 测试Excel文件上传功能
3. 检查版本显示是否正确（应显示3.0.0版本）
4. 查看系统日志确认无错误

## 六、注意事项

1. 定期检查服务器资源使用情况
2. 监控应用日志，及时发现并解决问题
3. 定期更新系统和依赖包
4. 建议为重要数据配置远程备份
5. 考虑配置监控告警系统

---

部署完成后，系统将在腾讯云上稳定运行，提供Excel数据上传、分析和统计功能。如有任何问题，请查看相关日志或联系技术支持。