import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import subprocess
import threading
import time
import os
import sys

class ServerManager:
    """服务器管理类，负责启动和停止服务器"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.backend_log_callback = None
        self.frontend_log_callback = None
    
    def set_log_callbacks(self, backend_callback, frontend_callback):
        """设置日志回调函数"""
        self.backend_log_callback = backend_callback
        self.frontend_log_callback = frontend_callback
    
    def start_backend(self, port=5000):
        """启动后端Flask服务器"""
        if self.backend_process is not None and self.backend_process.poll() is None:
            self._log_backend("后端服务器已经在运行中\n")
            return False
        
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.join(current_dir, "backend")
            
            # 启动Flask应用
            cmd = [
                sys.executable, "app.py"
            ]
            
            self._log_backend(f"启动后端服务器，端口: {port}\n")
            self._log_backend(f"命令: {' '.join(cmd)}\n")
            self._log_backend(f"工作目录: {backend_dir}\n")
            
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动日志捕获线程
            threading.Thread(
                target=self._capture_log,
                args=(self.backend_process, self._log_backend),
                daemon=True
            ).start()
            
            return True
        except Exception as e:
            self._log_backend(f"启动后端服务器失败: {str(e)}\n")
            return False
    
    def stop_backend(self):
        """停止后端服务器"""
        if self.backend_process is None or self.backend_process.poll() is not None:
            self._log_backend("后端服务器未在运行\n")
            return False
        
        try:
            self._log_backend("停止后端服务器...\n")
            # 尝试优雅终止
            self.backend_process.terminate()
            
            # 等待进程结束
            for _ in range(5):
                if self.backend_process.poll() is not None:
                    break
                time.sleep(0.5)
            else:
                # 强制终止
                self.backend_process.kill()
                self._log_backend("后端服务器已强制终止\n")
            
            self.backend_process = None
            self._log_backend("后端服务器已停止\n")
            return True
        except Exception as e:
            self._log_backend(f"停止后端服务器失败: {str(e)}\n")
            return False
    
    def start_frontend(self, port=8000):
        """启动前端静态服务器"""
        if self.frontend_process is not None and self.frontend_process.poll() is None:
            self._log_frontend("前端服务器已经在运行中\n")
            return False
        
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            frontend_dir = os.path.join(current_dir, "frontend")
            
            # 启动Python内置HTTP服务器
            cmd = [
                sys.executable, "-m", "http.server", str(port)
            ]
            
            self._log_frontend(f"启动前端服务器，端口: {port}\n")
            self._log_frontend(f"命令: {' '.join(cmd)}\n")
            self._log_frontend(f"工作目录: {frontend_dir}\n")
            
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动日志捕获线程
            threading.Thread(
                target=self._capture_log,
                args=(self.frontend_process, self._log_frontend),
                daemon=True
            ).start()
            
            return True
        except Exception as e:
            self._log_frontend(f"启动前端服务器失败: {str(e)}\n")
            return False
    
    def stop_frontend(self):
        """停止前端服务器"""
        if self.frontend_process is None or self.frontend_process.poll() is not None:
            self._log_frontend("前端服务器未在运行\n")
            return False
        
        try:
            self._log_frontend("停止前端服务器...\n")
            # 尝试优雅终止
            self.frontend_process.terminate()
            
            # 等待进程结束
            for _ in range(5):
                if self.frontend_process.poll() is not None:
                    break
                time.sleep(0.5)
            else:
                # 强制终止
                self.frontend_process.kill()
                self._log_frontend("前端服务器已强制终止\n")
            
            self.frontend_process = None
            self._log_frontend("前端服务器已停止\n")
            return True
        except Exception as e:
            self._log_frontend(f"停止前端服务器失败: {str(e)}\n")
            return False
    
    def _capture_log(self, process, log_callback):
        """捕获服务器输出日志"""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log_callback(line)
    
    def _log_backend(self, message):
        """记录后端日志"""
        if self.backend_log_callback:
            self.backend_log_callback(message)
    
    def _log_frontend(self, message):
        """记录前端日志"""
        if self.frontend_log_callback:
            self.frontend_log_callback(message)

class ServerGUI:
    """服务器管理UI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.server_manager = ServerManager()
        self.setup_ui()
        self.server_manager.set_log_callbacks(
            self.update_backend_log,
            self.update_frontend_log
        )
    
    def setup_ui(self):
        """设置UI界面"""
        self.root.title("本地服务器管理")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 服务器配置区域
        config_frame = ttk.LabelFrame(main_frame, text="服务器配置", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 后端配置
        ttk.Label(config_frame, text="后端端口:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.backend_port = ttk.Entry(config_frame, width=10)
        self.backend_port.insert(0, "5000")
        self.backend_port.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 前端配置
        ttk.Label(config_frame, text="前端端口:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10), pady=5)
        self.frontend_port = ttk.Entry(config_frame, width=10)
        self.frontend_port.insert(0, "8000")
        self.frontend_port.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # 后端服务器控制区域
        backend_frame = ttk.LabelFrame(main_frame, text="后端API服务器", padding="10")
        backend_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5), pady=(0, 10))
        backend_frame.columnconfigure(0, weight=1)
        
        # 后端状态
        self.backend_status = ttk.Label(backend_frame, text="状态: 未运行", foreground="red")
        self.backend_status.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # 后端按钮
        backend_btn_frame = ttk.Frame(backend_frame)
        backend_btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        backend_btn_frame.columnconfigure(0, weight=1)
        backend_btn_frame.columnconfigure(1, weight=1)
        
        self.start_backend_btn = ttk.Button(backend_btn_frame, text="启动后端", command=self.start_backend)
        self.start_backend_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.stop_backend_btn = ttk.Button(backend_btn_frame, text="停止后端", command=self.stop_backend, state=tk.DISABLED)
        self.stop_backend_btn.grid(row=0, column=1, sticky=tk.E, padx=(5, 0))
        
        # 前端服务器控制区域
        frontend_frame = ttk.LabelFrame(main_frame, text="前端静态服务器", padding="10")
        frontend_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0), pady=(0, 10))
        frontend_frame.columnconfigure(0, weight=1)
        
        # 前端状态
        self.frontend_status = ttk.Label(frontend_frame, text="状态: 未运行", foreground="red")
        self.frontend_status.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # 前端按钮
        frontend_btn_frame = ttk.Frame(frontend_frame)
        frontend_btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        frontend_btn_frame.columnconfigure(0, weight=1)
        frontend_btn_frame.columnconfigure(1, weight=1)
        
        self.start_frontend_btn = ttk.Button(frontend_btn_frame, text="启动前端", command=self.start_frontend)
        self.start_frontend_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.stop_frontend_btn = ttk.Button(frontend_btn_frame, text="停止前端", command=self.stop_frontend, state=tk.DISABLED)
        self.stop_frontend_btn.grid(row=0, column=1, sticky=tk.E, padx=(5, 0))
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="服务器日志", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        
        # 日志标签
        log_label_frame = ttk.Frame(log_frame)
        log_label_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(log_label_frame, text="后端日志: ").grid(row=0, column=0, sticky=tk.W)
        self.backend_log_tab = ttk.Button(log_label_frame, text="后端", command=lambda: self.show_backend_log(), style="LogTab.TButton")
        self.backend_log_tab.grid(row=0, column=1, padx=(5, 5))
        
        ttk.Label(log_label_frame, text="前端日志: ").grid(row=0, column=2, sticky=tk.W)
        self.frontend_log_tab = ttk.Button(log_label_frame, text="前端", command=lambda: self.show_frontend_log(), style="LogTab.TButton")
        self.frontend_log_tab.grid(row=0, column=3, padx=(5, 5))
        
        ttk.Label(log_label_frame, text="全部日志: ").grid(row=0, column=4, sticky=tk.W)
        self.all_log_tab = ttk.Button(log_label_frame, text="全部", command=lambda: self.show_all_log(), style="LogTab.TButton")
        self.all_log_tab.grid(row=0, column=5, padx=(5, 5))
        
        # 清空日志按钮
        self.clear_log_btn = ttk.Button(log_label_frame, text="清空日志", command=self.clear_log)
        self.clear_log_btn.grid(row=0, column=6, sticky=tk.E)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志类型
        self.current_log_view = "all"  # all, backend, frontend
        
        # 日志存储
        self.backend_log = []
        self.frontend_log = []
        
        # 设置样式
        style = ttk.Style()
        style.configure("LogTab.TButton", padding=(10, 2))
        
        # 定时检查服务器状态
        self.check_server_status()
    
    def start_backend(self):
        """启动后端服务器"""
        port = int(self.backend_port.get())
        if self.server_manager.start_backend(port):
            self.backend_status.config(text="状态: 运行中", foreground="green")
            self.start_backend_btn.config(state=tk.DISABLED)
            self.stop_backend_btn.config(state=tk.NORMAL)
    
    def stop_backend(self):
        """停止后端服务器"""
        if self.server_manager.stop_backend():
            self.backend_status.config(text="状态: 未运行", foreground="red")
            self.start_backend_btn.config(state=tk.NORMAL)
            self.stop_backend_btn.config(state=tk.DISABLED)
    
    def start_frontend(self):
        """启动前端服务器"""
        port = int(self.frontend_port.get())
        if self.server_manager.start_frontend(port):
            self.frontend_status.config(text="状态: 运行中", foreground="green")
            self.start_frontend_btn.config(state=tk.DISABLED)
            self.stop_frontend_btn.config(state=tk.NORMAL)
    
    def stop_frontend(self):
        """停止前端服务器"""
        if self.server_manager.stop_frontend():
            self.frontend_status.config(text="状态: 未运行", foreground="red")
            self.start_frontend_btn.config(state=tk.NORMAL)
            self.stop_frontend_btn.config(state=tk.DISABLED)
    
    def update_backend_log(self, message):
        """更新后端日志"""
        self.backend_log.append(message)
        if self.current_log_view in ["all", "backend"]:
            self.log_text.insert(tk.END, f"[后端] {message}")
            self.log_text.see(tk.END)
    
    def update_frontend_log(self, message):
        """更新前端日志"""
        self.frontend_log.append(message)
        if self.current_log_view in ["all", "frontend"]:
            self.log_text.insert(tk.END, f"[前端] {message}")
            self.log_text.see(tk.END)
    
    def show_backend_log(self):
        """显示后端日志"""
        self.current_log_view = "backend"
        self.update_log_display()
    
    def show_frontend_log(self):
        """显示前端日志"""
        self.current_log_view = "frontend"
        self.update_log_display()
    
    def show_all_log(self):
        """显示全部日志"""
        self.current_log_view = "all"
        self.update_log_display()
    
    def update_log_display(self):
        """更新日志显示"""
        self.log_text.delete(1.0, tk.END)
        
        if self.current_log_view == "backend":
            for message in self.backend_log:
                self.log_text.insert(tk.END, f"[后端] {message}")
        elif self.current_log_view == "frontend":
            for message in self.frontend_log:
                self.log_text.insert(tk.END, f"[前端] {message}")
        else:  # all
            # 合并日志，按时间顺序显示
            combined_log = []
            for message in self.backend_log:
                combined_log.append(("backend", message))
            for message in self.frontend_log:
                combined_log.append(("frontend", message))
            
            # 这里简化处理，实际应该按时间排序
            for log_type, message in combined_log:
                self.log_text.insert(tk.END, f"[{log_type}] {message}")
        
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """清空日志"""
        self.backend_log = []
        self.frontend_log = []
        self.log_text.delete(1.0, tk.END)
    
    def check_server_status(self):
        """定时检查服务器状态"""
        # 这里可以添加服务器状态检查逻辑
        # 目前通过按钮状态间接反映
        self.root.after(1000, self.check_server_status)
    
    def run(self):
        """运行UI"""
        self.root.mainloop()

if __name__ == "__main__":
    gui = ServerGUI()
    gui.run()
