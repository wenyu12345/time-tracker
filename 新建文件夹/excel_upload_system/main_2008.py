from app import app
import os

# 系统版本信息
VERSION = "2.0.0"
VERSION_DATE = "2025-11-05"

if __name__ == '__main__':
    # 设置matplotlib不使用GUI后端
    import matplotlib
    matplotlib.use('Agg')
    
    # 确保必要的目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 启动应用 - 端口2008
    app.run(host='0.0.0.0', port=2008, debug=True)