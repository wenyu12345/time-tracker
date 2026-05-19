# Gunicorn配置文件 - Excel上传分析系统
# 用于腾讯云服务器生产环境部署

import multiprocessing
import os
import sys

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 添加项目根目录到Python路径
sys.path.insert(0, project_root)

# 绑定地址和端口
bind = "127.0.0.1:5001"

# 工作进程数量（根据CPU核心数自动调整）
workers = multiprocessing.cpu_count() * 2 + 1

# 每个工作进程的线程数
threads = 2

# 最大并发连接数
worker_connections = 1000

# 工作模式 - 推荐使用gevent模式提高并发性能
worker_class = "gevent"

# 超时设置（秒）
timeout = 300
graceful_timeout = 30
keepalive = 2

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 100

# 日志配置
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)

accesslog = os.path.join(log_dir, 'gunicorn_access.log')
errorlog = os.path.join(log_dir, 'gunicorn_error.log')
loglevel = "info"

# 日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 进程名称
proc_name = 'excel_upload_system'

# 用户和组（生产环境运行用户）
# user = 'www-data'
# group = 'www-data'

# 环境变量
environ = {
    'FLASK_ENV': 'production',
    'FLASK_APP': 'main.py',
    'PYTHONPATH': project_root
}

# 预加载应用（提高性能）
preload_app = True

# 监听文件变化（开发环境使用，生产环境建议关闭）
# reload = True

# 启动钩子
def on_starting(server):
    """服务器启动时执行"""
    server.log.info("Excel上传分析系统服务器启动中...")

# 工作进程初始化钩子
def worker_init(worker):
    """工作进程初始化时执行"""
    worker.log.info("工作进程初始化")
    
    # 确保上传目录存在
    upload_dir = os.path.join(project_root, 'data', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

# 工作进程退出钩子
def worker_exit(server, worker):
    """工作进程退出时执行"""
    worker.log.info("工作进程退出")

# 服务器关闭钩子
def on_exit(server):
    """服务器关闭时执行"""
    server.log.info("Excel上传分析系统服务器关闭")