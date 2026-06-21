# 部署指南

## 🚀 快速部署方案

### 方案一：Railway.app（推荐，最简单）

#### 步骤：

1. **准备代码**
   ```bash
   cd d:\新建文件夹\小工具\time-tracker
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **创建GitHub仓库**
   - 访问 https://github.com/new
   - 创建新仓库
   - 推送代码到GitHub

3. **部署到Railway**
   - 访问 https://railway.app
   - 登录账号
   - 点击 "New Project"
   - 选择 "Deploy from repo"
   - 选择您的仓库
   - 配置：
     - Root Directory: 留空
     - Build Command: `pip install -r backend/requirements.txt`
     - Start Command: `cd backend && gunicorn app:app --preload --workers 4 --timeout 300 --bind 0.0.0.0:$PORT`
   - 点击 "Deploy"

4. **注意事项**
   - Ollama功能无法在云服务器上正常使用（需要本地安装Ollama）
   - 可以使用在线AI API替代（如OpenAI、DeepSeek等）

---

### 方案二：Render.com

#### 步骤：

1. 同样先推送到GitHub
2. 访问 https://render.com
3. 点击 "New +" → "Web Service"
4. 连接GitHub仓库
5. 配置：
   - Root Directory: 留空
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && gunicorn app:app --preload --workers 4 --timeout 300 --bind 0.0.0.0:$PORT`
6. 部署

---

### 方案三：VPS部署（腾讯云/阿里云）

#### 1. 购买VPS
- 选择Ubuntu 20.04/22.04系统
- 配置至少1核2G

#### 2. 连接服务器
```bash
ssh root@your-server-ip
```

#### 3. 安装依赖
```bash
# 更新系统
apt update && apt upgrade -y

# 安装Python
apt install python3 python3-pip python3-venv -y

# 安装Nginx
apt install nginx -y
```

#### 4. 上传代码
```bash
# 使用scp上传
scp -r time-tracker root@your-server-ip:/root/

# 或者使用git clone
cd /root
git clone your-repo-url time-tracker
cd time-tracker
```

#### 5. 配置环境
```bash
cd /root/time-tracker/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python3 init_db.py
```

#### 6. 配置Gunicorn
创建 `/etc/systemd/system/time-tracker.service`:
```ini
[Unit]
Description=Time Tracker Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/root/time-tracker/backend
Environment="PATH=/root/time-tracker/backend/venv/bin"
ExecStart=/root/time-tracker/backend/venv/bin/gunicorn app:app --preload --workers 4 --timeout 300 --bind 127.0.0.1:5000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
systemctl daemon-reload
systemctl start time-tracker
systemctl enable time-tracker
```

#### 7. 配置Nginx
创建 `/etc/nginx/sites-available/time-tracker`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

启用配置：
```bash
ln -s /etc/nginx/sites-available/time-tracker /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### 8. 配置SSL（可选，推荐）
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

---

## ⚠️ 重要说明

### 1. Ollama功能限制
当前代码中的Ollama功能需要：
- 本地安装Ollama
- 有足够的GPU/CPU资源
- 对于云服务器，可以：
  - 禁用Ollama相关功能
  - 改用在线AI API（OpenAI、DeepSeek、Claude等）

### 2. 数据库
- 当前使用SQLite（文件数据库）
- 对于生产环境，建议改用MySQL或PostgreSQL

### 3. 安全性
- 修改默认密码
- 配置环境变量
- 定期备份数据库

---

## 📞 需要帮助？

如果在部署过程中遇到问题，请告诉我具体的错误信息，我会帮您解决！
