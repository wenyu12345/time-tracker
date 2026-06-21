import os
from datetime import timezone, timedelta

# 定义北京时间时区 (UTC+8)
BEIJING_TIMEZONE = timezone(timedelta(hours=8), name='Asia/Shanghai')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')
    PORT = 5000
    DEBUG = True
    TIMEZONE = BEIJING_TIMEZONE