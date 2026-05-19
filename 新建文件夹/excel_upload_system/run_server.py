#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel上传系统启动器
用于在中文路径环境下正确启动服务器
"""

import os
import sys
import subprocess

def main():
    # 找到Python解释器
    python_exe = r"C:\Users\19394\miniconda3\python.exe"
    
    # 确保Python存在
    if not os.path.exists(python_exe):
        print(f"错误：找不到Python解释器：{python_exe}")
        input("按回车键退出...")
        return
    
    # 设置环境变量，确保使用正确的Python环境
    env = os.environ.copy()
    env['PYTHONHOME'] = r"C:\Users\19394\miniconda3"
    env['PYTHONPATH'] = r"C:\Users\19394\miniconda3\Lib"
    env['FLASK_APP'] = 'main.py'
    env['FLASK_ENV'] = 'development'
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 切换到项目目录
    os.chdir(script_dir)
    
    print("=" * 60)
    print("Excel上传分析系统")
    print("=" * 60)
    print(f"Python路径: {python_exe}")
    print(f"工作目录: {script_dir}")
    print("=" * 60)
    print("正在启动服务器...")
    print("访问地址: http://localhost:5002")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    # 启动Flask服务器
    try:
        # 使用subprocess启动，保持环境变量
        process = subprocess.Popen(
            [python_exe, "-m", "flask", "run", "--host=0.0.0.0", "--port=5002"],
            env=env,
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1
        )
        
        # 实时输出
        for line in process.stdout:
            try:
                print(line.decode('utf-8', errors='ignore').rstrip())
            except:
                pass
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        process.terminate()
        process.wait()
        print("服务器已停止")
        
    except Exception as e:
        print(f"启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

if __name__ == "__main__":
    main()
