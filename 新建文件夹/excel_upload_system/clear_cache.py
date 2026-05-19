import os
import shutil
from datetime import datetime

def clear_server_cache():
    """清理服务器缓存和上传文件"""
    
    # 清理上传文件目录
    upload_dir = 'data/uploads'
    if os.path.exists(upload_dir):
        files = os.listdir(upload_dir)
        print(f'找到 {len(files)} 个文件在上传目录')
        
        # 创建备份目录
        backup_dir = f'data/uploads_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(backup_dir, exist_ok=True)
        
        # 备份并清理文件
        for file in files:
            src = os.path.join(upload_dir, file)
            dst = os.path.join(backup_dir, file)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                os.remove(src)
                print(f'已备份并删除: {file}')
        
        print(f'所有上传文件已备份到: {backup_dir}')
    else:
        print('上传目录不存在')
    
    # 清理session缓存（如果存在）
    session_dir = 'data/sessions'
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
        os.makedirs(session_dir)
        print('Session缓存已清空')
    
    print('服务器缓存清理完成！')

if __name__ == '__main__':
    clear_server_cache()