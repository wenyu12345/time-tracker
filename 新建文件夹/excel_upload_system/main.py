from app import app
import os

# 系统版本信息
VERSION = "4.0.0"
VERSION_DATE = "2026-05-16"

if __name__ == '__main__':
    # 设置matplotlib不使用GUI后端
    import matplotlib
    matplotlib.use('Agg')
    
    # 确保必要的目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 启动应用 - 开启debug模式支持热加载
    app.run(host='0.0.0.0', port=2006, debug=True)
