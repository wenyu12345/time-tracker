import os
import sqlite3
import datetime
import shutil
from pathlib import Path

# 备份目录
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')

# 确保备份目录存在
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_database(db_path):
    """备份数据库到SQL文件"""
    try:
        # 生成备份文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.sql'
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        
        # 执行备份
        with open(backup_path, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        
        conn.close()
        
        return {
            'success': True,
            'filename': backup_filename,
            'path': backup_path,
            'size': os.path.getsize(backup_path),
            'timestamp': timestamp
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def restore_database(db_path, backup_file):
    """从SQL文件恢复数据库"""
    try:
        # 关闭所有可能的数据库连接
        # 这里简化处理，实际应用中可能需要更复杂的处理
        
        # 备份当前数据库作为安全措施
        safety_backup = backup_database(db_path)
        if not safety_backup['success']:
            return {
                'success': False,
                'error': f'安全备份失败: {safety_backup["error"]}'
            }
        
        # 删除当前数据库文件
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # 创建新的数据库文件
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行恢复
        with open(backup_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'safety_backup': safety_backup['filename']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_backup_list():
    """获取备份文件列表"""
    try:
        backups = []
        
        # 遍历备份目录
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('backup_') and filename.endswith('.sql'):
                filepath = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(filepath)
                backups.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created_at': datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'path': filepath
                })
        
        # 按创建时间降序排序
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            'success': True,
            'backups': backups
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def delete_backup(backup_file):
    """删除备份文件"""
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_file)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            return {
                'success': True
            }
        else:
            return {
                'success': False,
                'error': '备份文件不存在'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def auto_backup(db_path, retention_days=7):
    """自动备份并清理旧备份"""
    try:
        # 执行备份
        backup_result = backup_database(db_path)
        if not backup_result['success']:
            return backup_result
        
        # 清理旧备份
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('backup_') and filename.endswith('.sql'):
                filepath = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(filepath)
                file_date = datetime.datetime.fromtimestamp(stat.st_ctime)
                
                if file_date < cutoff_date:
                    os.remove(filepath)
        
        return backup_result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
