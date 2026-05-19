# Nginx最佳实践指南 - Excel上传分析系统

## 一、基础配置优化

### 1. 工作进程优化

编辑 `/etc/nginx/nginx.conf` 文件，根据服务器CPU核心数优化工作进程：

```nginx
# 工作进程数，建议设置为CPU核心数
worker_processes auto;

# 每个工作进程的最大连接数
worker_connections 4096;

# 连接复用
keepalive_timeout 65;
keepalive_requests 100;

# 使用epoll事件模型（Linux系统推荐）
events {
    use epoll;
    multi_accept on;
}
```

### 2. 缓存配置

优化静态文件缓存以提高性能：

```nginx
# 在http块中添加
http {
    # 文件缓存配置
    open_file_cache max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
    
    # 压缩配置
    gzip on;
    gzip_comp_level 6;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # 客户端请求缓冲区
    client_body_buffer_size 128k;
    client_max_body_size 1m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # 响应缓冲区
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
}
```

## 二、安全配置

### 1. 防止常见攻击

```nginx
# 在server块中添加
server {
    # 隐藏Nginx版本信息
    server_tokens off;
    
    # 防止点击劫持
    add_header X-Frame-Options SAMEORIGIN;
    
    # 防止MIME类型嗅探
    add_header X-Content-Type-Options nosniff;
    
    # 启用XSS保护
    add_header X-XSS-Protection "1; mode=block";
    
    # 启用内容安全策略
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;";
    
    # 限制请求方法
    if ($request_method !~ ^(GET|POST|HEAD|OPTIONS)$ ) {
        return 405;
    }
    
    # 防止恶意请求
    if ($http_user_agent ~* (nikto|nmap|w3af|acunetix|nessus|nessus|sqlmap|fimap|havij|arachni|grabber|webscarab|netsparker)) {
        return 403;
    }
}
```

### 2. 请求速率限制

```nginx
# 在http块中添加
http {
    # 定义限流区域
    limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;
}

# 在server块中添加
server {
    # 应用限流
    location / {
        limit_req zone=mylimit burst=20 nodelay;
    }
    
    # 对上传接口单独限流
    location /upload {
        limit_req zone=mylimit burst=5 nodelay;
    }
}
```

## 三、HTTPS配置

### 1. 获取SSL证书

推荐使用Let's Encrypt免费证书：

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书并自动配置Nginx
sudo certbot --nginx -d 您的域名
```

### 2. SSL优化配置

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name 您的域名;
    
    # SSL证书路径
    ssl_certificate /etc/letsencrypt/live/您的域名/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/您的域名/privkey.pem;
    
    # SSL优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
}

# 重定向HTTP到HTTPS
server {
    listen 80;
    listen [::]:80;
    
    server_name 您的域名;
    return 301 https://$host$request_uri;
}
```

## 四、静态文件优化

### 1. 缓存控制

```nginx
location /static/ {
    alias /opt/excel_upload_system/app/static/;
    
    # 缓存控制
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
    
    # ETag支持
    add_header ETag "$body_bytes_sent-$msec";
    
    # 压缩静态文件
    gzip_static on;
    
    # 访问控制
    add_header Access-Control-Allow-Origin *;
    
    # 日志记录优化
    access_log off;
    log_not_found off;
}
```

### 2. 大文件上传配置

```nginx
# 在http块中添加
client_max_body_size 100m;
client_body_timeout 120s;

# 在server块中添加
location /api/upload {
    proxy_pass http://127.0.0.1:5000;
    
    # 大文件上传配置
    proxy_request_buffering off;
    proxy_http_version 1.1;
    proxy_buffering off;
    
    # 增加超时时间
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    
    # 缓冲区设置
    proxy_buffers 8 16k;
    proxy_buffer_size 32k;
}
```

## 五、日志和监控

### 1. 日志配置

```nginx
# 自定义日志格式
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for"';

# 访问日志
access_log /var/log/nginx/excel_upload_system_access.log main;

# 错误日志
error_log /var/log/nginx/excel_upload_system_error.log warn;
```

### 2. 健康检查端点

```nginx
location /health {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

## 六、Nginx性能监控

### 1. 启用状态页

```nginx
# 在http块中添加
server {
    listen 127.0.0.1:8080;
    server_name localhost;
    
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

### 2. 配置日志轮转

```bash
# 创建日志轮转配置
cat > /etc/logrotate.d/nginx << 'EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -s /run/nginx.pid ] && kill -USR1 `cat /run/nginx.pid`
    endscript
}
EOF
```

## 七、故障排查指南

### 1. 常见错误及解决方案

#### 502 Bad Gateway
- 检查Gunicorn服务是否运行：`sudo supervisorctl status excel_upload_system`
- 检查端口监听：`netstat -tulpn | grep 5000`
- 检查Gunicorn日志：`tail -n 100 /opt/excel_upload_system/logs/gunicorn_error.log`

#### 504 Gateway Timeout
- 增加Nginx超时设置：`proxy_read_timeout 300;`
- 检查Gunicorn工作进程数量是否足够
- 检查服务器资源使用情况

#### 413 Request Entity Too Large
- 增加Nginx客户端请求大小限制：`client_max_body_size 100m;`

### 2. Nginx命令参考

```bash
# 测试配置语法
sudo nginx -t

# 重新加载配置
sudo nginx -s reload

# 查看Nginx进程
sudo ps aux | grep nginx

# 查看端口监听
sudo netstat -tulpn | grep nginx

# 查看访问日志
tail -f /var/log/nginx/excel_upload_system_access.log

# 查看错误日志
tail -f /var/log/nginx/excel_upload_system_error.log
```

## 八、性能调优建议

1. **根据服务器内存调整缓冲区大小**：
   - 小内存服务器（1-2GB）：减小buffer大小
   - 大内存服务器（4GB+）：增大buffer大小

2. **启用HTTP/2**：
   - 在HTTPS配置中添加`http2`参数
   - 显著提升并发连接性能

3. **配置连接池**：
   ```nginx
   upstream flask_app {
       server 127.0.0.1:5000;
       keepalive 32;
   }
   
   location / {
       proxy_pass http://flask_app;
       proxy_http_version 1.1;
       proxy_set_header Connection "";
   }
   ```

4. **根据流量调整工作进程**：
   - 高并发场景：考虑增加worker_processes数量
   - 调整worker_rlimit_nofile增加文件描述符限制

5. **监控并优化**：
   - 定期检查访问日志识别慢请求
   - 使用nginx-top等工具监控实时性能

---

按照以上配置优化Nginx，可以显著提升Excel上传分析系统的性能、安全性和稳定性，为用户提供更好的服务体验。