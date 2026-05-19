# 数据存储配置与备份策略 - Excel上传分析系统

## 一、项目数据存储现状分析

经过代码分析，Excel上传分析系统当前采用以下数据存储方式：

1. **文件存储**：使用JSON文件存储型号映射规则
2. **Session存储**：使用Flask Session存储临时处理数据
3. **内存处理**：核心数据处理（Excel文件解析、数据转换）在内存中完成
4. **本地文件**：上传的Excel文件临时存储在服务器本地

目前系统**未使用**传统关系型数据库或NoSQL数据库。

## 二、数据存储优化配置

### 1. 文件存储优化

```python
# 文件路径配置优化
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 确保目录存在并设置权限
for directory in [DATA_DIR, UPLOAD_DIR, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        # 设置适当的权限（仅用户和组可读写）
        os.chmod(directory, 0o750)
```

### 2. JSON文件读写优化

```python
import json
import os
import threading
from datetime import datetime

# 添加文件操作锁防止并发问题
file_locks = {}

# 获取文件锁
def get_file_lock(file_path):
    if file_path not in file_locks:
        file_locks[file_path] = threading.Lock()
    return file_locks[file_path]

# 优化的读取函数
def read_json_file(file_path, default_data=None):
    with get_file_lock(file_path):
        if not os.path.exists(file_path):
            return default_data or {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误 (文件: {file_path}): {str(e)}")
            # 尝试恢复或使用默认值
            return default_data or {}

# 优化的写入函数
def write_json_file(file_path, data):
    # 确保父目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 创建备份文件（时间戳命名）
    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    
    with get_file_lock(file_path):
        # 如果原文件存在，先备份
        if os.path.exists(file_path):
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                logger.warning(f"创建备份文件失败: {str(e)}")
        
        # 写入数据
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 设置文件权限
            os.chmod(file_path, 0o640)
            return True
        except Exception as e:
            logger.error(f"写入JSON文件失败 (文件: {file_path}): {str(e)}")
            return False
```

### 3. Session存储优化

在 `app/__init__.py` 中添加以下配置：

```python
from flask import Flask
import os
import tempfile

app = Flask(__name__)

# 生成安全的SECRET_KEY
if 'SECRET_KEY' not in app.config:
    app.config['SECRET_KEY'] = os.urandom(24)

# 配置Session存储
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储Session
app.config['SESSION_FILE_DIR'] = os.path.join(tempfile.gettempdir(), 'excel_upload_system_sessions')
app.config['SESSION_PERMANENT'] = False  # Session不过期
app.config['SESSION_USE_SIGNER'] = True  # 使用签名保护Session
app.config['SESSION_KEY_PREFIX'] = 'excel_upload_'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS环境下启用
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问Cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 防止CSRF攻击

# 初始化Session
from flask_session import Session
Session(app)
```

### 4. 上传文件存储优化

```python
# 文件上传配置优化
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB限制
app.config['UPLOAD_ALLOWED_EXTENSIONS'] = {'xlsx', 'xls', 'csv'}

# 文件命名规则（添加时间戳避免冲突）
def generate_safe_filename(original_filename):
    from werkzeug.utils import secure_filename
    from datetime import datetime
    import os
    
    secure_name = secure_filename(original_filename)
    name, ext = os.path.splitext(secure_name)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{name}_{timestamp}{ext}"

# 文件自动清理功能
def cleanup_old_uploads(max_age_hours=24):
    import os
    import time
    
    upload_dir = app.config['UPLOAD_FOLDER']
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    if not os.path.exists(upload_dir):
        return
    
    removed_count = 0
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    removed_count += 1
                    logger.info(f"已删除过期上传文件: {filename}")
                except Exception as e:
                    logger.error(f"删除文件失败 {filename}: {str(e)}")
    
    if removed_count > 0:
        logger.info(f"共清理 {removed_count} 个过期上传文件")
```

## 三、数据备份策略

### 1. 自动化备份脚本

创建 `backup_system.py` 文件：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Excel上传系统自动备份脚本"""

import os
import sys
import shutil
import tarfile
import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('backup_system')

# 定义路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

# 确保备份目录存在
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup():
    """创建系统备份"""
    try:
        # 生成备份文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"excel_upload_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        logger.info(f"开始创建备份: {backup_filename}")
        
        # 创建压缩文件
        with tarfile.open(backup_path, "w:gz") as tar:
            # 添加数据目录
            if os.path.exists(DATA_DIR):
                tar.add(DATA_DIR, arcname=os.path.basename(DATA_DIR))
                logger.info(f"已添加数据目录: {DATA_DIR}")
            
            # 添加日志目录
            if os.path.exists(LOG_DIR):
                tar.add(LOG_DIR, arcname=os.path.basename(LOG_DIR))
                logger.info(f"已添加日志目录: {LOG_DIR}")
        
        backup_size = os.path.getsize(backup_path) / (1024 * 1024)
        logger.info(f"备份完成: {backup_filename} ({backup_size:.2f} MB)")
        
        # 清理旧备份（保留最近7个）
        cleanup_old_backups()
        
        return backup_path
        
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return None

def cleanup_old_backups(max_backups=7):
    """清理旧备份，保留指定数量的最新备份"""
    try:
        # 获取所有备份文件，按修改时间排序
        backups = [(os.path.join(BACKUP_DIR, f), os.path.getmtime(os.path.join(BACKUP_DIR, f))) 
                   for f in os.listdir(BACKUP_DIR) if f.endswith('.tar.gz')]
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # 删除多余的备份
        if len(backups) > max_backups:
            backups_to_remove = backups[max_backups:]
            for backup_path, _ in backups_to_remove:
                os.remove(backup_path)
                logger.info(f"已删除旧备份: {os.path.basename(backup_path)}")
    except Exception as e:
        logger.error(f"清理旧备份失败: {str(e)}")

def restore_from_backup(backup_file):
    """从备份恢复系统"""
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_file)
        if not os.path.exists(backup_path):
            logger.error(f"备份文件不存在: {backup_file}")
            return False
        
        logger.info(f"开始从备份恢复: {backup_file}")
        
        # 解压缩备份文件
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(BASE_DIR)
        
        logger.info(f"恢复完成: {backup_file}")
        return True
        
    except Exception as e:
        logger.error(f"恢复备份失败: {str(e)}")
        return False

def list_backups():
    """列出所有备份"""
    try:
        backups = [(f, os.path.getmtime(os.path.join(BACKUP_DIR, f))) 
                   for f in os.listdir(BACKUP_DIR) if f.endswith('.tar.gz')]
        backups.sort(key=lambda x: x[1], reverse=True)
        
        for filename, timestamp in backups:
            backup_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            size = os.path.getsize(os.path.join(BACKUP_DIR, filename)) / (1024 * 1024)
            print(f"- {filename} ({backup_time}) - {size:.2f} MB")
            
    except Exception as e:
        logger.error(f"列出备份失败: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "create":
            create_backup()
        elif sys.argv[1] == "list":
            list_backups()
        elif sys.argv[1] == "restore" and len(sys.argv) > 2:
            restore_from_backup(sys.argv[2])
        else:
            print("用法: python backup_system.py [create|list|restore 备份文件名]")
    else:
        # 默认创建备份
        create_backup()
```

### 2. 备份计划配置

在Linux系统中，使用crontab设置定时备份：

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天凌晨2点执行备份）
0 2 * * * cd /opt/excel_upload_system && python backup_system.py create >> /var/log/excel_backup.log 2>&1
```

在Windows系统中，创建任务计划：

```batch
@echo off
cd d:\excel_upload_system
python backup_system.py create
```

### 3. 备份验证与恢复测试

创建 `test_backup.py` 文件：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""备份验证与恢复测试脚本"""

import os
import sys
import shutil
import tempfile
import unittest
from backup_system import create_backup, restore_from_backup, list_backups

class BackupTest(unittest.TestCase):
    def setUp(self):
        # 创建测试环境
        self.test_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # 创建测试数据
        os.makedirs('data', exist_ok=True)
        with open('data/test.json', 'w') as f:
            f.write('{"test": "data"}')
            
    def tearDown(self):
        # 清理测试环境
        os.chdir(self.orig_dir)
        shutil.rmtree(self.test_dir)
    
    def test_backup_restore(self):
        # 创建备份
        backup_path = create_backup()
        self.assertTrue(os.path.exists(backup_path))
        
        # 修改测试数据
        with open('data/test.json', 'w') as f:
            f.write('{"test": "modified"}')
        
        # 恢复备份
        success = restore_from_backup(os.path.basename(backup_path))
        self.assertTrue(success)
        
        # 验证数据已恢复
        with open('data/test.json', 'r') as f:
            content = f.read()
        self.assertEqual(content, '{"test": "data"}')

if __name__ == '__main__':
    unittest.main()
```

## 四、未来数据库迁移建议

### 1. 数据库选型建议

| 数据库类型 | 推荐场景 | 不推荐场景 |
|------------|----------|------------|
| SQLite     | 小型部署、单机运行、低并发 | 高并发、大数据量、集群部署 |
| PostgreSQL | 企业级部署、数据完整性要求高、复杂查询 | 资源受限的环境、简单应用 |
| MySQL/MariaDB | 一般生产环境、中等并发、关系数据存储 | 超大规模数据、复杂JSON操作 |

**推荐**：对于Excel上传分析系统，初期可使用SQLite快速部署，后期根据需求增长迁移到PostgreSQL。

### 2. 数据库迁移步骤

#### 步骤1：安装数据库依赖

```bash
# 安装SQLAlchemy和数据库驱动
pip install sqlalchemy psycopg2-binary  # PostgreSQL
# 或
pip install sqlalchemy pymysql          # MySQL
# 或
pip install sqlalchemy                  # SQLite (内置)
```

#### 步骤2：创建数据库模型

创建 `app/models/db_model.py`：

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class ModelMapping(Base):
    """型号映射规则表"""
    __tablename__ = 'model_mappings'
    
    id = Column(Integer, primary_key=True)
    prefix = Column(String(20), unique=True, nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UploadedFile(Base):
    """上传文件记录表"""
    __tablename__ = 'uploaded_files'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_size = Column(Integer)  # 文件大小（字节）
    file_type = Column(String(50))  # 文件类型
    processed = Column(Integer, default=0)  # 处理状态：0-未处理，1-处理中，2-处理完成，3-处理失败
    data_count = Column(Integer)  # 处理后的数据行数
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    error_message = Column(Text)  # 错误信息

class ProcessedData(Base):
    """处理后的数据表"""
    __tablename__ = 'processed_data'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, index=True)  # 关联uploaded_files表
    model_number = Column(String(100), index=True)  # 型号
    workshop = Column(String(100), index=True)  # 车间
    batch_number = Column(String(100), index=True)  # 批号
    weight = Column(String(50))  # 重量
    original_workshop = Column(String(100))  # 原车间
    target_workshop = Column(String(100))  # 目标车间
    processed_at = Column(DateTime, default=datetime.utcnow)
    other_data = Column(Text)  # 其他数据（JSON格式）

# 数据库连接配置
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///excel_upload.db')

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库表
def init_db():
    Base.metadata.create_all(bind=engine)

# 依赖注入函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 步骤3：修改应用配置

在 `app/__init__.py` 中添加：

```python
# 导入数据库模型
from app.models.db_model import init_db

# 初始化数据库
with app.app_context():
    init_db()
```

#### 步骤4：迁移现有数据

创建 `migrate_data.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据迁移脚本 - 从JSON文件迁移到数据库"""

import json
import os
import logging
from app.models.db_model import get_db, ModelMapping

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_migration')

# 原JSON文件路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPINGS_FILE = os.path.join(BASE_DIR, 'data', 'model_mappings.json')

def migrate_model_mappings():
    """迁移型号映射数据"""
    try:
        # 读取JSON文件
        if not os.path.exists(MAPPINGS_FILE):
            logger.warning(f"映射文件不存在: {MAPPINGS_FILE}")
            return 0
        
        with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        # 连接数据库
        db = next(get_db())
        
        # 迁移数据
        migrated_count = 0
        for prefix, model_name in mappings.items():
            # 检查是否已存在
            existing = db.query(ModelMapping).filter_by(prefix=prefix).first()
            if not existing:
                new_mapping = ModelMapping(
                    prefix=prefix,
                    model_name=model_name
                )
                db.add(new_mapping)
                migrated_count += 1
            elif existing.model_name != model_name:
                # 更新现有记录
                existing.model_name = model_name
                migrated_count += 1
        
        # 提交更改
        db.commit()
        logger.info(f"成功迁移 {migrated_count} 条型号映射记录")
        return migrated_count
        
    except Exception as e:
        logger.error(f"数据迁移失败: {str(e)}")
        # 回滚事务
        if 'db' in locals():
            db.rollback()
        return 0
    finally:
        # 关闭数据库连接
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    logger.info("开始数据迁移...")
    count = migrate_model_mappings()
    logger.info(f"数据迁移完成，共迁移 {count} 条记录")
```

### 3. 数据库配置文件模板

创建 `.env.example` 文件：

```dotenv
# 数据库配置
# SQLite配置 (默认)
DATABASE_URL="sqlite:///excel_upload.db"

# PostgreSQL配置
# DATABASE_URL="postgresql://username:password@localhost:5432/excel_upload"

# MySQL配置
# DATABASE_URL="mysql+pymysql://username:password@localhost:3306/excel_upload"

# 数据库连接池配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
```

## 五、数据存储监控与维护

### 1. 磁盘空间监控

创建 `disk_space_monitor.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""磁盘空间监控脚本"""

import os
import shutil
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("disk_space_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('disk_space_monitor')

# 监控配置
THRESHOLD_WARNING = 80  # 警告阈值（%）
THRESHOLD_CRITICAL = 90  # 临界阈值（%）
MONITORED_PATHS = [
    os.path.dirname(os.path.abspath(__file__)),  # 当前目录
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'),  # 上传目录
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'),  # 数据目录
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs'),  # 日志目录
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')  # 备份目录
]

def check_disk_space(path):
    """检查磁盘空间"""
    try:
        # 获取磁盘信息
        disk_usage = shutil.disk_usage(path)
        total = disk_usage.total
        used = disk_usage.used
        free = disk_usage.free
        
        # 计算使用率
        percent_used = (used / total) * 100
        
        return {
            'path': path,
            'total_gb': total / (1024 * 1024 * 1024),
            'used_gb': used / (1024 * 1024 * 1024),
            'free_gb': free / (1024 * 1024 * 1024),
            'percent_used': percent_used
        }
    except Exception as e:
        logger.error(f"检查路径 {path} 的磁盘空间失败: {str(e)}")
        return None

def send_alert(alert_level, disk_info):
    """发送磁盘空间告警"""
    try:
        # 这里可以配置邮件告警、短信告警等
        logger.warning(
            f"磁盘空间告警 ({alert_level}): 路径={disk_info['path']}, "
            f"使用率={disk_info['percent_used']:.1f}%, "
            f"已用={disk_info['used_gb']:.2f}GB, "
            f"可用={disk_info['free_gb']:.2f}GB"
        )
        
        # 示例：发送邮件告警（需要配置SMTP）
        # send_email_alert(alert_level, disk_info)
        
    except Exception as e:
        logger.error(f"发送告警失败: {str(e)}")

def send_email_alert(alert_level, disk_info):
    """发送邮件告警"""
    # 邮件配置（需要根据实际情况修改）
    smtp_server = "smtp.example.com"
    smtp_port = 587
    smtp_username = "alert@example.com"
    smtp_password = "your_password"
    recipient = "admin@example.com"
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = recipient
    msg['Subject'] = f"[磁盘空间告警-{alert_level}] 路径 {disk_info['path']} 空间不足"
    
    # 邮件正文
    body = f"""磁盘空间告警 ({alert_level})

告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
监控路径: {disk_info['path']}
总容量: {disk_info['total_gb']:.2f} GB
已用空间: {disk_info['used_gb']:.2f} GB
可用空间: {disk_info['free_gb']:.2f} GB
使用率: {disk_info['percent_used']:.1f}%

请及时清理磁盘空间或扩容。"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    # 发送邮件
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)

def cleanup_uploads(upload_dir, max_age_hours=24):
    """清理过期上传文件"""
    try:
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        removed_count = 0
        removed_size = 0
        
        if not os.path.exists(upload_dir):
            return removed_count, removed_size
        
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    removed_count += 1
                    removed_size += file_size
        
        return removed_count, removed_size / (1024 * 1024)  # 返回MB
    except Exception as e:
        logger.error(f"清理上传目录失败: {str(e)}")
        return 0, 0

if __name__ == "__main__":
    logger.info("开始磁盘空间监控...")
    
    # 检查每个路径的磁盘空间
    for path in MONITORED_PATHS:
        if os.path.exists(path):
            disk_info = check_disk_space(path)
            if disk_info:
                # 记录磁盘使用情况
                logger.info(
                    f"磁盘空间监控: 路径={disk_info['path']}, "
                    f"使用率={disk_info['percent_used']:.1f}%, "
                    f"已用={disk_info['used_gb']:.2f}GB, "
                    f"可用={disk_info['free_gb']:.2f}GB"
                )
                
                # 发送告警
                if disk_info['percent_used'] >= THRESHOLD_CRITICAL:
                    send_alert("CRITICAL", disk_info)
                elif disk_info['percent_used'] >= THRESHOLD_WARNING:
                    send_alert("WARNING", disk_info)
    
    # 清理上传目录
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if os.path.exists(upload_dir):
        count, size = cleanup_uploads(upload_dir)
        if count > 0:
            logger.info(f"已清理 {count} 个过期上传文件，释放 {size:.2f} MB 空间")
    
    logger.info("磁盘空间监控完成")
```

### 2. 数据完整性检查

创建 `data_integrity_check.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据完整性检查脚本"""

import os
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_integrity_check.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('data_integrity')

# 检查配置
CHECK_FILES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'model_mappings.json')
]

def check_json_file(file_path):
    """检查JSON文件完整性"""
    try:
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return False
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error(f"文件为空: {file_path}")
            return False
        
        # 尝试解析JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据结构
        if not isinstance(data, dict):
            logger.error(f"JSON不是有效的字典: {file_path}")
            return False
        
        logger.info(f"文件检查通过: {file_path}, 大小: {file_size} 字节, 包含 {len(data)} 条记录")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON格式错误 ({file_path}): {str(e)}")
        return False
    except Exception as e:
        logger.error(f"检查文件 {file_path} 失败: {str(e)}")
        return False

def create_file_backup(file_path):
    """创建文件备份"""
    try:
        if not os.path.exists(file_path):
            return None
        
        backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"已创建备份: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"创建备份失败 ({file_path}): {str(e)}")
        return None

def repair_json_file(file_path, default_data=None):
    """尝试修复损坏的JSON文件"""
    try:
        # 创建备份
        backup_path = create_file_backup(file_path)
        
        # 写入默认数据
        if default_data is None:
            default_data = {
                "466": "A732正极片",
                "505": "A730负极片",
                "467": "A730正极片",
                "Y46": "D640负极片",
                "A47": "D652正极片",
                "A44": "D640正极片",
                "Y49": "D652正极片",
                "477": "A732负极片"
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已修复文件: {file_path}, 使用默认数据")
        return True
        
    except Exception as e:
        logger.error(f"修复文件失败 ({file_path}): {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始数据完整性检查...")
    
    success_count = 0
    repair_count = 0
    
    for file_path in CHECK_FILES:
        logger.info(f"检查文件: {file_path}")
        
        # 检查文件完整性
        if not check_json_file(file_path):
            # 尝试修复
            if repair_json_file(file_path):
                repair_count += 1
                # 再次检查修复结果
                if check_json_file(file_path):
                    success_count += 1
        else:
            success_count += 1
    
    logger.info(f"数据完整性检查完成: 成功 {success_count}/{len(CHECK_FILES)}, 修复 {repair_count} 个文件")
```

## 六、配置部署指南

### 1. 环境变量配置

在生产环境中，建议使用环境变量配置数据库和应用设置：

```bash
# 基本配置
export SECRET_KEY="your_secret_key_here"
export FLASK_ENV="production"
export FLASK_APP="main.py"

# 数据库配置 (如果迁移到数据库)
export DATABASE_URL="postgresql://username:password@localhost:5432/excel_upload"

# 文件路径配置
export APP_BASE_DIR="/opt/excel_upload_system"
export APP_UPLOAD_FOLDER="/opt/excel_upload_system/uploads"
export APP_DATA_FOLDER="/opt/excel_upload_system/data"
export APP_LOG_FOLDER="/opt/excel_upload_system/logs"

# 上传限制配置
export MAX_CONTENT_LENGTH="52428800"  # 50MB in bytes
```

### 2. 腾讯云服务器数据存储优化

在腾讯云服务器上，建议：

1. **使用云硬盘**：选择高性能SSD云硬盘存储应用数据
2. **定期备份到COS**：配置自动将备份文件上传到腾讯云对象存储(COS)
3. **启用云监控**：使用腾讯云监控监控磁盘空间和文件系统性能

创建 `cos_backup.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""备份上传到腾讯云COS脚本"""

import os
import time
import logging
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cos_backup')

# COS配置（需要根据实际情况修改）
# 请在腾讯云控制台获取以下信息
SECRET_ID = os.environ.get('COS_SECRET_ID', '')  # 腾讯云账号SecretId
SECRET_KEY = os.environ.get('COS_SECRET_KEY', '')  # 腾讯云账号SecretKey
REGION = os.environ.get('COS_REGION', 'ap-guangzhou')  # 存储桶所在地域
BUCKET = os.environ.get('COS_BUCKET', '')  # 存储桶名称

# 本地备份目录
BACKUP_DIR = os.environ.get('APP_BACKUP_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups'))

def upload_to_cos(local_file, cos_path):
    """上传文件到COS"""
    try:
        # 配置COS客户端
        config = CosConfig(Region=REGION, SecretId=SECRET_ID, SecretKey=SECRET_KEY)
        client = CosS3Client(config)
        
        # 上传文件
        response = client.upload_file(
            Bucket=BUCKET,
            LocalFilePath=local_file,
            Key=cos_path,
            PartSize=10,
            MAXThread=10
        )
        
        logger.info(f"上传成功: {local_file} -> {cos_path}")
        return True
        
    except Exception as e:
        logger.error(f"上传失败 ({local_file}): {str(e)}")
        return False

def get_latest_backup():
    """获取最新的备份文件"""
    try:
        if not os.path.exists(BACKUP_DIR):
            logger.error(f"备份目录不存在: {BACKUP_DIR}")
            return None
        
        # 获取所有备份文件
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.tar.gz')]
        if not backups:
            logger.error(f"没有找到备份文件: {BACKUP_DIR}")
            return None
        
        # 按修改时间排序，返回最新的
        backup_files = [(os.path.join(BACKUP_DIR, f), os.path.getmtime(os.path.join(BACKUP_DIR, f))) 
                       for f in backups]
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        latest_file = backup_files[0][0]
        logger.info(f"找到最新备份: {latest_file}")
        return latest_file
        
    except Exception as e:
        logger.error(f"获取最新备份失败: {str(e)}")
        return None

def main():
    """主函数"""
    # 验证配置
    if not all([SECRET_ID, SECRET_KEY, REGION, BUCKET]):
        logger.error("COS配置不完整，请设置环境变量: COS_SECRET_ID, COS_SECRET_KEY, COS_REGION, COS_BUCKET")
        sys.exit(1)
    
    # 获取最新备份
    latest_backup = get_latest_backup()
    if not latest_backup:
        sys.exit(1)
    
    # 构建COS路径
    filename = os.path.basename(latest_backup)
    cos_path = f"excel_upload_backups/{filename}"
    
    # 上传到COS
    if upload_to_cos(latest_backup, cos_path):
        logger.info("备份上传完成")
    else:
        logger.error("备份上传失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

通过以上配置和脚本，可以确保Excel上传分析系统的数据存储安全可靠，并为未来可能的数据库迁移提供了清晰的路径。