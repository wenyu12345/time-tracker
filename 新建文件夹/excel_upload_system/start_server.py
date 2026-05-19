#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接启动Excel上传系统服务器
不依赖任何特殊环境
"""

import os
import sys
import webbrowser
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # 设置matplotlib不使用GUI后端
    import matplotlib
    matplotlib.use('Agg')
    
    # 导入应用
    from app import app
    
    # 确保必要的目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 打印启动信息
    print("=" * 60)
    print("Excel上传系统服务器")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"版本: 2.0.0")
    print(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    print("=" * 60)
    print("服务器正在启动...")
    print(f"请访问: http://localhost:2006")

    print(f"分类汇总表格: http://localhost:2006/summary_table")
    print("=" * 60)
    print("按Ctrl+C停止服务器")
    
    # 启动应用
    app.run(host='0.0.0.0', port=2006, debug=True)
    
except Exception as e:
    print(f"启动服务器失败: {str(e)}")
    import traceback
    traceback.print_exc()
    input("按任意键退出...")