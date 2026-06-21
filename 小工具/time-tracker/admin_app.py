import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# API基础URL
BASE_URL = 'http://127.0.0.1:5000/api/admin'

# 保存登录状态
LOGIN_FILE = 'admin_login.json'

class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title('考勤管理系统')
        self.root.geometry('800x600')
        self.root.resizable(True, True)
        
        # 设置主题
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 登录状态
        self.logged_in = False
        self.admin_info = None
        self.token = None
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 检查登录状态
        self.check_login_status()
        
    def check_login_status(self):
        """检查登录状态"""
        if os.path.exists(LOGIN_FILE):
            try:
                with open(LOGIN_FILE, 'r') as f:
                    login_data = json.load(f)
                    self.token = login_data.get('token')
                    self.admin_info = login_data.get('admin')
                    self.logged_in = True
                    self.show_main_window()
            except:
                self.show_login_window()
        else:
            self.show_login_window()
    
    def show_login_window(self):
        """显示登录窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 登录框架
        login_frame = ttk.Frame(self.main_frame)
        login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(login_frame, text='考勤管理系统', font=('Arial', 24))
        title_label.pack(pady=20)
        
        # 登录表单
        form_frame = ttk.Frame(login_frame)
        form_frame.pack(pady=20)
        
        # 用户名
        ttk.Label(form_frame, text='用户名:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.username_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 密码
        ttk.Label(form_frame, text='密码:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.password_var, show='*', width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 登录按钮
        login_btn = ttk.Button(form_frame, text='登录', command=self.login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # 注册按钮（仅首次使用）
        register_btn = ttk.Button(form_frame, text='注册管理员', command=self.show_register_window)
        register_btn.grid(row=3, column=0, columnspan=2, pady=10)
    
    def show_register_window(self):
        """显示注册窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 注册框架
        register_frame = ttk.Frame(self.main_frame)
        register_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(register_frame, text='注册管理员', font=('Arial', 24))
        title_label.pack(pady=20)
        
        # 注册表单
        form_frame = ttk.Frame(register_frame)
        form_frame.pack(pady=20)
        
        # 用户名
        ttk.Label(form_frame, text='用户名:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.reg_username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.reg_username_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 密码
        ttk.Label(form_frame, text='密码:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.reg_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.reg_password_var, show='*', width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 确认密码
        ttk.Label(form_frame, text='确认密码:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.reg_confirm_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.reg_confirm_var, show='*', width=30).grid(row=2, column=1, padx=10, pady=10)
        
        # 注册按钮
        register_btn = ttk.Button(form_frame, text='注册', command=self.register)
        register_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        # 返回登录按钮
        back_btn = ttk.Button(form_frame, text='返回登录', command=self.show_login_window)
        back_btn.grid(row=4, column=0, columnspan=2, pady=10)
    
    def login(self):
        """登录"""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror('错误', '用户名和密码不能为空')
            return
        
        try:
            response = requests.post(f'{BASE_URL}/login', json={
                'username': username,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.admin_info = data.get('admin')
                self.logged_in = True
                
                # 保存登录状态
                with open(LOGIN_FILE, 'w') as f:
                    json.dump({
                        'token': self.token,
                        'admin': self.admin_info
                    }, f)
                
                self.show_main_window()
            else:
                messagebox.showerror('错误', response.json().get('error', '登录失败'))
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def register(self):
        """注册"""
        username = self.reg_username_var.get()
        password = self.reg_password_var.get()
        confirm_password = self.reg_confirm_var.get()
        
        if not username or not password:
            messagebox.showerror('错误', '用户名和密码不能为空')
            return
        
        if password != confirm_password:
            messagebox.showerror('错误', '两次输入的密码不一致')
            return
        
        try:
            response = requests.post(f'{BASE_URL}/register', json={
                'username': username,
                'password': password
            })
            
            if response.status_code == 201:
                messagebox.showinfo('成功', '注册成功，请登录')
                self.show_login_window()
            else:
                messagebox.showerror('错误', response.json().get('error', '注册失败'))
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def get_today_stats(self):
        """获取当天统计数据"""
        try:
            response = requests.get(f'{BASE_URL}/stats/today')
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except:
            return None
    
    def manual_add_time_records(self):
        """手动将排班写入工时和班别"""
        if messagebox.askyesno('确认', '确定要手动将排班写入工时和班别吗？'):
            try:
                response = requests.post(f'{BASE_URL}/schedules/manual-add-time-records')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '手动添加工时记录成功')
                    # 刷新页面数据
                    self.show_main_window()
                else:
                    messagebox.showerror('错误', response.json().get('error', '手动添加工时记录失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def manual_send_attendance_to_message_wall(self):
        """手动发送考勤记录到留言墙"""
        if messagebox.askyesno('确认', '确定要手动发送考勤记录到留言墙吗？'):
            try:
                response = requests.post('http://localhost:5000/api/messages/test-system-message')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '考勤记录已成功发送到留言墙')
                else:
                    messagebox.showerror('错误', f'发送考勤记录失败: {response.text}')
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def show_scheduler_report(self):
        """显示定时任务执行报表"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='定时任务执行报表', font=('Arial', 24)).pack(side=tk.LEFT)
        
        try:
            # 获取定时任务统计数据
            stats_response = requests.get('http://localhost:5000/api/scheduler/stats')
            if stats_response.status_code != 200:
                raise Exception('获取统计数据失败')
            
            stats_data = stats_response.json()
            
            # 获取定时任务日志
            logs_response = requests.get('http://localhost:5000/api/scheduler/logs')
            if logs_response.status_code != 200:
                raise Exception('获取日志数据失败')
            
            logs_data = logs_response.json()
            
            # 统计信息框架
            stats_frame = ttk.Frame(self.main_frame)
            stats_frame.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Label(stats_frame, text='统计信息', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
            
            # 总体统计卡片
            total_stats = stats_data.get('total_stats', {})
            total_cards_frame = ttk.Frame(stats_frame)
            total_cards_frame.pack(fill=tk.X, pady=10)
            
            ttk.LabelFrame(total_cards_frame, text='总体统计').grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(total_cards_frame, text=f"总任务数: {total_stats.get('total_jobs', 0)}").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
            ttk.Label(total_cards_frame, text=f"成功数: {total_stats.get('success_count', 0)}").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
            ttk.Label(total_cards_frame, text=f"失败数: {total_stats.get('failed_count', 0)}").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
            ttk.Label(total_cards_frame, text=f"平均执行时间: {total_stats.get('avg_execution_time', 0):.2f} 秒").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
            
            # 按任务类型统计
            job_stats = stats_data.get('job_stats', [])
            if job_stats:
                job_stats_frame = ttk.Frame(stats_frame)
                job_stats_frame.pack(fill=tk.X, pady=10)
                
                ttk.Label(job_stats_frame, text='按任务类型统计', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
                
                # 表格
                columns = ('job_name', 'total_jobs', 'success_count', 'failed_count', 'avg_execution_time')
                job_tree = ttk.Treeview(job_stats_frame, columns=columns, show='headings')
                
                # 设置列标题
                job_tree.heading('job_name', text='任务名称')
                job_tree.heading('total_jobs', text='总执行次数')
                job_tree.heading('success_count', text='成功次数')
                job_tree.heading('failed_count', text='失败次数')
                job_tree.heading('avg_execution_time', text='平均执行时间(秒)')
                
                # 设置列宽
                job_tree.column('job_name', width=200, anchor=tk.CENTER)
                job_tree.column('total_jobs', width=120, anchor=tk.CENTER)
                job_tree.column('success_count', width=120, anchor=tk.CENTER)
                job_tree.column('failed_count', width=120, anchor=tk.CENTER)
                job_tree.column('avg_execution_time', width=150, anchor=tk.CENTER)
                
                # 添加数据
                for job in job_stats:
                    job_tree.insert('', tk.END, values=(
                        job['job_name'],
                        job['total_jobs'],
                        job['success_count'],
                        job['failed_count'],
                        f"{job['avg_execution_time']:.2f}"
                    ))
                
                # 添加滚动条
                scrollbar = ttk.Scrollbar(job_stats_frame, orient=tk.VERTICAL, command=job_tree.yview)
                job_tree.configure(yscroll=scrollbar.set)
                
                # 布局
                job_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 最近7天统计
            recent_stats = stats_data.get('recent_stats', [])
            if recent_stats:
                recent_frame = ttk.Frame(stats_frame)
                recent_frame.pack(fill=tk.X, pady=10)
                
                ttk.Label(recent_frame, text='最近7天执行情况', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
                
                # 表格
                columns = ('date', 'total_jobs', 'success_count', 'failed_count')
                recent_tree = ttk.Treeview(recent_frame, columns=columns, show='headings')
                
                # 设置列标题
                recent_tree.heading('date', text='日期')
                recent_tree.heading('total_jobs', text='总执行次数')
                recent_tree.heading('success_count', text='成功次数')
                recent_tree.heading('failed_count', text='失败次数')
                
                # 设置列宽
                recent_tree.column('date', width=150, anchor=tk.CENTER)
                recent_tree.column('total_jobs', width=120, anchor=tk.CENTER)
                recent_tree.column('success_count', width=120, anchor=tk.CENTER)
                recent_tree.column('failed_count', width=120, anchor=tk.CENTER)
                
                # 添加数据
                for day in recent_stats:
                    recent_tree.insert('', tk.END, values=(
                        day['date'],
                        day['total_jobs'],
                        day['success_count'],
                        day['failed_count']
                    ))
                
                # 添加滚动条
                scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=recent_tree.yview)
                recent_tree.configure(yscroll=scrollbar.set)
                
                # 布局
                recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 日志列表
            logs_frame = ttk.Frame(self.main_frame)
            logs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            ttk.Label(logs_frame, text='最近执行日志', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
            
            logs = logs_data.get('logs', [])
            
            # 表格
            columns = ('id', 'job_name', 'status', 'start_time', 'execution_time', 'message')
            logs_tree = ttk.Treeview(logs_frame, columns=columns, show='headings')
            
            # 设置列标题
            logs_tree.heading('id', text='ID')
            logs_tree.heading('job_name', text='任务名称')
            logs_tree.heading('status', text='状态')
            logs_tree.heading('start_time', text='执行时间')
            logs_tree.heading('execution_time', text='执行时长(秒)')
            logs_tree.heading('message', text='消息')
            
            # 设置列宽
            logs_tree.column('id', width=80, anchor=tk.CENTER)
            logs_tree.column('job_name', width=150, anchor=tk.CENTER)
            logs_tree.column('status', width=100, anchor=tk.CENTER)
            logs_tree.column('start_time', width=180, anchor=tk.CENTER)
            logs_tree.column('execution_time', width=120, anchor=tk.CENTER)
            logs_tree.column('message', width=400, anchor=tk.W)
            
            # 添加数据
            for log in logs:
                logs_tree.insert('', tk.END, values=(
                    log['id'],
                    log['job_name'],
                    log['status'],
                    log['start_time'],
                    f"{log['execution_time']:.2f}",
                    log['message']
                ))
            
            # 添加滚动条
            scrollbar_y = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=logs_tree.yview)
            scrollbar_x = ttk.Scrollbar(logs_frame, orient=tk.HORIZONTAL, command=logs_tree.xview)
            logs_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
            
            # 布局
            logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            ttk.Label(self.main_frame, text=f'获取报表数据失败: {str(e)}', font=('Arial', 12), foreground='red').pack(anchor=tk.W, padx=20, pady=10)
    
    def show_login_report(self):
        """显示用户登录报表"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='用户登录报表', font=('Arial', 24)).pack(side=tk.LEFT)
        
        try:
            # 获取登录日志统计数据
            stats_response = requests.get('http://localhost:5000/api/admin/user-login-logs/stats')
            if stats_response.status_code != 200:
                raise Exception('获取登录统计数据失败')
            
            stats_data = stats_response.json()
            
            # 获取登录日志列表
            logs_response = requests.get('http://localhost:5000/api/admin/user-login-logs')
            if logs_response.status_code != 200:
                raise Exception('获取登录日志数据失败')
            
            logs_data = logs_response.json()
            
            # 统计信息框架
            stats_frame = ttk.Frame(self.main_frame)
            stats_frame.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Label(stats_frame, text='统计信息', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
            
            # 总体统计卡片
            total_cards_frame = ttk.Frame(stats_frame)
            total_cards_frame.pack(fill=tk.X, pady=10)
            
            ttk.LabelFrame(total_cards_frame, text='总体统计').grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(total_cards_frame, text=f"总登录次数: {stats_data.get('total_logins', 0)}").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
            ttk.Label(total_cards_frame, text=f"登录用户数: {stats_data.get('unique_users', 0)}").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
            ttk.Label(total_cards_frame, text=f"登录IP数: {stats_data.get('unique_ips', 0)}").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
            
            # 登录日志列表
            logs_frame = ttk.Frame(self.main_frame)
            logs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            ttk.Label(logs_frame, text='登录日志列表', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
            
            logs = logs_data.get('logs', [])
            
            # 表格
            columns = ('id', 'user_id', 'username', 'ip_address', 'login_time')
            logs_tree = ttk.Treeview(logs_frame, columns=columns, show='headings')
            
            # 设置列标题
            logs_tree.heading('id', text='ID')
            logs_tree.heading('user_id', text='用户ID')
            logs_tree.heading('username', text='用户名')
            logs_tree.heading('ip_address', text='登录IP')
            logs_tree.heading('login_time', text='登录时间')
            
            # 设置列宽
            logs_tree.column('id', width=80, anchor=tk.CENTER)
            logs_tree.column('user_id', width=100, anchor=tk.CENTER)
            logs_tree.column('username', width=150, anchor=tk.CENTER)
            logs_tree.column('ip_address', width=150, anchor=tk.CENTER)
            logs_tree.column('login_time', width=180, anchor=tk.CENTER)
            
            # 添加数据
            for log in logs:
                logs_tree.insert('', tk.END, values=(
                    log['id'],
                    log['user_id'],
                    log['username'],
                    log['ip_address'],
                    log['login_time']
                ))
            
            # 添加滚动条
            scrollbar_y = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=logs_tree.yview)
            scrollbar_x = ttk.Scrollbar(logs_frame, orient=tk.HORIZONTAL, command=logs_tree.xview)
            logs_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
            
            # 布局
            logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            ttk.Label(self.main_frame, text=f'获取登录报表数据失败: {str(e)}', font=('Arial', 12), foreground='red').pack(anchor=tk.W, padx=20, pady=10)
    
    def show_online_users_report(self):
        """显示在线用户报表"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='在线用户报表', font=('Arial', 24)).pack(side=tk.LEFT)
        
        try:
            from datetime import datetime
            # 获取今天的日期
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 获取今天的在线用户记录
            logs_response = requests.get(f'http://localhost:5000/api/admin/user-online-logs/today')
            if logs_response.status_code != 200:
                raise Exception('获取在线用户数据失败')
            
            logs_data = logs_response.json()
            
            # 统计信息框架
            stats_frame = ttk.Frame(self.main_frame)
            stats_frame.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Label(stats_frame, text='统计信息', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
            
            # 总体统计卡片
            total_cards_frame = ttk.Frame(stats_frame)
            total_cards_frame.pack(fill=tk.X, pady=10)
            
            ttk.LabelFrame(total_cards_frame, text='总体统计').grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(total_cards_frame, text=f"统计日期: {today}").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
            ttk.Label(total_cards_frame, text=f"在线用户数: {len(logs_data)}").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
            
            # 在线用户列表
            logs_frame = ttk.Frame(self.main_frame)
            logs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            ttk.Label(logs_frame, text='今天在线用户列表', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
            
            # 表格
            columns = ('id', 'user_id', 'username', 'ip_address', 'visit_date', 'last_visit_time', 'visit_count')
            logs_tree = ttk.Treeview(logs_frame, columns=columns, show='headings')
            
            # 设置列标题
            logs_tree.heading('id', text='ID')
            logs_tree.heading('user_id', text='用户ID')
            logs_tree.heading('username', text='用户名')
            logs_tree.heading('ip_address', text='访问IP')
            logs_tree.heading('visit_date', text='访问日期')
            logs_tree.heading('last_visit_time', text='最后访问时间')
            logs_tree.heading('visit_count', text='访问次数')
            
            # 设置列宽
            logs_tree.column('id', width=80, anchor=tk.CENTER)
            logs_tree.column('user_id', width=100, anchor=tk.CENTER)
            logs_tree.column('username', width=150, anchor=tk.CENTER)
            logs_tree.column('ip_address', width=150, anchor=tk.CENTER)
            logs_tree.column('visit_date', width=120, anchor=tk.CENTER)
            logs_tree.column('last_visit_time', width=180, anchor=tk.CENTER)
            logs_tree.column('visit_count', width=100, anchor=tk.CENTER)
            
            # 添加数据
            for log in logs_data:
                logs_tree.insert('', tk.END, values=(
                    log['id'],
                    log['user_id'],
                    log['username'],
                    log['ip_address'],
                    log['visit_date'],
                    log['last_visit_time'],
                    log['visit_count']
                ))
            
            # 添加滚动条
            scrollbar_y = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=logs_tree.yview)
            scrollbar_x = ttk.Scrollbar(logs_frame, orient=tk.HORIZONTAL, command=logs_tree.xview)
            logs_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
            
            # 布局
            logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            ttk.Label(self.main_frame, text=f'获取报表数据失败: {str(e)}', font=('Arial', 12), foreground='red').pack(anchor=tk.W, padx=20, pady=10)
    
    def check_duplicate_time_records(self):
        """检查并处理重复的工时记录"""
        try:
            # 查询重复的工时记录
            response = requests.get(f'{BASE_URL}/time-records/duplicates')
            if response.status_code == 200:
                duplicates = response.json()
                
                if not duplicates:
                    messagebox.showinfo('提示', '没有发现重复的工时记录')
                    return
                
                total_duplicates = len(duplicates)
                messagebox.showinfo('提示', f'发现 {total_duplicates} 条重复的工时记录，将逐个处理')
                
                for duplicate in duplicates:
                    user_id = duplicate['user_id']
                    username = duplicate['username']
                    record_date = duplicate['record_date']
                    records = duplicate['records']
                    
                    # 创建一个对话框，让管理员选择保留哪条记录
                    self.show_duplicate_dialog(user_id, username, record_date, records)
                
                # 处理完成后刷新页面
                self.show_main_window()
            else:
                messagebox.showerror('错误', response.json().get('error', '查询重复工时记录失败'))
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def show_duplicate_dialog(self, user_id, username, record_date, records):
        """显示重复记录对话框，让管理员选择保留哪条记录"""
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f'处理重复工时记录 - {username} - {record_date}')
        dialog.geometry('600x400')
        dialog.resizable(False, False)
        
        # 设置对话框居中
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # 标题
        title_frame = ttk.Frame(dialog, padding=10)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text=f'用户: {username}', font=('Arial', 14)).pack(side=tk.LEFT)
        ttk.Label(title_frame, text=f'日期: {record_date}', font=('Arial', 14)).pack(side=tk.RIGHT)
        
        # 记录列表
        list_frame = ttk.Frame(dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表格列定义
        columns = ('select', 'id', 'start_time', 'end_time', 'duration', 'shift_type', 'description')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        tree.heading('select', text='保留')
        tree.heading('id', text='ID')
        tree.heading('start_time', text='开始时间')
        tree.heading('end_time', text='结束时间')
        tree.heading('duration', text='时长(分钟)')
        tree.heading('shift_type', text='班别')
        tree.heading('description', text='描述')
        
        # 设置列宽
        tree.column('select', width=50, anchor=tk.CENTER)
        tree.column('id', width=80, anchor=tk.CENTER)
        tree.column('start_time', width=150, anchor=tk.CENTER)
        tree.column('end_time', width=150, anchor=tk.CENTER)
        tree.column('duration', width=100, anchor=tk.CENTER)
        tree.column('shift_type', width=80, anchor=tk.CENTER)
        tree.column('description', width=200, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # 布局表格和滚动条
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 存储选中的记录ID
        selected_record_id = tk.IntVar()
        
        # 添加数据
        for record in records:
            # 默认选中第一条记录
            is_selected = record['id'] == records[0]['id']
            if is_selected:
                selected_record_id.set(record['id'])
            
            tree.insert('', tk.END, values=(
                '☑' if is_selected else '□',
                record['id'],
                record['start_time'],
                record['end_time'],
                record['duration'],
                record['shift_type'],
                record['description']
            ), tags=('record',))
        
        # 绑定点击事件
        def on_tree_click(event):
            item = tree.identify_row(event.y)
            column = tree.identify_column(event.x)
            if column == '#1':  # select列
                # 获取当前行的值
                values = tree.item(item, 'values')
                record_id = int(values[1])
                
                # 更新选中状态
                selected_record_id.set(record_id)
                
                # 更新所有行的选中状态
                for row in tree.get_children():
                    row_values = tree.item(row, 'values')
                    if int(row_values[1]) == record_id:
                        tree.item(row, values=('☑',) + row_values[1:])
                    else:
                        tree.item(row, values=('□',) + row_values[1:])
        
        tree.bind('<ButtonRelease-1>', on_tree_click)
        
        # 按钮框架
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill=tk.X)
        
        def handle_duplicates():
            """处理重复记录"""
            keep_id = selected_record_id.get()
            
            # 删除除了保留记录之外的所有记录
            deleted_count = 0
            for record in records:
                if record['id'] != keep_id:
                    try:
                        response = requests.delete(f'{BASE_URL}/time-records/{record['id']}')
                        if response.status_code == 200:
                            deleted_count += 1
                    except Exception as e:
                        messagebox.showerror('错误', f'删除记录 {record['id']} 失败: {str(e)}')
            
            messagebox.showinfo('成功', f'成功删除 {deleted_count} 条重复记录')
            dialog.destroy()
        
        # 按钮
        ttk.Button(button_frame, text='确定', command=handle_duplicates).pack(side=tk.RIGHT, padx=10)
        ttk.Button(button_frame, text='取消', command=dialog.destroy).pack(side=tk.RIGHT)
    
    def show_main_window(self):
        """显示主窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 主窗口布局
        # 顶部菜单栏
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # 文件菜单
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='文件', menu=file_menu)
        file_menu.add_command(label='退出', command=self.exit_app)
        
        # 首页选项
        menu_bar.add_command(label='首页', command=self.show_main_window)
        
        # 管理菜单
        manage_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='管理', menu=manage_menu)
        manage_menu.add_command(label='用户管理', command=self.show_user_management)
        manage_menu.add_command(label='排班管理', command=self.show_schedule_management)
        manage_menu.add_command(label='工资算法配置', command=self.show_salary_config)
        
        # 权限管理子菜单
        permission_menu = tk.Menu(manage_menu, tearoff=0)
        manage_menu.add_cascade(label='权限管理', menu=permission_menu)
        permission_menu.add_command(label='权限配置', command=self.show_permission_management)
        permission_menu.add_command(label='角色管理', command=self.show_role_management)
        permission_menu.add_command(label='角色权限分配', command=self.show_role_permission_assignment)
        permission_menu.add_command(label='管理员角色分配', command=self.show_admin_role_assignment)
        
        # 模块管理
        manage_menu.add_command(label='模块管理', command=self.show_module_management)
        
        # 操作日志
        manage_menu.add_command(label='操作日志', command=self.show_operation_logs)
        
        # 自动任务管理器
        manage_menu.add_command(label='自动任务管理器', command=self.show_auto_task_manager)
        
        # 统计菜单
        stats_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='统计', menu=stats_menu)
        stats_menu.add_command(label='当天统计', command=self.show_today_stats)
        stats_menu.add_command(label='本周统计', command=self.show_week_stats)
        stats_menu.add_command(label='本月统计', command=self.show_month_stats)
        stats_menu.add_command(label='自定义统计', command=self.show_custom_stats)
        
        # 报表菜单
        report_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='报表', menu=report_menu)
        report_menu.add_command(label='每日出勤报表', command=self.show_daily_attendance_report)
        report_menu.add_command(label='个人出勤报表', command=self.show_personal_attendance_report)
        report_menu.add_command(label='定时任务报表', command=self.show_scheduler_report)
        report_menu.add_command(label='登录报表', command=self.show_login_report)
        report_menu.add_command(label='在线用户报表', command=self.show_online_users_report)
        
        # 帮助菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='帮助', menu=help_menu)
        help_menu.add_command(label='关于', command=self.show_about)
        
        # 欢迎信息
        welcome_frame = ttk.Frame(self.main_frame)
        welcome_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(welcome_frame, text=f'欢迎回来, {self.admin_info.get('username')}', font=('Arial', 16)).pack(side=tk.LEFT)
        ttk.Button(welcome_frame, text='退出登录', command=self.logout).pack(side=tk.RIGHT)
        
        # 首页内容
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        ttk.Label(content_frame, text='考勤管理系统', font=('Arial', 24)).pack(pady=20)
        
        # 快捷功能按钮 - 移到顶部，确保可见
        quick_frame = ttk.Frame(content_frame)
        quick_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(quick_frame, text='快捷功能', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
        
        buttons_frame = ttk.Frame(quick_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text='用户管理', command=self.show_user_management, width=20).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(buttons_frame, text='排班管理', command=self.show_schedule_management, width=20).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(buttons_frame, text='工资算法配置', command=self.show_salary_config, width=20).grid(row=0, column=2, padx=10, pady=10)
        ttk.Button(buttons_frame, text='当天统计', command=self.show_today_stats, width=20).grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(buttons_frame, text='本周统计', command=self.show_week_stats, width=20).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(buttons_frame, text='本月统计', command=self.show_month_stats, width=20).grid(row=1, column=2, padx=10, pady=10)
        
        # 新增：手动将排班写入工时和班别按钮
        ttk.Button(buttons_frame, text='手动将排班写入工时', command=self.manual_add_time_records, width=20).grid(row=2, column=0, padx=10, pady=10)
        
        # 新增：检查重复工时记录按钮
        ttk.Button(buttons_frame, text='检查重复工时记录', command=self.check_duplicate_time_records, width=20).grid(row=2, column=1, padx=10, pady=10)
        
        # 新增：手动发送考勤记录到留言墙按钮
        ttk.Button(buttons_frame, text='手动发送考勤到留言墙', command=self.manual_send_attendance_to_message_wall, width=20).grid(row=3, column=0, padx=10, pady=10)
        
        # 设置网格列权重，使按钮等宽
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)
        buttons_frame.grid_rowconfigure(2, weight=1)
        buttons_frame.grid_rowconfigure(3, weight=1)
        
        # 当天统计卡片 - 移到快捷功能下方
        stats_frame = ttk.Frame(content_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        ttk.Label(stats_frame, text='当天统计', font=('Arial', 18)).pack(anchor=tk.W, pady=10)
        
        # 获取当天统计数据
        today_stats = self.get_today_stats()
        
        if today_stats:
            # 统计卡片网格
            cards_frame = ttk.Frame(stats_frame)
            cards_frame.pack(fill=tk.X, pady=10)
            
            # 上班人数卡片
            card1 = ttk.LabelFrame(cards_frame, text='上班人数')
            card1.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card1, text=str(today_stats.get('working_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 请假人数卡片
            card2 = ttk.LabelFrame(cards_frame, text='请假人数')
            card2.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card2, text=str(today_stats.get('leave_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 总工时卡片
            card3 = ttk.LabelFrame(cards_frame, text='总工时（小时）')
            card3.grid(row=0, column=2, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card3, text=str(today_stats.get('total_hours', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 总请假时长卡片
            card4 = ttk.LabelFrame(cards_frame, text='总请假时长（小时）')
            card4.grid(row=0, column=3, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card4, text=str(today_stats.get('total_leave_hours', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 设置网格列权重，使卡片等宽
            cards_frame.grid_columnconfigure(0, weight=1)
            cards_frame.grid_columnconfigure(1, weight=1)
            cards_frame.grid_columnconfigure(2, weight=1)
            cards_frame.grid_columnconfigure(3, weight=1)
            
            # 白班人数卡片
            card5 = ttk.LabelFrame(cards_frame, text='白班人数')
            card5.grid(row=1, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card5, text=str(today_stats.get('day_shift_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 夜班人数卡片
            card6 = ttk.LabelFrame(cards_frame, text='夜班人数')
            card6.grid(row=1, column=1, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card6, text=str(today_stats.get('night_shift_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 设置第二行网格列权重
            cards_frame.grid_columnconfigure(0, weight=1)
            cards_frame.grid_columnconfigure(1, weight=1)
            cards_frame.grid_columnconfigure(2, weight=1)
            cards_frame.grid_columnconfigure(3, weight=1)
            
            # 出勤人员列表
            ttk.Label(stats_frame, text='出勤人员列表', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
            
            attendance_users = today_stats.get('attendance_users', [])
            if attendance_users:
                # 创建表格显示出勤人员
                attendance_frame = ttk.Frame(stats_frame)
                attendance_frame.pack(fill=tk.BOTH, expand=True, pady=10)
                
                # 表格列定义
                columns = ('username', 'email', 'shift_type', 'today_hours')
                attendance_tree = ttk.Treeview(attendance_frame, columns=columns, show='headings')
                
                # 设置列标题
                attendance_tree.heading('username', text='用户名')
                attendance_tree.heading('email', text='邮箱')
                attendance_tree.heading('shift_type', text='班别')
                attendance_tree.heading('today_hours', text='今日工时(小时)')
                
                # 设置列宽
                attendance_tree.column('username', width=150, anchor=tk.CENTER)
                attendance_tree.column('email', width=200, anchor=tk.CENTER)
                attendance_tree.column('shift_type', width=100, anchor=tk.CENTER)
                attendance_tree.column('today_hours', width=150, anchor=tk.CENTER)
                
                # 添加数据
                for user in attendance_users:
                    attendance_tree.insert('', tk.END, values=(
                        user['username'],
                        user['email'],
                        user['shift_type'],
                        user['today_hours']
                    ))
                
                # 添加滚动条
                scrollbar = ttk.Scrollbar(attendance_frame, orient=tk.VERTICAL, command=attendance_tree.yview)
                attendance_tree.configure(yscroll=scrollbar.set)
                
                # 布局表格和滚动条
                attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                ttk.Label(stats_frame, text='今日暂无出勤人员', font=('Arial', 12)).pack(anchor=tk.W, pady=10)
            
            # 请假人员列表
            ttk.Label(stats_frame, text='请假人员列表', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
            
            leave_users = today_stats.get('leave_users_list', [])
            if leave_users:
                # 创建表格显示请假人员
                leave_frame = ttk.Frame(stats_frame)
                leave_frame.pack(fill=tk.BOTH, expand=True, pady=10)
                
                # 表格列定义
                columns = ('username', 'email', 'shift_type', 'today_hours')
                leave_tree = ttk.Treeview(leave_frame, columns=columns, show='headings')
                
                # 设置列标题
                leave_tree.heading('username', text='用户名')
                leave_tree.heading('email', text='邮箱')
                leave_tree.heading('shift_type', text='班别')
                leave_tree.heading('today_hours', text='请假时长(小时)')
                
                # 设置列宽
                leave_tree.column('username', width=150, anchor=tk.CENTER)
                leave_tree.column('email', width=200, anchor=tk.CENTER)
                leave_tree.column('shift_type', width=100, anchor=tk.CENTER)
                leave_tree.column('today_hours', width=150, anchor=tk.CENTER)
                
                # 添加数据
                for user in leave_users:
                    leave_tree.insert('', tk.END, values=(
                        user['username'],
                        user['email'],
                        user['shift_type'],
                        user['today_hours']
                    ))
                
                # 添加滚动条
                scrollbar = ttk.Scrollbar(leave_frame, orient=tk.VERTICAL, command=leave_tree.yview)
                leave_tree.configure(yscroll=scrollbar.set)
                
                # 布局表格和滚动条
                leave_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                ttk.Label(stats_frame, text='今日暂无请假人员', font=('Arial', 12)).pack(anchor=tk.W, pady=10)
            
            # 日期信息
            ttk.Label(stats_frame, text=f'统计日期: {today_stats.get('date', '')}', font=('Arial', 12)).pack(anchor=tk.W, pady=10)
        else:
            ttk.Label(stats_frame, text='无法获取当天统计数据', font=('Arial', 12), foreground='red').pack(anchor=tk.W, pady=10)
    
    def show_user_management(self):
        """显示用户管理窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='用户管理', font=('Arial', 24)).pack(side=tk.LEFT)
        ttk.Button(title_frame, text='新增用户', command=self.show_add_user_window).pack(side=tk.RIGHT)
        
        # 用户列表
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格
        columns = ('id', 'username', 'email', 'hire_date', 'salary_level', 'actions')
        self.user_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.user_tree.heading('id', text='ID')
        self.user_tree.heading('username', text='用户名')
        self.user_tree.heading('email', text='邮箱')
        self.user_tree.heading('hire_date', text='入职日期')
        self.user_tree.heading('salary_level', text='薪资等级')
        self.user_tree.heading('actions', text='操作')
        
        # 设置列宽
        self.user_tree.column('id', width=50, anchor=tk.CENTER)
        self.user_tree.column('username', width=150, anchor=tk.CENTER)
        self.user_tree.column('email', width=200, anchor=tk.CENTER)
        self.user_tree.column('hire_date', width=120, anchor=tk.CENTER)
        self.user_tree.column('salary_level', width=100, anchor=tk.CENTER)
        self.user_tree.column('actions', width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载用户数据
        self.load_users()
    
    def load_users(self):
        """加载用户数据"""
        # 清空现有数据
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        try:
            response = requests.get(f'{BASE_URL}/users')
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    # 添加操作按钮
                    actions = f"编辑 | 删除"
                    self.user_tree.insert('', tk.END, values=(
                        user.get('id'),
                        user.get('username'),
                        user.get('email'),
                        user.get('hire_date'),
                        user.get('salary_level'),
                        actions
                    ))
                
                # 添加点击事件处理
                self.user_tree.bind('<ButtonRelease-1>', self.on_user_tree_click)
            else:
                messagebox.showerror('错误', '无法获取用户列表')
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def on_user_tree_click(self, event):
        """处理用户列表点击事件"""
        # 获取点击的行和列
        item = self.user_tree.identify_row(event.y)
        column = self.user_tree.identify_column(event.x)
        
        # 如果点击了操作列
        if column == '#6':  # actions列
            # 获取行数据
            values = self.user_tree.item(item, 'values')
            if values:
                user_id = values[0]
                # 获取Treeview控件的坐标
                tree_x = self.user_tree.winfo_x()
                tree_y = self.user_tree.winfo_y()
                # 转换event坐标为相对于Treeview控件的坐标
                tree_event_x = event.x - tree_x
                tree_event_y = event.y - tree_y
                # 获取操作列的坐标和宽度
                x, y, width, height = self.user_tree.bbox(item, column)
                # 计算相对点击位置
                relative_x = tree_event_x - x
                # 计算每个按钮的宽度
                button_width = width / 2
                # 判断点击的是哪个按钮
                if relative_x < button_width:
                    # 编辑按钮
                    self.edit_user(user_id)
                else:
                    # 删除按钮
                    self.delete_user(user_id)
    
    def edit_user(self, user_id):
        """编辑用户"""
        # 导入日期组件
        from tkcalendar import DateEntry
        
        # 获取用户详情
        try:
            response = requests.get(f'{BASE_URL}/users/{user_id}')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取用户详情')
                return
            user = response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title('编辑用户')
        edit_window.geometry('500x400')
        edit_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 用户名
        ttk.Label(form_frame, text='用户名:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_user_username_var = tk.StringVar(value=user.get('username'))
        ttk.Entry(form_frame, textvariable=self.edit_user_username_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 邮箱
        ttk.Label(form_frame, text='邮箱:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_user_email_var = tk.StringVar(value=user.get('email'))
        ttk.Entry(form_frame, textvariable=self.edit_user_email_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 入职日期 - 使用DateEntry组件
        ttk.Label(form_frame, text='入职日期:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        hire_date_entry = DateEntry(form_frame, width=27, date_pattern='yyyy-MM-dd')
        # 设置初始日期
        if user.get('hire_date'):
            try:
                # 处理日期格式，将"Sat, 29 Nov 2025 00:00:00 GMT"转换为"2025-11-29"
                from datetime import datetime
                hire_date_str = user.get('hire_date')
                # 尝试解析不同的日期格式
                try:
                    # 解析ISO格式
                    hire_date = datetime.fromisoformat(hire_date_str.replace('Z', '+00:00'))
                except:
                    # 解析GMT格式
                    hire_date = datetime.strptime(hire_date_str, '%a, %d %b %Y %H:%M:%S GMT')
                # 设置日期
                hire_date_entry.set_date(hire_date)
            except Exception as e:
                print(f'设置入职日期失败: {str(e)}')
        hire_date_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # 薪资等级 - 使用下拉菜单
        ttk.Label(form_frame, text='薪资等级:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_user_salary_level_var = tk.StringVar(value=user.get('salary_level'))
        # 定义薪资等级选项，从E8到D5
        salary_levels = ['E17', 'E16', 'E15', 'E14', 'E13', 'E12', 'E11', 'E10', 'E9', 'E8', 'D1', 'D2', 'D3', 'D4', 'D5']
        salary_combo = ttk.Combobox(form_frame, textvariable=self.edit_user_salary_level_var, width=27, values=salary_levels, state='readonly')
        salary_combo.grid(row=3, column=1, padx=10, pady=10)
        
        # 密码（可选）
        ttk.Label(form_frame, text='密码:').grid(row=4, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_user_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.edit_user_password_var, show='*', width=30).grid(row=4, column=1, padx=10, pady=10)
        ttk.Label(form_frame, text='留空则不修改').grid(row=4, column=2, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        def save_edited_user():
            """保存编辑后的用户"""
            username = self.edit_user_username_var.get()
            email = self.edit_user_email_var.get()
            hire_date = hire_date_entry.get()
            salary_level = self.edit_user_salary_level_var.get()
            password = self.edit_user_password_var.get()
            
            if not username:
                messagebox.showerror('错误', '用户名不能为空')
                return
            
            # 构建更新数据
            update_data = {
                'username': username,
                'email': email,
                'hire_date': hire_date,
                'salary_level': salary_level
            }
            
            # 如果密码不为空，则添加到更新数据中
            if password:
                update_data['password'] = password
            
            try:
                response = requests.put(f'{BASE_URL}/users/{user_id}', json=update_data)
                if response.status_code == 200:
                    messagebox.showinfo('成功', '用户编辑成功')
                    edit_window.destroy()
                    self.load_users()  # 刷新用户列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '编辑用户失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_edited_user).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_user(self, user_id):
        """删除用户"""
        if messagebox.askyesno('确认', f'确定要删除ID为 {user_id} 的用户吗？'):
            try:
                response = requests.delete(f'{BASE_URL}/users/{user_id}')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '用户删除成功')
                    self.load_users()  # 刷新用户列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '删除用户失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def show_add_user_window(self):
        """显示新增用户窗口"""
        # 导入日期组件
        from tkcalendar import DateEntry
        
        # 创建弹窗
        add_window = tk.Toplevel(self.root)
        add_window.title('新增用户')
        add_window.geometry('500x400')
        add_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(add_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 用户名
        ttk.Label(form_frame, text='用户名:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=username_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 密码
        ttk.Label(form_frame, text='密码:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=password_var, show='*', width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 邮箱
        ttk.Label(form_frame, text='邮箱:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=email_var, width=30).grid(row=2, column=1, padx=10, pady=10)
        
        # 入职日期 - 使用DateEntry组件
        ttk.Label(form_frame, text='入职日期:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        hire_date_entry = DateEntry(form_frame, width=27, date_pattern='yyyy-MM-dd')
        hire_date_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # 薪资等级 - 使用下拉菜单
        ttk.Label(form_frame, text='薪资等级:').grid(row=4, column=0, padx=10, pady=10, sticky=tk.E)
        salary_level_var = tk.StringVar()
        # 定义薪资等级选项，从E8到D5
        salary_levels = ['E17', 'E16', 'E15', 'E14', 'E13', 'E12', 'E11', 'E10', 'E9', 'E8', 'D1', 'D2', 'D3', 'D4', 'D5']
        salary_combo = ttk.Combobox(form_frame, textvariable=salary_level_var, width=27, values=salary_levels, state='readonly')
        salary_combo.grid(row=4, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        def save_user():
            """保存用户"""
            username = username_var.get()
            password = password_var.get()
            email = email_var.get()
            hire_date = hire_date_entry.get()
            salary_level = salary_level_var.get()
            
            if not username or not password:
                messagebox.showerror('错误', '用户名和密码不能为空')
                return
            
            try:
                response = requests.post(f'{BASE_URL}/users', json={
                    'username': username,
                    'password': password,
                    'email': email,
                    'hire_date': hire_date,
                    'salary_level': salary_level
                })
                
                if response.status_code == 201:
                    messagebox.showinfo('成功', '用户添加成功')
                    add_window.destroy()
                    self.load_users()  # 刷新用户列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '添加用户失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_user).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=add_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def show_schedule_management(self):
        """显示排班管理窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='排班管理', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 按钮框架
        buttons_frame = ttk.Frame(title_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text='新增排班', command=self.show_add_schedule_window).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text='一键删除过期排班', command=self.delete_expired_schedules).pack(side=tk.LEFT, padx=10)
        
        # 导入日期组件
        from tkcalendar import DateEntry
        
        # 筛选条件
        filter_frame = ttk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(filter_frame, text='筛选条件:').pack(side=tk.LEFT, padx=10)
        
        # 角色筛选
        ttk.Label(filter_frame, text='角色:').pack(side=tk.LEFT, padx=10)
        self.schedule_role_var = tk.StringVar()
        self.schedule_role_combo = ttk.Combobox(filter_frame, textvariable=self.schedule_role_var, width=15)
        self.schedule_role_combo.pack(side=tk.LEFT, padx=10)
        
        # 用户筛选
        ttk.Label(filter_frame, text='用户:').pack(side=tk.LEFT, padx=10)
        self.schedule_user_var = tk.StringVar()
        self.schedule_user_combo = ttk.Combobox(filter_frame, textvariable=self.schedule_user_var, width=20)
        self.schedule_user_combo.pack(side=tk.LEFT, padx=10)
        
        # 日期筛选（使用日期组件）
        ttk.Label(filter_frame, text='日期:').pack(side=tk.LEFT, padx=10)
        self.schedule_date_entry = DateEntry(filter_frame, width=12, date_pattern='yyyy-MM-dd')
        self.schedule_date_entry.pack(side=tk.LEFT, padx=10)
        
        # 筛选按钮
        ttk.Button(filter_frame, text='筛选', command=self.load_schedules).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text='重置', command=self.reset_schedule_filters).pack(side=tk.LEFT, padx=10)
        
        # 排班列表
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格
        columns = ('id', 'user_id', 'username', 'start_date', 'end_date', 'shift_type', 'hours', 'description', 'actions')
        self.schedule_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.schedule_tree.heading('id', text='ID')
        self.schedule_tree.heading('user_id', text='用户ID')
        self.schedule_tree.heading('username', text='用户名')
        self.schedule_tree.heading('start_date', text='日期范围')
        self.schedule_tree.heading('end_date', text='')
        self.schedule_tree.heading('shift_type', text='班别')
        self.schedule_tree.heading('hours', text='工时')
        self.schedule_tree.heading('description', text='描述')
        self.schedule_tree.heading('actions', text='操作')
        
        # 设置列宽
        self.schedule_tree.column('id', width=50, anchor=tk.CENTER)
        self.schedule_tree.column('user_id', width=80, anchor=tk.CENTER)
        self.schedule_tree.column('username', width=120, anchor=tk.CENTER)
        self.schedule_tree.column('start_date', width=180, anchor=tk.CENTER)  # 增加宽度以适应日期范围
        self.schedule_tree.column('end_date', width=0, anchor=tk.CENTER)  # 隐藏结束日期列
        self.schedule_tree.column('shift_type', width=80, anchor=tk.CENTER)
        self.schedule_tree.column('hours', width=80, anchor=tk.CENTER)
        self.schedule_tree.column('description', width=200, anchor=tk.CENTER)
        self.schedule_tree.column('actions', width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载用户数据（用于下拉选择）
        self.load_users_for_combo()
        
        # 加载排班数据
        self.load_schedules()
    
    def load_users_for_combo(self):
        """加载用户数据和角色数据到下拉选择框"""
        try:
            # 加载用户数据
            response = requests.get(f'{BASE_URL}/users')
            if response.status_code == 200:
                users = response.json()
                self.users_dict = {user.get('id'): user.get('username') for user in users}
                # 设置用户下拉选项
                self.schedule_user_combo['values'] = ['全部'] + [f"{user.get('id')} - {user.get('username')}" for user in users]
                self.schedule_user_combo.current(0)  # 默认选择全部
            
            # 加载角色数据
            roles_response = requests.get(f'{BASE_URL}/roles')
            if roles_response.status_code == 200:
                roles = roles_response.json()
                # 设置角色下拉选项
                self.schedule_role_combo['values'] = ['全部'] + [role.get('name') for role in roles]
                self.schedule_role_combo.current(0)  # 默认选择全部
        except Exception as e:
            print(f'加载数据失败: {str(e)}')
    
    def load_schedules(self):
        """加载排班数据"""
        # 导入datetime模块
        from datetime import datetime
        # 清空现有数据
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        try:
            # 获取筛选条件
            user_filter = self.schedule_user_var.get()
            role_filter = self.schedule_role_var.get()
            date_filter = self.schedule_date_entry.get()
            
            # 获取所有用户，用于后续根据角色筛选
            users_response = requests.get(f'{BASE_URL}/users')
            if users_response.status_code != 200:
                messagebox.showerror('错误', '无法获取用户列表')
                return
            all_users = users_response.json()
            
            # 根据角色筛选用户
            filtered_user_ids = []
            if role_filter != '全部':
                # 筛选出具有指定角色的用户
                filtered_users = []
                for user in all_users:
                    # 获取用户的所有角色
                    try:
                        roles_response = requests.get(f'{BASE_URL}/users/{user.get('id')}/roles')
                        if roles_response.status_code == 200:
                            user_roles = roles_response.json()
                            # 检查用户是否具有指定角色
                            if any(role.get('name') == role_filter for role in user_roles):
                                filtered_users.append(user)
                    except Exception as e:
                        print(f'获取用户角色失败: {str(e)}')
                filtered_user_ids = [user.get('id') for user in filtered_users]
            
            url = f'{BASE_URL}/schedules'
            
            # 存储所有符合条件的排班
            all_schedules = []
            
            # 获取所有排班或根据用户筛选
            if user_filter != '全部':
                # 提取用户ID
                user_id = user_filter.split(' - ')[0]
                response = requests.get(f'{BASE_URL}/schedules/user/{user_id}')
                if response.status_code == 200:
                    all_schedules = response.json()
            elif date_filter:
                response = requests.get(f'{BASE_URL}/schedules/date/{date_filter}')
                if response.status_code == 200:
                    all_schedules = response.json()
            else:
                response = requests.get(url)
                if response.status_code == 200:
                    all_schedules = response.json()
            
            # 应用角色筛选
            if role_filter != '全部':
                all_schedules = [schedule for schedule in all_schedules if schedule.get('user_id') in filtered_user_ids]
            
            # 显示排班数据
            for schedule in all_schedules:
                # 获取用户名
                username = self.users_dict.get(schedule.get('user_id'), '未知用户')
                
                # 格式化日期为中文格式
                def format_date(date_str):
                    """将各种日期格式转换为中文格式"""
                    if not date_str:
                        return ''
                    try:
                        # 尝试解析多种日期格式
                        if 'GMT' in date_str:
                            # 处理 GMT 格式，如 "Mon, Dec 01 2025 00:00:00 GMT"
                            date = datetime.strptime(date_str, '%a, %b %d %Y %H:%M:%S GMT')
                        else:
                            # 处理 ISO 格式，如 "2025-12-01"
                            date = datetime.strptime(date_str, '%Y-%m-%d')
                        return f"{date.month}月{date.day}日"
                    except Exception as e:
                        # 使用英文错误信息避免编码问题
                        print(f"Date parse error: {date_str}, error: {str(e)}")
                        return date_str
                
                def format_date_range(start_date, end_date):
                    """格式化日期范围为中文格式"""
                    if not start_date or not end_date:
                        return ''
                    try:
                        # 解析开始日期
                        if 'GMT' in start_date:
                            start = datetime.strptime(start_date, '%a, %b %d %Y %H:%M:%S GMT')
                        else:
                            start = datetime.strptime(start_date, '%Y-%m-%d')
                        
                        # 解析结束日期
                        if 'GMT' in end_date:
                            end = datetime.strptime(end_date, '%a, %b %d %Y %H:%M:%S GMT')
                        else:
                            end = datetime.strptime(end_date, '%Y-%m-%d')
                        
                        # 如果是同一年
                        if start.year == end.year:
                            # 如果是同一月
                            if start.month == end.month:
                                # 格式：12月1日-14日
                                return f"{start.month}月{start.day}日-{end.day}日"
                            else:
                                # 格式：12月1日-1月14日
                                return f"{start.month}月{start.day}日-{end.month}月{end.day}日"
                        else:
                            # 格式：2023年12月1日-2024年1月14日
                            return f"{start.year}年{start.month}月{start.day}日-{end.year}年{end.month}月{end.day}日"
                    except Exception as e:
                        # 使用英文错误信息避免编码问题
                        print(f"Date range parse error: {start_date} - {end_date}, error: {str(e)}")
                        return f"{start_date} - {end_date}"
                
                # 格式化日期范围
                date_range = format_date_range(schedule.get('start_date'), schedule.get('end_date'))
                
                # 添加操作按钮
                actions = f"编辑 | 删除"
                self.schedule_tree.insert('', tk.END, values=(
                    schedule.get('id'),
                    schedule.get('user_id'),
                    username,
                    date_range,  # 显示格式化后的日期范围
                    '',  # 结束日期列留空，因为已经在日期范围中显示
                    schedule.get('shift_type'),
                    schedule.get('hours'),
                    schedule.get('description'),
                    actions
                ))
            
            # 添加点击事件处理
            self.schedule_tree.bind('<ButtonRelease-1>', self.on_schedule_tree_click)
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def on_schedule_tree_click(self, event):
        """处理排班列表点击事件"""
        # 获取点击的行和列
        item = self.schedule_tree.identify_row(event.y)
        column = self.schedule_tree.identify_column(event.x)
        
        # 如果点击了操作列
        if column == '#9':  # actions列
            # 获取行数据
            values = self.schedule_tree.item(item, 'values')
            if values:
                schedule_id = values[0]
                # 获取Treeview控件的坐标
                tree_x = self.schedule_tree.winfo_x()
                tree_y = self.schedule_tree.winfo_y()
                # 转换event坐标为相对于Treeview控件的坐标
                tree_event_x = event.x - tree_x
                tree_event_y = event.y - tree_y
                # 获取操作列的坐标和宽度
                x, y, width, height = self.schedule_tree.bbox(item, column)
                # 计算相对点击位置
                relative_x = tree_event_x - x
                # 计算操作按钮的宽度
                button_width = width / 2
                # 判断点击的是编辑还是删除按钮
                if relative_x < button_width:
                    # 编辑按钮
                    self.edit_schedule(schedule_id)
                else:
                    # 删除按钮
                    self.delete_schedule(schedule_id)
    
    def edit_schedule(self, schedule_id):
        """编辑排班"""
        from datetime import datetime, timedelta
        # 获取排班详情
        try:
            response = requests.get(f'{BASE_URL}/schedules/{schedule_id}')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取排班详情')
                return
            schedule = response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title('编辑排班')
        edit_window.geometry('600x500')
        edit_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 用户选择
        ttk.Label(form_frame, text='用户:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_schedule_user_var = tk.StringVar()
        user_combo = ttk.Combobox(form_frame, textvariable=self.edit_schedule_user_var, width=30)
        user_combo['values'] = [f"{user_id} - {username}" for user_id, username in self.users_dict.items()]
        # 设置默认值
        user_combo.set(f"{schedule.get('user_id')} - {self.users_dict.get(schedule.get('user_id'))}")
        user_combo.grid(row=0, column=1, padx=10, pady=10)
        
        # 处理日期格式，确保是YYYY-MM-DD格式
        start_date = schedule.get('start_date', '')
        if 'T' in start_date:
            start_date = start_date.split('T')[0]
        end_date = schedule.get('end_date', '')
        if 'T' in end_date:
            end_date = end_date.split('T')[0]
        
        # 开始日期（使用标准日期组件，确保格式整齐）
        ttk.Label(form_frame, text='开始日期:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_schedule_start_var = tk.StringVar(value=start_date)
        # 使用简单的Entry组件，添加日期格式提示和验证
        start_date_entry = ttk.Entry(form_frame, textvariable=self.edit_schedule_start_var, width=28)
        start_date_entry.grid(row=1, column=1, padx=10, pady=10)
        # 添加日期格式标签
        ttk.Label(form_frame, text='YYYY-MM-DD', font=('Arial', 8, 'bold')).grid(row=1, column=2, padx=5, pady=10, sticky=tk.W)
        
        # 结束日期（使用标准日期组件，确保格式整齐）
        ttk.Label(form_frame, text='结束日期:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_schedule_end_var = tk.StringVar(value=end_date)
        # 使用简单的Entry组件，添加日期格式提示和验证
        end_date_entry = ttk.Entry(form_frame, textvariable=self.edit_schedule_end_var, width=28)
        end_date_entry.grid(row=2, column=1, padx=10, pady=10)
        # 添加日期格式标签
        ttk.Label(form_frame, text='YYYY-MM-DD', font=('Arial', 8, 'bold')).grid(row=2, column=2, padx=5, pady=10, sticky=tk.W)
        
        # 添加日期选择辅助按钮
        def set_today_start():
            """设置开始日期为今天"""
            self.edit_schedule_start_var.set(datetime.now().strftime('%Y-%m-%d'))
        
        def set_today_end():
            """设置结束日期为今天"""
            self.edit_schedule_end_var.set(datetime.now().strftime('%Y-%m-%d'))
        
        def set_previous_month_start():
            """设置开始日期为上个月"""
            # 获取当前输入的日期
            current_date_str = self.edit_schedule_start_var.get()
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d')
                # 计算上个月的日期
                if current_date.month == 1:
                    previous_month = current_date.replace(year=current_date.year - 1, month=12, day=1)
                else:
                    previous_month = current_date.replace(month=current_date.month - 1, day=1)
                self.edit_schedule_start_var.set(previous_month.strftime('%Y-%m-%d'))
            except ValueError:
                # 如果当前日期格式不正确，使用今天的日期计算
                today = datetime.now()
                if today.month == 1:
                    previous_month = today.replace(year=today.year - 1, month=12, day=1)
                else:
                    previous_month = today.replace(month=today.month - 1, day=1)
                self.edit_schedule_start_var.set(previous_month.strftime('%Y-%m-%d'))
        
        def set_next_month_start():
            """设置开始日期为下个月"""
            # 获取当前输入的日期
            current_date_str = self.edit_schedule_start_var.get()
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d')
                # 计算下个月的日期
                if current_date.month == 12:
                    next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                self.edit_schedule_start_var.set(next_month.strftime('%Y-%m-%d'))
            except ValueError:
                # 如果当前日期格式不正确，使用今天的日期计算
                today = datetime.now()
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
                self.edit_schedule_start_var.set(next_month.strftime('%Y-%m-%d'))
        
        def set_previous_month_end():
            """设置结束日期为上个月"""
            # 获取当前输入的日期
            current_date_str = self.edit_schedule_end_var.get()
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d')
                # 计算上个月的日期
                if current_date.month == 1:
                    previous_month = current_date.replace(year=current_date.year - 1, month=12, day=1)
                else:
                    previous_month = current_date.replace(month=current_date.month - 1, day=1)
                self.edit_schedule_end_var.set(previous_month.strftime('%Y-%m-%d'))
            except ValueError:
                # 如果当前日期格式不正确，使用今天的日期计算
                today = datetime.now()
                if today.month == 1:
                    previous_month = today.replace(year=today.year - 1, month=12, day=1)
                else:
                    previous_month = today.replace(month=today.month - 1, day=1)
                self.edit_schedule_end_var.set(previous_month.strftime('%Y-%m-%d'))
        
        def set_next_month_end():
            """设置结束日期为下个月"""
            # 获取当前输入的日期
            current_date_str = self.edit_schedule_end_var.get()
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d')
                # 计算下个月的日期
                if current_date.month == 12:
                    next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                self.edit_schedule_end_var.set(next_month.strftime('%Y-%m-%d'))
            except ValueError:
                # 如果当前日期格式不正确，使用今天的日期计算
                today = datetime.now()
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
                self.edit_schedule_end_var.set(next_month.strftime('%Y-%m-%d'))
        
        # 添加日期操作按钮框架
        start_date_buttons = ttk.Frame(form_frame)
        start_date_buttons.grid(row=1, column=3, padx=5, pady=10)
        
        # 开始日期按钮
        ttk.Button(start_date_buttons, text='上个月', command=set_previous_month_start, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(start_date_buttons, text='今天', command=set_today_start, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(start_date_buttons, text='下个月', command=set_next_month_start, width=8).pack(side=tk.LEFT, padx=2)
        
        # 结束日期按钮框架
        end_date_buttons = ttk.Frame(form_frame)
        end_date_buttons.grid(row=2, column=3, padx=5, pady=10)
        
        # 结束日期按钮
        ttk.Button(end_date_buttons, text='上个月', command=set_previous_month_end, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(end_date_buttons, text='今天', command=set_today_end, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(end_date_buttons, text='下个月', command=set_next_month_end, width=8).pack(side=tk.LEFT, padx=2)
        
        # 班别
        ttk.Label(form_frame, text='班别:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_schedule_shift_var = tk.StringVar()
        shift_combo = ttk.Combobox(form_frame, textvariable=self.edit_schedule_shift_var, width=30)
        shift_combo['values'] = ['白班', '夜班']
        shift_combo.set(schedule.get('shift_type'))
        shift_combo.grid(row=3, column=1, padx=10, pady=10)
        
        # 工时
        ttk.Label(form_frame, text='工时:').grid(row=4, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_schedule_hours_var = tk.StringVar()
        self.edit_schedule_hours_var.set(schedule.get('hours'))
        ttk.Entry(form_frame, textvariable=self.edit_schedule_hours_var, width=30).grid(row=4, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=5, column=0, padx=10, pady=10, sticky=tk.NE)
        self.edit_schedule_desc_var = tk.StringVar()
        self.edit_schedule_desc_var.set(schedule.get('description') or '')
        ttk.Entry(form_frame, textvariable=self.edit_schedule_desc_var, width=30).grid(row=5, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        def save_edited_schedule():
            """保存编辑后的排班"""
            # 提取用户ID
            user_text = self.edit_schedule_user_var.get()
            if not user_text:
                messagebox.showerror('错误', '请选择用户')
                return
            user_id = user_text.split(' - ')[0]
            
            # 获取日期
            start_date = self.edit_schedule_start_var.get()
            end_date = self.edit_schedule_end_var.get()
            shift_type = self.edit_schedule_shift_var.get()
            hours = self.edit_schedule_hours_var.get()
            description = self.edit_schedule_desc_var.get()
            
            if not start_date or not end_date or not shift_type or not hours:
                messagebox.showerror('错误', '开始日期、结束日期、班别和工时不能为空')
                return
            
            # 验证日期格式（YYYY-MM-DD）
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            if not re.match(date_pattern, start_date):
                messagebox.showerror('错误', '开始日期格式不正确，请使用YYYY-MM-DD格式')
                return
            if not re.match(date_pattern, end_date):
                messagebox.showerror('错误', '结束日期格式不正确，请使用YYYY-MM-DD格式')
                return
            
            # 验证日期有效性
            try:
                from datetime import datetime
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                if end_datetime < start_datetime:
                    messagebox.showerror('错误', '结束日期不能早于开始日期')
                    return
            except ValueError:
                messagebox.showerror('错误', '日期无效，请检查日期是否正确')
                return
            
            try:
                hours = float(hours)
            except:
                messagebox.showerror('错误', '工时必须是数字')
                return
            
            try:
                response = requests.put(f'{BASE_URL}/schedules/{schedule_id}', json={
                    'user_id': user_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'shift_type': shift_type,
                    'hours': hours,
                    'description': description
                })
                
                if response.status_code == 200:
                    messagebox.showinfo('成功', '排班编辑成功')
                    edit_window.destroy()
                    self.load_schedules()  # 刷新排班列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '编辑排班失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_edited_schedule).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_schedule(self, schedule_id):
        """删除排班"""
        if messagebox.askyesno('确认', f'确定要删除ID为 {schedule_id} 的排班吗？'):
            try:
                response = requests.delete(f'{BASE_URL}/schedules/{schedule_id}')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '排班删除成功')
                    self.load_schedules()  # 刷新排班列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '删除排班失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def delete_expired_schedules(self):
        """删除过期排班"""
        if messagebox.askyesno('确认', '确定要删除所有过期的排班计划吗？'):
            try:
                response = requests.delete(f'{BASE_URL}/schedules/expired')
                if response.status_code == 200:
                    messagebox.showinfo('成功', response.json().get('message', '过期排班删除成功'))
                    self.load_schedules()  # 刷新排班列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '删除过期排班失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def reset_schedule_filters(self):
        """重置筛选条件"""
        self.schedule_user_combo.current(0)
        self.schedule_role_combo.current(0)  # 重置角色筛选
        # 重置日期组件 - 使用当前日期作为默认值
        from datetime import datetime
        self.schedule_date_entry.set_date(datetime.now())
        self.load_schedules()
    
    def show_add_schedule_window(self):
        """显示新增排班窗口"""
        # 导入日期组件
        from tkcalendar import DateEntry
        
        # 创建弹窗
        add_window = tk.Toplevel(self.root)
        add_window.title('新增排班')
        add_window.geometry('600x500')
        add_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(add_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 角色选择
        ttk.Label(form_frame, text='角色:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_schedule_role_var = tk.StringVar()
        role_combo = ttk.Combobox(form_frame, textvariable=self.new_schedule_role_var, width=30)
        # 加载角色数据
        try:
            roles_response = requests.get(f'{BASE_URL}/roles')
            if roles_response.status_code == 200:
                roles = roles_response.json()
                role_combo['values'] = ['选择角色'] + [role.get('name') for role in roles]
                role_combo.current(0)  # 默认选择"选择角色"
        except Exception as e:
            print(f'加载角色数据失败: {str(e)}')
        role_combo.grid(row=0, column=1, padx=10, pady=10)
        
        # 用户选择
        ttk.Label(form_frame, text='用户:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_schedule_user_var = tk.StringVar()
        user_combo = ttk.Combobox(form_frame, textvariable=self.new_schedule_user_var, width=30)
        user_combo['values'] = ['选择用户'] + [f"{user_id} - {username}" for user_id, username in self.users_dict.items()]
        user_combo.current(0)  # 默认选择"选择用户"
        user_combo.grid(row=1, column=1, padx=10, pady=10)
        
        # 开始日期（使用日期组件）
        ttk.Label(form_frame, text='开始日期:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.start_date_entry = DateEntry(form_frame, width=28, date_pattern='yyyy-MM-dd')
        self.start_date_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # 结束日期（使用日期组件）
        ttk.Label(form_frame, text='结束日期:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        self.end_date_entry = DateEntry(form_frame, width=28, date_pattern='yyyy-MM-dd')
        self.end_date_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # 班别
        ttk.Label(form_frame, text='班别:').grid(row=4, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_schedule_shift_var = tk.StringVar()
        shift_combo = ttk.Combobox(form_frame, textvariable=self.new_schedule_shift_var, width=30)
        shift_combo['values'] = ['白班', '夜班']
        shift_combo.grid(row=4, column=1, padx=10, pady=10)
        
        # 工时
        ttk.Label(form_frame, text='工时:').grid(row=5, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_schedule_hours_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_schedule_hours_var, width=30).grid(row=5, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=6, column=0, padx=10, pady=10, sticky=tk.NE)
        self.new_schedule_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_schedule_desc_var, width=30).grid(row=6, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        
        def save_schedule():
            """保存排班"""
            # 获取表单数据
            role = self.new_schedule_role_var.get()
            user_text = self.new_schedule_user_var.get()
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            shift_type = self.new_schedule_shift_var.get()
            hours = self.new_schedule_hours_var.get()
            description = self.new_schedule_desc_var.get()
            
            # 验证必填字段
            if not start_date or not end_date or not shift_type or not hours:
                messagebox.showerror('错误', '开始日期、结束日期、班别和工时不能为空')
                return
            
            try:
                hours = float(hours)
            except:
                messagebox.showerror('错误', '工时必须是数字')
                return
            
            # 验证角色或用户选择
            if role == '选择角色' and user_text == '选择用户':
                messagebox.showerror('错误', '请选择角色或用户')
                return
            
            if role != '选择角色' and user_text != '选择用户':
                messagebox.showerror('错误', '请只选择角色或用户，不能同时选择')
                return
            
            try:
                # 获取要排班的用户ID列表
                user_ids = []
                
                if role != '选择角色':
                    # 按角色排班，获取该角色下的所有用户
                    users_response = requests.get(f'{BASE_URL}/users')
                    if users_response.status_code == 200:
                        users = users_response.json()
                        # 筛选出具有指定角色的用户
                        role_users = []
                        for user in users:
                            # 获取用户的所有角色
                            try:
                                roles_response = requests.get(f'{BASE_URL}/users/{user.get('id')}/roles')
                                if roles_response.status_code == 200:
                                    user_roles = roles_response.json()
                                    # 检查用户是否具有指定角色
                                    if any(r.get('name') == role for r in user_roles):
                                        role_users.append(user)
                            except Exception as e:
                                print(f'获取用户角色失败: {str(e)}')
                        user_ids = [user.get('id') for user in role_users]
                        if not user_ids:
                            messagebox.showerror('错误', f'角色 {role} 下没有用户')
                            return
                else:
                    # 按用户排班，提取用户ID
                    user_id = user_text.split(' - ')[0]
                    user_ids = [user_id]
                
                # 批量创建排班
                success_count = 0
                failed_count = 0
                for user_id in user_ids:
                    # 检查该用户在指定日期范围内是否已经有排班记录
                    try:
                        # 构建查询URL，获取该用户在指定日期范围内的排班记录
                        check_url = f'{BASE_URL}/schedules/user/{user_id}/date/{start_date}'
                        check_response = requests.get(check_url)
                        if check_response.status_code == 200:
                            existing_schedules = check_response.json()
                            if existing_schedules:
                                failed_count += 1
                                continue
                    except Exception as e:
                        print(f'检查重复排班失败: {str(e)}')
                        failed_count += 1
                        continue
                    
                    # 创建排班记录
                    response = requests.post(f'{BASE_URL}/schedules', json={
                        'user_id': user_id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'shift_type': shift_type,
                        'hours': hours,
                        'description': description
                    })
                    if response.status_code == 201:
                        success_count += 1
                    else:
                        failed_count += 1
                
                # 显示结果
                result_msg = f'成功添加 {success_count} 条排班记录'
                if failed_count > 0:
                    result_msg += f'，{failed_count} 条记录添加失败（可能是重复排班）'
                messagebox.showinfo('结果', result_msg)
                add_window.destroy()
                self.load_schedules()  # 刷新排班列表
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_schedule).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=add_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def show_salary_config(self):
        """显示工资算法配置窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='工资算法配置', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 保存按钮
        save_btn = ttk.Button(title_frame, text='保存配置')
        save_btn.pack(side=tk.RIGHT)
        
        # 配置内容
        config_frame = ttk.Frame(self.main_frame)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 配置表格
        columns = ('config_key', 'config_value', 'description')
        config_tree = ttk.Treeview(config_frame, columns=columns, show='headings')
        
        # 设置列标题
        config_tree.heading('config_key', text='配置项')
        config_tree.heading('config_value', text='配置值')
        config_tree.heading('description', text='描述')
        
        # 设置列宽
        config_tree.column('config_key', width=150, anchor=tk.CENTER)
        config_tree.column('config_value', width=150, anchor=tk.CENTER)
        config_tree.column('description', width=300, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(config_frame, orient=tk.VERTICAL, command=config_tree.yview)
        config_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置数据存储
        config_data = []
        
        # 加载配置数据
        def load_config():
            """加载配置数据"""
            try:
                response = requests.get(f'{BASE_URL}/salary-config')
                if response.status_code != 200:
                    messagebox.showerror('错误', '无法获取工资算法配置数据')
                    return
                configs = response.json()
                
                # 清空表格
                for item in config_tree.get_children():
                    config_tree.delete(item)
                
                # 清空配置数据
                config_data.clear()
                
                # 添加配置项
                for config in configs:
                    config_data.append(config)
                    config_tree.insert('', tk.END, values=(
                        config.get('config_key'),
                        config.get('config_value'),
                        config.get('description')
                    ))
            except Exception as e:
                messagebox.showerror('错误', f'加载配置数据失败: {str(e)}')
        
        # 保存配置数据
        def save_config():
            """保存配置数据"""
            try:
                # 获取所有配置项
                for item in config_tree.get_children():
                    values = config_tree.item(item, 'values')
                    config_key = values[0]
                    config_value = values[1]
                    
                    # 转换配置值为数字
                    try:
                        config_value = float(config_value)
                    except:
                        messagebox.showerror('错误', f'配置项 {config_key} 的值必须是数字')
                        return
                    
                    # 找到对应的配置项
                    for config in config_data:
                        if config['config_key'] == config_key:
                            # 更新配置值
                            config['config_value'] = config_value
                            break
                
                # 保存配置
                for config in config_data:
                    response = requests.put(f'{BASE_URL}/salary-config', json={
                        'config_key': config['config_key'],
                        'config_value': config['config_value'],
                        'description': config['description']
                    })
                    if response.status_code != 200:
                        messagebox.showerror('错误', f'保存配置项 {config['config_key']} 失败')
                        return
                
                messagebox.showinfo('成功', '配置保存成功')
            except Exception as e:
                messagebox.showerror('错误', f'保存配置失败: {str(e)}')
        
        # 双击编辑配置值
        def on_config_tree_double_click(event):
            """处理配置表格双击事件"""
            item = config_tree.identify_row(event.y)
            column = config_tree.identify_column(event.x)
            
            # 如果点击了配置值列
            if column == '#2':
                # 获取当前值
                values = config_tree.item(item, 'values')
                config_key = values[0]
                current_value = values[1]
                
                # 创建编辑窗口
                edit_window = tk.Toplevel(self.root)
                edit_window.title('编辑配置值')
                edit_window.geometry('400x200')
                edit_window.resizable(False, False)
                
                # 表单框架
                form_frame = ttk.Frame(edit_window, padding=20)
                form_frame.pack(fill=tk.BOTH, expand=True)
                
                # 配置项名称
                ttk.Label(form_frame, text=f'配置项: {config_key}').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
                
                # 配置值输入框
                value_var = tk.StringVar(value=str(current_value))
                ttk.Entry(form_frame, textvariable=value_var, width=30).grid(row=1, column=0, padx=10, pady=10)
                
                # 按钮
                button_frame = ttk.Frame(form_frame)
                button_frame.grid(row=2, column=0, pady=20)
                
                def save_edited_value():
                    """保存编辑后的配置值"""
                    new_value = value_var.get()
                    
                    # 验证配置值
                    try:
                        float(new_value)
                    except:
                        messagebox.showerror('错误', '配置值必须是数字')
                        return
                    
                    # 更新表格
                    config_tree.set(item, column, new_value)
                    
                    # 关闭窗口
                    edit_window.destroy()
                
                ttk.Button(button_frame, text='保存', command=save_edited_value).pack(side=tk.LEFT, padx=10)
                ttk.Button(button_frame, text='取消', command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
        
        # 绑定双击事件
        config_tree.bind('<Double-1>', on_config_tree_double_click)
        
        # 绑定保存按钮事件
        save_btn.config(command=save_config)
        
        # 初始加载配置数据
        load_config()
    
    def show_today_stats(self):
        """显示当天统计窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='当天统计', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 统计内容
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        try:
            # 获取当天统计数据
            response = requests.get(f'{BASE_URL}/stats/today')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取当天统计数据')
                return
            today_stats = response.json()
            
            # 显示统计数据
            ttk.Label(stats_frame, text=f'统计日期: {today_stats.get('date', '')}', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
            
            # 统计卡片网格
            cards_frame = ttk.Frame(stats_frame)
            cards_frame.pack(fill=tk.X, pady=10)
            
            # 上班人数卡片
            card1 = ttk.LabelFrame(cards_frame, text='上班人数')
            card1.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card1, text=str(today_stats.get('working_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 总工时卡片
            card2 = ttk.LabelFrame(cards_frame, text='总工时（小时）')
            card2.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card2, text=str(today_stats.get('total_hours', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 白班人数卡片
            card3 = ttk.LabelFrame(cards_frame, text='白班人数')
            card3.grid(row=0, column=2, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card3, text=str(today_stats.get('day_shift_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 夜班人数卡片
            card4 = ttk.LabelFrame(cards_frame, text='夜班人数')
            card4.grid(row=0, column=3, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card4, text=str(today_stats.get('night_shift_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 设置网格列权重，使卡片等宽
            cards_frame.grid_columnconfigure(0, weight=1)
            cards_frame.grid_columnconfigure(1, weight=1)
            cards_frame.grid_columnconfigure(2, weight=1)
            cards_frame.grid_columnconfigure(3, weight=1)
            
        except Exception as e:
            messagebox.showerror('错误', f'获取当天统计数据失败: {str(e)}')
    
    def show_week_stats(self):
        """显示本周统计窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='本周统计', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 统计内容
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        try:
            # 获取本周统计数据
            response = requests.get(f'{BASE_URL}/stats/week')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取本周统计数据')
                return
            week_stats = response.json()
            
            # 显示统计数据
            ttk.Label(stats_frame, text=f'统计日期: {week_stats.get('start_date', '')} 至 {week_stats.get('end_date', '')}', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
            
            # 统计卡片网格
            cards_frame = ttk.Frame(stats_frame)
            cards_frame.pack(fill=tk.X, pady=10)
            
            # 上班人数卡片
            card1 = ttk.LabelFrame(cards_frame, text='上班人数')
            card1.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card1, text=str(week_stats.get('working_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 总工时卡片
            card2 = ttk.LabelFrame(cards_frame, text='总工时（小时）')
            card2.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card2, text=str(week_stats.get('total_hours', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 白班天数卡片
            card3 = ttk.LabelFrame(cards_frame, text='白班天数')
            card3.grid(row=0, column=2, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card3, text=str(week_stats.get('day_shifts', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 夜班天数卡片
            card4 = ttk.LabelFrame(cards_frame, text='夜班天数')
            card4.grid(row=0, column=3, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card4, text=str(week_stats.get('night_shifts', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 设置网格列权重，使卡片等宽
            cards_frame.grid_columnconfigure(0, weight=1)
            cards_frame.grid_columnconfigure(1, weight=1)
            cards_frame.grid_columnconfigure(2, weight=1)
            cards_frame.grid_columnconfigure(3, weight=1)
            
        except Exception as e:
            messagebox.showerror('错误', f'获取本周统计数据失败: {str(e)}')
    
    def show_month_stats(self):
        """显示本月统计窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='本月统计', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 统计内容
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        try:
            # 获取本月统计数据
            response = requests.get(f'{BASE_URL}/stats/month')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取本月统计数据')
                return
            month_stats = response.json()
            
            # 显示统计数据
            ttk.Label(stats_frame, text=f'统计日期: {month_stats.get('start_date', '')} 至 {month_stats.get('end_date', '')}', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
            
            # 统计卡片网格
            cards_frame = ttk.Frame(stats_frame)
            cards_frame.pack(fill=tk.X, pady=10)
            
            # 上班人数卡片
            card1 = ttk.LabelFrame(cards_frame, text='上班人数')
            card1.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card1, text=str(month_stats.get('working_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 总工时卡片
            card2 = ttk.LabelFrame(cards_frame, text='总工时（小时）')
            card2.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card2, text=str(month_stats.get('total_hours', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 白班天数卡片
            card3 = ttk.LabelFrame(cards_frame, text='白班天数')
            card3.grid(row=0, column=2, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card3, text=str(month_stats.get('day_shifts', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 夜班天数卡片
            card4 = ttk.LabelFrame(cards_frame, text='夜班天数')
            card4.grid(row=0, column=3, padx=10, pady=10, sticky=tk.NSEW)
            ttk.Label(card4, text=str(month_stats.get('night_shifts', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
            
            # 设置网格列权重，使卡片等宽
            cards_frame.grid_columnconfigure(0, weight=1)
            cards_frame.grid_columnconfigure(1, weight=1)
            cards_frame.grid_columnconfigure(2, weight=1)
            cards_frame.grid_columnconfigure(3, weight=1)
            
        except Exception as e:
            messagebox.showerror('错误', f'获取本月统计数据失败: {str(e)}')
    
    def show_custom_stats(self):
        """显示自定义统计窗口"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='自定义统计', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 筛选条件
        filter_frame = ttk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(filter_frame, text='日期范围:').pack(side=tk.LEFT, padx=10)
        
        # 导入日期组件
        from tkcalendar import DateEntry
        
        # 开始日期
        start_date_entry = DateEntry(filter_frame, width=12, date_pattern='yyyy-MM-dd')
        start_date_entry.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(filter_frame, text='至').pack(side=tk.LEFT, padx=10)
        
        # 结束日期
        end_date_entry = DateEntry(filter_frame, width=12, date_pattern='yyyy-MM-dd')
        end_date_entry.pack(side=tk.LEFT, padx=10)
        
        # 生成统计按钮
        generate_btn = ttk.Button(filter_frame, text='生成统计')
        generate_btn.pack(side=tk.LEFT, padx=10)
        
        # 统计内容
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 统计结果显示区域
        result_frame = ttk.Frame(stats_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 显示提示信息
        ttk.Label(result_frame, text='请选择日期范围并点击生成统计按钮', font=('Arial', 16)).pack(anchor=tk.CENTER, pady=20)
        
        def generate_stats():
            """生成自定义统计"""
            # 清空结果区域
            for widget in result_frame.winfo_children():
                widget.destroy()
            
            # 获取日期范围
            start_date = start_date_entry.get()
            end_date = end_date_entry.get()
            
            if not start_date or not end_date:
                ttk.Label(result_frame, text='请选择完整的日期范围', font=('Arial', 16), foreground='red').pack(anchor=tk.CENTER, pady=20)
                return
            
            try:
                # 获取自定义统计数据
                response = requests.get(f'{BASE_URL}/stats/custom?start_date={start_date}&end_date={end_date}')
                if response.status_code != 200:
                    ttk.Label(result_frame, text='无法获取自定义统计数据', font=('Arial', 16), foreground='red').pack(anchor=tk.CENTER, pady=20)
                    return
                custom_stats = response.json()
                
                # 显示统计数据
                ttk.Label(result_frame, text=f'统计日期: {custom_stats.get('start_date', '')} 至 {custom_stats.get('end_date', '')}', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
                
                # 统计卡片网格
                cards_frame = ttk.Frame(result_frame)
                cards_frame.pack(fill=tk.X, pady=10)
                
                # 上班人数卡片
                card1 = ttk.LabelFrame(cards_frame, text='上班人数')
                card1.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
                ttk.Label(card1, text=str(custom_stats.get('working_users', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
                
                # 总工时卡片
                card2 = ttk.LabelFrame(cards_frame, text='总工时（小时）')
                card2.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
                ttk.Label(card2, text=str(custom_stats.get('total_hours', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
                
                # 白班天数卡片
                card3 = ttk.LabelFrame(cards_frame, text='白班天数')
                card3.grid(row=0, column=2, padx=10, pady=10, sticky=tk.NSEW)
                ttk.Label(card3, text=str(custom_stats.get('day_shifts', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
                
                # 夜班天数卡片
                card4 = ttk.LabelFrame(cards_frame, text='夜班天数')
                card4.grid(row=0, column=3, padx=10, pady=10, sticky=tk.NSEW)
                ttk.Label(card4, text=str(custom_stats.get('night_shifts', 0)), font=('Arial', 36)).pack(padx=20, pady=20)
                
                # 设置网格列权重，使卡片等宽
                cards_frame.grid_columnconfigure(0, weight=1)
                cards_frame.grid_columnconfigure(1, weight=1)
                cards_frame.grid_columnconfigure(2, weight=1)
                cards_frame.grid_columnconfigure(3, weight=1)
                
            except Exception as e:
                ttk.Label(result_frame, text=f'获取自定义统计数据失败: {str(e)}', font=('Arial', 16), foreground='red').pack(anchor=tk.CENTER, pady=20)
        
        # 绑定按钮事件
        generate_btn.config(command=generate_stats)
    
    def show_about(self):
        """显示关于窗口"""
        messagebox.showinfo('关于', '考勤管理系统 v1.0\n用于管理个人工时记录系统')
    
    def show_daily_attendance_report(self):
        """显示每日出勤报表"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='每日出勤报表', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 筛选条件
        filter_frame = ttk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(filter_frame, text='日期:').pack(side=tk.LEFT, padx=10)
        
        # 导入日期组件
        from tkcalendar import DateEntry
        self.daily_report_date = DateEntry(filter_frame, width=12, date_pattern='yyyy-MM-dd')
        self.daily_report_date.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(filter_frame, text='生成报表', command=self.generate_daily_attendance_report).pack(side=tk.LEFT, padx=10)
        
        # 操作按钮
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(action_frame, text='修改', command=self.edit_selected_records).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text='批量删除', command=self.delete_selected_records).pack(side=tk.LEFT, padx=10)
        
        # 报表内容
        report_frame = ttk.Frame(self.main_frame)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格
        columns = ('select', 'user_id', 'username', 'shift_type', 'hours', 'is_leave', 'leave_time', 'status')
        self.daily_report_tree = ttk.Treeview(report_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.daily_report_tree.heading('select', text='选择')
        self.daily_report_tree.heading('user_id', text='用户ID')
        self.daily_report_tree.heading('username', text='用户名')
        self.daily_report_tree.heading('shift_type', text='班别')
        self.daily_report_tree.heading('hours', text='时长(小时)')
        self.daily_report_tree.heading('is_leave', text='是否请假')
        self.daily_report_tree.heading('leave_time', text='请假时间')
        self.daily_report_tree.heading('status', text='状态')
        
        # 设置列宽
        self.daily_report_tree.column('select', width=60, anchor=tk.CENTER)
        self.daily_report_tree.column('user_id', width=80, anchor=tk.CENTER)
        self.daily_report_tree.column('username', width=150, anchor=tk.CENTER)
        self.daily_report_tree.column('shift_type', width=100, anchor=tk.CENTER)
        self.daily_report_tree.column('hours', width=100, anchor=tk.CENTER)
        self.daily_report_tree.column('is_leave', width=100, anchor=tk.CENTER)
        self.daily_report_tree.column('leave_time', width=150, anchor=tk.CENTER)
        self.daily_report_tree.column('status', width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.daily_report_tree.yview)
        self.daily_report_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.daily_report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加复选框功能
        self.selected_records = {}
        def on_tree_click(event):
            item = self.daily_report_tree.identify_row(event.y)
            column = self.daily_report_tree.identify_column(event.x)
            if column == '#1':  # 选择列
                if item in self.selected_records:
                    del self.selected_records[item]
                    self.daily_report_tree.set(item, 'select', '□')
                else:
                    self.selected_records[item] = True
                    self.daily_report_tree.set(item, 'select', '☑')
        
        self.daily_report_tree.bind('<ButtonRelease-1>', on_tree_click)
    
    def generate_daily_attendance_report(self):
        """生成每日出勤报表"""
        # 清空现有数据
        for item in self.daily_report_tree.get_children():
            self.daily_report_tree.delete(item)
        
        # 获取日期
        report_date = self.daily_report_date.get()
        if not report_date:
            messagebox.showerror('错误', '请选择日期')
            return
        
        try:
            # 获取当天的所有用户工时记录
            records_response = requests.get(f'{BASE_URL}/time-records/date/{report_date}')
            if records_response.status_code != 200:
                messagebox.showerror('错误', '无法获取工时记录数据')
                return
            time_records = records_response.json()
            
            # 获取所有用户
            users_response = requests.get(f'{BASE_URL}/users')
            if users_response.status_code != 200:
                messagebox.showerror('错误', '无法获取用户列表')
                return
            users = users_response.json()
            
            # 构建工时记录字典
            records_dict = {}
            for record in time_records:
                user_id = record.get('user_id')
                records_dict[user_id] = record
            
            # 生成报表数据
            for user in users:
                user_id = user.get('id')
                username = user.get('username')
                record = records_dict.get(user_id)
                
                if record:
                    shift_type = record.get('shift_type')
                    hours = round(record.get('duration', 0) / 60, 1)  # 转换为小时
                    is_leave = record.get('is_leave', False)
                    is_leave_text = '是' if is_leave else '否'
                    
                    # 处理请假时间
                    start_time = record.get('start_time', '')
                    end_time = record.get('end_time', '')
                    leave_time = ''
                    if is_leave and start_time and end_time:
                        # 提取时间部分，格式化为 HH:MM - HH:MM
                        start_time_str = start_time.split('T')[1].split(':')[0:2]  # 提取小时和分钟
                        end_time_str = end_time.split('T')[1].split(':')[0:2]  # 提取小时和分钟
                        leave_time = f'{start_time_str[0]}:{start_time_str[1]} - {end_time_str[0]}:{end_time_str[1]}'
                    
                    if is_leave:
                        status = '请假'
                    else:
                        status = '已出勤'
                else:
                    shift_type = ''
                    hours = ''
                    is_leave_text = '否'
                    leave_time = ''
                    status = '未出勤'
                
                self.daily_report_tree.insert('', tk.END, values=(
                    '□',  # 选择列，显示为复选框
                    user_id,
                    username,
                    shift_type,
                    hours,
                    is_leave_text,
                    leave_time,
                    status
                ))
        except Exception as e:
            messagebox.showerror('错误', f'生成报表失败: {str(e)}')
    
    def delete_selected_records(self):
        """批量删除选中的记录"""
        # 检查是否有选中的记录
        if not self.selected_records:
            messagebox.showwarning('警告', '请选择要删除的记录')
            return
        
        # 获取当前报表日期
        report_date = self.daily_report_date.get()
        if not report_date:
            messagebox.showerror('错误', '请选择日期')
            return
        
        # 确认删除操作
        if not messagebox.askyesno('确认删除', f'确定要删除选中的记录吗？\n这将删除{report_date}当天的排班和工时记录\n包括请假记录'):
            return
        
        try:
            # 获取选中记录的用户ID
            selected_user_ids = []
            for item in self.selected_records:
                values = self.daily_report_tree.item(item, 'values')
                user_id = values[1]  # 第2列是用户ID
                selected_user_ids.append(int(user_id))  # 确保用户ID是整数类型
            
            # 调用后端API批量安排调休（这里复用了调休API，因为功能逻辑类似）
            api_url = f'{BASE_URL}/arrange-leave'
            print(f"Sending POST request to: {api_url}")
            print(f"Request data: user_ids={selected_user_ids}, dates={[report_date]}")
            response = requests.post(
                api_url,
                headers={'Content-Type': 'application/json'},
                json={
                    'user_ids': selected_user_ids,
                    'dates': [report_date]
                }
            )
            
            # 打印调试信息
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Content: {response.content}")
            
            if response.status_code == 200:
                # 重新生成报表
                self.generate_daily_attendance_report()
                # 清空选中状态
                self.selected_records = {}
                messagebox.showinfo('成功', '批量删除成功')
            else:
                # 处理错误响应，增加容错处理
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', '删除失败')
                except ValueError:
                    # 如果响应不是JSON格式，直接使用响应文本
                    error_message = response.text.strip() or '删除失败，服务器返回非JSON响应'
                messagebox.showerror('错误', f'批量删除失败: {error_message}')
        except Exception as e:
            # 捕获所有异常，提供更详细的错误信息
            import traceback
            error_details = traceback.format_exc()
            print(f"Error details: {error_details}")
            messagebox.showerror('错误', f'批量删除失败: {str(e)}\n\n详细错误: {error_details[:200]}...')
    
    def show_personal_attendance_report(self):
        """显示个人出勤报表"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='个人出勤报表', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 筛选条件
        filter_frame = ttk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 导入日期组件
        from tkcalendar import DateEntry
        
        ttk.Label(filter_frame, text='用户:').pack(side=tk.LEFT, padx=10)
        self.personal_report_user_var = tk.StringVar()
        self.personal_report_user_combo = ttk.Combobox(filter_frame, textvariable=self.personal_report_user_var, width=20)
        self.personal_report_user_combo.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(filter_frame, text='开始日期:').pack(side=tk.LEFT, padx=10)
        self.personal_report_start_date = DateEntry(filter_frame, width=12, date_pattern='yyyy-MM-dd')
        self.personal_report_start_date.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(filter_frame, text='结束日期:').pack(side=tk.LEFT, padx=10)
        self.personal_report_end_date = DateEntry(filter_frame, width=12, date_pattern='yyyy-MM-dd')
        self.personal_report_end_date.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(filter_frame, text='生成报表', command=self.generate_personal_attendance_report).pack(side=tk.LEFT, padx=10)
        
        # 报表内容
        report_frame = ttk.Frame(self.main_frame)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格
        columns = ('date', 'shift_type', 'hours', 'is_leave', 'leave_time', 'status')
        self.personal_report_tree = ttk.Treeview(report_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.personal_report_tree.heading('date', text='日期')
        self.personal_report_tree.heading('shift_type', text='班别')
        self.personal_report_tree.heading('hours', text='时长(小时)')
        self.personal_report_tree.heading('is_leave', text='是否请假')
        self.personal_report_tree.heading('leave_time', text='请假时间')
        self.personal_report_tree.heading('status', text='状态')
        
        # 设置列宽
        self.personal_report_tree.column('date', width=120, anchor=tk.CENTER)
        self.personal_report_tree.column('shift_type', width=100, anchor=tk.CENTER)
        self.personal_report_tree.column('hours', width=100, anchor=tk.CENTER)
        self.personal_report_tree.column('is_leave', width=100, anchor=tk.CENTER)
        self.personal_report_tree.column('leave_time', width=150, anchor=tk.CENTER)
        self.personal_report_tree.column('status', width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.personal_report_tree.yview)
        self.personal_report_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.personal_report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载用户数据到下拉选择框
        self.load_users_for_personal_report()
    
    def load_users_for_personal_report(self):
        """加载用户数据到个人出勤报表的下拉选择框"""
        try:
            response = requests.get(f'{BASE_URL}/users')
            if response.status_code == 200:
                users = response.json()
                # 设置下拉选项
                self.personal_report_user_combo['values'] = [f"{user.get('id')} - {user.get('username')}" for user in users]
                if users:
                    self.personal_report_user_combo.current(0)  # 默认选择第一个用户
        except Exception as e:
            print(f'加载用户数据失败: {str(e)}')
    
    def generate_personal_attendance_report(self):
        """生成个人出勤报表"""
        # 清空现有数据
        for item in self.personal_report_tree.get_children():
            self.personal_report_tree.delete(item)
        
        # 获取筛选条件
        user_text = self.personal_report_user_var.get()
        if not user_text:
            messagebox.showerror('错误', '请选择用户')
            return
        
        start_date = self.personal_report_start_date.get()
        end_date = self.personal_report_end_date.get()
        if not start_date or not end_date:
            messagebox.showerror('错误', '请选择开始日期和结束日期')
            return
        
        # 提取用户ID
        user_id = user_text.split(' - ')[0]
        
        try:
            # 获取该用户在日期范围内的工时记录
            records_response = requests.get(f'{BASE_URL}/time-records/user/{user_id}/range?start_date={start_date}&end_date={end_date}')
            if records_response.status_code != 200:
                messagebox.showerror('错误', '无法获取工时记录数据')
                return
            time_records = records_response.json()
            
            # 构建工时记录字典
            records_dict = {}
            for record in time_records:
                # 提取日期
                record_date = record.get('start_time').split('T')[0]
                records_dict[record_date] = record
            
            # 生成日期范围内的所有日期
            import datetime
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            delta = datetime.timedelta(days=1)
            
            # 生成报表数据
            current_date = start
            while current_date <= end:
                date_str = current_date.strftime('%Y-%m-%d')
                record = records_dict.get(date_str)
                
                if record:
                    shift_type = record.get('shift_type')
                    hours = round(record.get('duration', 0) / 60, 1)  # 转换为小时
                    is_leave = record.get('is_leave', False)
                    is_leave_text = '是' if is_leave else '否'
                    
                    # 处理请假时间
                    start_time = record.get('start_time', '')
                    end_time = record.get('end_time', '')
                    leave_time = ''
                    if is_leave and start_time and end_time:
                        # 提取时间部分，格式化为 HH:MM - HH:MM
                        start_time_str = start_time.split('T')[1].split(':')[0:2]  # 提取小时和分钟
                        end_time_str = end_time.split('T')[1].split(':')[0:2]  # 提取小时和分钟
                        leave_time = f'{start_time_str[0]}:{start_time_str[1]} - {end_time_str[0]}:{end_time_str[1]}'
                    
                    if is_leave:
                        status = '请假'
                    else:
                        status = '已出勤'
                else:
                    shift_type = ''
                    hours = ''
                    is_leave_text = '否'
                    leave_time = ''
                    status = '未出勤'
                
                self.personal_report_tree.insert('', tk.END, values=(
                    date_str,
                    shift_type,
                    hours,
                    is_leave_text,
                    leave_time,
                    status
                ))
                
                current_date += delta
        except Exception as e:
            messagebox.showerror('错误', f'生成报表失败: {str(e)}')
    
    def show_copy_time_records_window(self):
        """显示批量复制工时记录窗口"""
        # 创建弹窗
        copy_window = tk.Toplevel(self.root)
        copy_window.title('批量复制工时记录')
        copy_window.geometry('500x300')
        copy_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(copy_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 源日期
        ttk.Label(form_frame, text='源日期:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        from tkcalendar import DateEntry
        self.copy_source_date = DateEntry(form_frame, width=12, date_pattern='yyyy-MM-dd')
        self.copy_source_date.grid(row=0, column=1, padx=10, pady=10)
        
        # 目标开始日期
        ttk.Label(form_frame, text='目标开始日期:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.copy_target_start_date = DateEntry(form_frame, width=12, date_pattern='yyyy-MM-dd')
        self.copy_target_start_date.grid(row=1, column=1, padx=10, pady=10)
        
        # 目标结束日期
        ttk.Label(form_frame, text='目标结束日期:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.copy_target_end_date = DateEntry(form_frame, width=12, date_pattern='yyyy-MM-dd')
        self.copy_target_end_date.grid(row=2, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def copy_records():
            """执行复制记录操作"""
            source_date = self.copy_source_date.get()
            target_start_date = self.copy_target_start_date.get()
            target_end_date = self.copy_target_end_date.get()
            
            if not source_date or not target_start_date or not target_end_date:
                messagebox.showerror('错误', '请填写完整的日期信息')
                return
            
            try:
                response = requests.post(f'{BASE_URL}/time-records/copy', json={
                    'source_date': source_date,
                    'target_start_date': target_start_date,
                    'target_end_date': target_end_date
                })
                
                if response.status_code == 200:
                    messagebox.showinfo('成功', response.json().get('message', '复制成功'))
                    copy_window.destroy()
                    # 刷新报表
                    self.generate_daily_attendance_report()
                else:
                    messagebox.showerror('错误', response.json().get('error', '复制失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='复制记录', command=copy_records).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text='取消', command=copy_window.destroy).grid(row=0, column=1, padx=10)
    
    def logout(self):
        """退出登录"""
        if os.path.exists(LOGIN_FILE):
            os.remove(LOGIN_FILE)
        self.logged_in = False
        self.admin_info = None
        self.token = None
        self.show_login_window()
    
    def exit_app(self):
        """退出应用"""
        self.root.destroy()
    
    # 权限管理相关方法
    def show_permission_management(self):
        """显示权限管理界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='权限管理', font=('Arial', 24)).pack(side=tk.LEFT)
        ttk.Button(title_frame, text='新增权限', command=self.show_add_permission_window).pack(side=tk.RIGHT)
        
        # 权限列表
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格
        columns = ('id', 'name', 'description', 'actions')
        self.permission_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.permission_tree.heading('id', text='ID')
        self.permission_tree.heading('name', text='权限名称')
        self.permission_tree.heading('description', text='描述')
        self.permission_tree.heading('actions', text='操作')
        
        # 设置列宽
        self.permission_tree.column('id', width=50, anchor=tk.CENTER)
        self.permission_tree.column('name', width=150, anchor=tk.CENTER)
        self.permission_tree.column('description', width=300, anchor=tk.CENTER)
        self.permission_tree.column('actions', width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.permission_tree.yview)
        self.permission_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.permission_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载权限数据
        self.load_permissions()
    
    def load_permissions(self):
        """加载权限数据"""
        # 清空现有数据
        for item in self.permission_tree.get_children():
            self.permission_tree.delete(item)
        
        try:
            response = requests.get(f'{BASE_URL}/permissions')
            if response.status_code == 200:
                permissions = response.json()
                for permission in permissions:
                    # 添加操作按钮
                    actions = f"编辑 | 删除"
                    self.permission_tree.insert('', tk.END, values=(
                        permission.get('id'),
                        permission.get('name'),
                        permission.get('description'),
                        actions
                    ))
                
                # 添加点击事件处理
                self.permission_tree.bind('<ButtonRelease-1>', self.on_permission_tree_click)
            else:
                messagebox.showerror('错误', '无法获取权限列表')
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def on_permission_tree_click(self, event):
        """处理权限列表点击事件"""
        # 获取点击的行和列
        item = self.permission_tree.identify_row(event.y)
        column = self.permission_tree.identify_column(event.x)
        
        # 如果点击了操作列
        if column == '#4':  # actions列
            # 获取行数据
            values = self.permission_tree.item(item, 'values')
            if values:
                permission_id = values[0]
                # 获取点击位置的x坐标
                x, y, width, height = self.permission_tree.bbox(item, column)
                # 判断点击的是编辑还是删除按钮
                if event.x - x < width / 2:
                    # 编辑按钮
                    self.edit_permission(permission_id)
                else:
                    # 删除按钮
                    self.delete_permission(permission_id)
    
    def show_add_permission_window(self):
        """显示添加权限窗口"""
        # 创建弹窗
        add_window = tk.Toplevel(self.root)
        add_window.title('新增权限')
        add_window.geometry('500x300')
        add_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(add_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 权限名称
        ttk.Label(form_frame, text='权限名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_permission_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_permission_name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.NE)
        self.new_permission_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_permission_desc_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def save_permission():
            """保存权限"""
            name = self.new_permission_name_var.get()
            description = self.new_permission_desc_var.get()
            
            if not name:
                messagebox.showerror('错误', '权限名称不能为空')
                return
            
            try:
                response = requests.post(f'{BASE_URL}/permissions', json={
                    'name': name,
                    'description': description
                })
                
                if response.status_code == 201:
                    messagebox.showinfo('成功', '权限添加成功')
                    add_window.destroy()
                    self.load_permissions()  # 刷新权限列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '添加权限失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_permission).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=add_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_permission(self, permission_id):
        """编辑权限"""
        # 获取权限详情
        try:
            response = requests.get(f'{BASE_URL}/permissions/{permission_id}')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取权限详情')
                return
            permission = response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title('编辑权限')
        edit_window.geometry('500x300')
        edit_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 权限名称
        ttk.Label(form_frame, text='权限名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_permission_name_var = tk.StringVar(value=permission.get('name'))
        ttk.Entry(form_frame, textvariable=self.edit_permission_name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.NE)
        self.edit_permission_desc_var = tk.StringVar(value=permission.get('description'))
        ttk.Entry(form_frame, textvariable=self.edit_permission_desc_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def save_edited_permission():
            """保存编辑后的权限"""
            name = self.edit_permission_name_var.get()
            description = self.edit_permission_desc_var.get()
            
            if not name:
                messagebox.showerror('错误', '权限名称不能为空')
                return
            
            try:
                response = requests.put(f'{BASE_URL}/permissions/{permission_id}', json={
                    'name': name,
                    'description': description
                })
                
                if response.status_code == 200:
                    messagebox.showinfo('成功', '权限编辑成功')
                    edit_window.destroy()
                    self.load_permissions()  # 刷新权限列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '编辑权限失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_edited_permission).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_permission(self, permission_id):
        """删除权限"""
        if messagebox.askyesno('确认', f'确定要删除ID为 {permission_id} 的权限吗？'):
            try:
                response = requests.delete(f'{BASE_URL}/permissions/{permission_id}')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '权限删除成功')
                    self.load_permissions()  # 刷新权限列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '删除权限失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    # 角色管理相关方法
    def show_role_management(self):
        """显示角色管理界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='角色管理', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 顶部按钮组
        button_group = ttk.Frame(title_frame)
        button_group.pack(side=tk.RIGHT)
        
        ttk.Button(button_group, text='新增角色', command=self.show_add_role_window).pack(side=tk.LEFT, padx=5)
        self.edit_role_btn = ttk.Button(button_group, text='编辑', command=self.edit_selected_role, state=tk.DISABLED)
        self.edit_role_btn.pack(side=tk.LEFT, padx=5)
        self.delete_role_btn = ttk.Button(button_group, text='删除', command=self.delete_selected_role, state=tk.DISABLED)
        self.delete_role_btn.pack(side=tk.LEFT, padx=5)
        self.assign_role_btn = ttk.Button(button_group, text='分配用户', command=self.assign_users_to_selected_role, state=tk.DISABLED)
        self.assign_role_btn.pack(side=tk.LEFT, padx=5)
        
        # 角色列表
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格 - 添加选择框列，只能单选
        columns = ('select', 'id', 'name', 'description')
        self.role_tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode=tk.BROWSE)
        
        # 设置列标题
        self.role_tree.heading('select', text='选择')
        self.role_tree.heading('id', text='ID')
        self.role_tree.heading('name', text='角色名称')
        self.role_tree.heading('description', text='描述')
        
        # 设置列宽
        self.role_tree.column('select', width=60, anchor=tk.CENTER)
        self.role_tree.column('id', width=50, anchor=tk.CENTER)
        self.role_tree.column('name', width=150, anchor=tk.CENTER)
        self.role_tree.column('description', width=300, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.role_tree.yview)
        self.role_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.role_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加选择事件处理
        self.role_tree.bind('<<TreeviewSelect>>', self.on_role_select)
        
        # 加载角色数据
        self.load_roles()
    
    def load_roles(self):
        """加载角色数据"""
        # 清空现有数据
        for item in self.role_tree.get_children():
            self.role_tree.delete(item)
        
        try:
            response = requests.get(f'{BASE_URL}/roles')
            if response.status_code == 200:
                roles = response.json()
                for role in roles:
                    # 添加单选框标记
                    select_mark = '○'
                    self.role_tree.insert('', tk.END, values=(
                        select_mark,
                        role.get('id'),
                        role.get('name'),
                        role.get('description')
                    ))
            else:
                messagebox.showerror('错误', '无法获取角色列表')
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def on_role_select(self, event):
        """处理角色选择事件"""
        # 获取选中的项目
        selected_items = self.role_tree.selection()
        if selected_items:
            # 启用按钮
            self.edit_role_btn['state'] = tk.NORMAL
            self.delete_role_btn['state'] = tk.NORMAL
            self.assign_role_btn['state'] = tk.NORMAL
            # 更新选中行的单选框标记
            for item in self.role_tree.get_children():
                values = self.role_tree.item(item, 'values')
                if values:
                    if item in selected_items:
                        # 选中行显示选中标记
                        self.role_tree.item(item, values=('●', values[1], values[2], values[3]))
                    else:
                        # 未选中行显示未选中标记
                        self.role_tree.item(item, values=('○', values[1], values[2], values[3]))
        else:
            # 禁用按钮
            self.edit_role_btn['state'] = tk.DISABLED
            self.delete_role_btn['state'] = tk.DISABLED
            self.assign_role_btn['state'] = tk.DISABLED
    
    def edit_selected_role(self):
        """编辑选中的角色"""
        selected_items = self.role_tree.selection()
        if selected_items:
            item = selected_items[0]
            values = self.role_tree.item(item, 'values')
            if values:
                role_id = values[1]
                self.edit_role(role_id)
    
    def delete_selected_role(self):
        """删除选中的角色"""
        selected_items = self.role_tree.selection()
        if selected_items:
            item = selected_items[0]
            values = self.role_tree.item(item, 'values')
            if values:
                role_id = values[1]
                self.delete_role(role_id)
    
    def assign_users_to_selected_role(self):
        """分配用户给选中的角色"""
        selected_items = self.role_tree.selection()
        if selected_items:
            item = selected_items[0]
            values = self.role_tree.item(item, 'values')
            if values:
                role_id = values[1]
                self.assign_users_to_role(role_id)
    
    def show_add_role_window(self):
        """显示添加角色窗口"""
        # 创建弹窗
        add_window = tk.Toplevel(self.root)
        add_window.title('新增角色')
        add_window.geometry('500x300')
        add_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(add_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 角色名称
        ttk.Label(form_frame, text='角色名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_role_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_role_name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.NE)
        self.new_role_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_role_desc_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def save_role():
            """保存角色"""
            name = self.new_role_name_var.get()
            description = self.new_role_desc_var.get()
            
            if not name:
                messagebox.showerror('错误', '角色名称不能为空')
                return
            
            try:
                response = requests.post(f'{BASE_URL}/roles', json={
                    'name': name,
                    'description': description
                })
                
                if response.status_code == 201:
                    messagebox.showinfo('成功', '角色添加成功')
                    add_window.destroy()
                    self.load_roles()  # 刷新角色列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '添加角色失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_role).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=add_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_role(self, role_id):
        """编辑角色"""
        # 获取角色详情
        try:
            response = requests.get(f'{BASE_URL}/roles/{role_id}')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取角色详情')
                return
            role = response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title('编辑角色')
        edit_window.geometry('500x300')
        edit_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 角色名称
        ttk.Label(form_frame, text='角色名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_role_name_var = tk.StringVar(value=role.get('name'))
        ttk.Entry(form_frame, textvariable=self.edit_role_name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.NE)
        self.edit_role_desc_var = tk.StringVar(value=role.get('description'))
        ttk.Entry(form_frame, textvariable=self.edit_role_desc_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def save_edited_role():
            """保存编辑后的角色"""
            name = self.edit_role_name_var.get()
            description = self.edit_role_desc_var.get()
            
            if not name:
                messagebox.showerror('错误', '角色名称不能为空')
                return
            
            try:
                response = requests.put(f'{BASE_URL}/roles/{role_id}', json={
                    'name': name,
                    'description': description
                })
                
                if response.status_code == 200:
                    messagebox.showinfo('成功', '角色编辑成功')
                    edit_window.destroy()
                    self.load_roles()  # 刷新角色列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '编辑角色失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_edited_role).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_role(self, role_id):
        """删除角色"""
        if messagebox.askyesno('确认', f'确定要删除ID为 {role_id} 的角色吗？'):
            try:
                response = requests.delete(f'{BASE_URL}/roles/{role_id}')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '角色删除成功')
                    self.load_roles()  # 刷新角色列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '删除角色失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def assign_users_to_role(self, role_id):
        """分配用户给角色"""
        # 获取角色详情
        try:
            role_response = requests.get(f'{BASE_URL}/roles/{role_id}')
            if role_response.status_code != 200:
                messagebox.showerror('错误', '无法获取角色详情')
                return
            role = role_response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 获取所有用户
        try:
            users_response = requests.get(f'{BASE_URL}/users')
            if users_response.status_code != 200:
                messagebox.showerror('错误', '无法获取用户列表')
                return
            users = users_response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 创建分配用户窗口
        assign_window = tk.Toplevel(self.root)
        assign_window.title(f'分配用户给角色 - {role.get('name')}')
        assign_window.geometry('600x500')
        assign_window.resizable(False, False)
        
        # 标题
        title_frame = ttk.Frame(assign_window, padding=20)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text=f'分配用户给角色: {role.get('name')}', font=('Arial', 18)).pack()
        
        # 用户列表框架
        list_frame = ttk.Frame(assign_window, padding=20)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动框架
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建用户选择变量字典
        user_vars = {}
        
        # 显示用户列表
        ttk.Label(scrollable_frame, text='选择要分配给该角色的用户:').pack(anchor=tk.W, pady=10)
        
        # 获取所有用户的角色信息
        user_roles_dict = {}
        try:
            for user in users:
                user_id = user.get('id')
                # 获取用户的所有角色
                roles_response = requests.get(f'{BASE_URL}/users/{user_id}/roles')
                if roles_response.status_code == 200:
                    user_roles = roles_response.json()
                    user_roles_dict[user_id] = [role.get('name') for role in user_roles]
                else:
                    user_roles_dict[user_id] = []
        except Exception as e:
            messagebox.showerror('错误', f'获取用户角色信息失败: {str(e)}')
            return
        
        for user in users:
            user_id = user.get('id')
            user_var = tk.BooleanVar()
            # 检查用户当前是否已分配该角色
            user_roles = user_roles_dict.get(user_id, [])
            if role.get('name') in user_roles:
                user_var.set(True)
            user_vars[user_id] = user_var
            
            # 创建复选框，显示用户的所有角色
            checkbox = ttk.Checkbutton(
                scrollable_frame,
                text=f"{user.get('id')} - {user.get('username')} (当前角色: {', '.join(user_roles) if user_roles else '无'})",
                variable=user_var
            )
            checkbox.pack(anchor=tk.W, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(assign_window, padding=20)
        button_frame.pack(fill=tk.X)
        
        def save_assignments():
            """保存用户角色分配"""
            try:
                # 更新每个用户的角色分配
                for user_id, var in user_vars.items():
                    # 获取用户当前的所有角色
                    current_roles = user_roles_dict.get(user_id, [])
                    
                    if var.get():
                        # 如果用户未分配该角色，则添加
                        if role.get('name') not in current_roles:
                            # 获取所有角色ID
                            all_roles_response = requests.get(f'{BASE_URL}/roles')
                            if all_roles_response.status_code == 200:
                                all_roles = all_roles_response.json()
                                role_id_map = {r.get('name'): r.get('id') for r in all_roles}
                                
                                # 构建角色ID列表
                                new_role_ids = [role_id_map[r] for r in current_roles]
                                new_role_ids.append(role_id)
                                
                                # 分配角色
                                response = requests.post(f'{BASE_URL}/users/{user_id}/roles', json={
                                    'role_ids': new_role_ids
                                })
                                if response.status_code != 200:
                                    messagebox.showerror('错误', f'更新用户 {user_id} 角色失败')
                                    return
                    else:
                        # 如果用户已分配该角色，则移除
                        if role.get('name') in current_roles:
                            # 获取所有角色ID
                            all_roles_response = requests.get(f'{BASE_URL}/roles')
                            if all_roles_response.status_code == 200:
                                all_roles = all_roles_response.json()
                                role_id_map = {r.get('name'): r.get('id') for r in all_roles}
                                
                                # 构建角色ID列表，移除当前角色
                                new_role_ids = [role_id_map[r] for r in current_roles if r != role.get('name')]
                                
                                # 分配角色
                                response = requests.post(f'{BASE_URL}/users/{user_id}/roles', json={
                                    'role_ids': new_role_ids
                                })
                                if response.status_code != 200:
                                    messagebox.showerror('错误', f'更新用户 {user_id} 角色失败')
                                    return
                
                messagebox.showinfo('成功', '用户角色分配成功')
                assign_window.destroy()
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_assignments).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=assign_window.destroy).pack(side=tk.LEFT, padx=10)
    
    # 角色权限分配相关方法
    def show_role_permission_assignment(self):
        """显示角色权限分配界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        ttk.Label(title_frame, text='角色权限分配', font=('Arial', 24)).pack()
        
        # 角色选择
        select_frame = ttk.Frame(self.main_frame)
        select_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(select_frame, text='选择角色:').pack(side=tk.LEFT, padx=10)
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(select_frame, textvariable=self.role_var, width=30)
        self.role_combo.pack(side=tk.LEFT, padx=10)
        
        # 加载角色数据
        self.load_roles_for_permission_assignment()
        
        # 权限列表
        permissions_frame = ttk.Frame(self.main_frame)
        permissions_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 权限列表标题
        ttk.Label(permissions_frame, text='权限列表', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
        
        # 权限列表
        self.permissions_listbox = tk.Listbox(permissions_frame, selectmode=tk.MULTIPLE, width=80, height=20)
        self.permissions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(permissions_frame, orient=tk.VERTICAL, command=self.permissions_listbox.yview)
        self.permissions_listbox.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 分配按钮
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text='分配权限', command=self.assign_permissions).pack(side=tk.RIGHT, padx=10)
        
        # 绑定角色选择事件
        self.role_combo.bind('<<ComboboxSelected>>', self.on_role_selected)
    
    def load_roles_for_permission_assignment(self):
        """加载角色数据用于权限分配"""
        try:
            response = requests.get(f'{BASE_URL}/roles')
            if response.status_code == 200:
                roles = response.json()
                self.role_combo['values'] = [f"{role.get('id')} - {role.get('name')}" for role in roles]
                if roles:
                    self.role_combo.current(0)
                    # 加载默认角色的权限
                    self.on_role_selected(None)
        except Exception as e:
            messagebox.showerror('错误', f'加载角色数据失败: {str(e)}')
    
    def on_role_selected(self, event):
        """角色选择事件处理"""
        role_text = self.role_var.get()
        if role_text:
            role_id = role_text.split(' - ')[0]
            self.load_permissions_for_role(role_id)
    
    def load_permissions_for_role(self, role_id):
        """加载角色的权限"""
        # 清空权限列表
        self.permissions_listbox.delete(0, tk.END)
        
        try:
            # 获取所有权限
            response = requests.get(f'{BASE_URL}/permissions')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取权限列表')
                return
            all_permissions = response.json()
            
            # 获取角色的权限
            response = requests.get(f'{BASE_URL}/roles/{role_id}/permissions')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取角色权限')
                return
            role_permissions = response.json()
            
            # 提取角色权限ID列表
            role_permission_ids = [str(permission.get('id')) for permission in role_permissions]
            
            # 填充权限列表
            self.permissions_dict = {}
            for permission in all_permissions:
                permission_id = str(permission.get('id'))
                permission_name = permission.get('name')
                permission_desc = permission.get('description')
                self.permissions_listbox.insert(tk.END, f"{permission_id} - {permission_name} ({permission_desc})")
                self.permissions_dict[permission_name] = permission_id
                
                # 如果是角色的权限，选中它
                if permission_id in role_permission_ids:
                    self.permissions_listbox.select_set(self.permissions_listbox.size() - 1)
        except Exception as e:
            messagebox.showerror('错误', f'加载权限数据失败: {str(e)}')
    
    def assign_permissions(self):
        """分配权限给角色"""
        role_text = self.role_var.get()
        if not role_text:
            messagebox.showerror('错误', '请选择角色')
            return
        
        role_id = role_text.split(' - ')[0]
        
        # 获取选中的权限
        selected_indices = self.permissions_listbox.curselection()
        selected_permissions = [self.permissions_listbox.get(index) for index in selected_indices]
        
        # 提取权限ID
        permission_ids = []
        for permission in selected_permissions:
            permission_id = permission.split(' - ')[0]
            permission_ids.append(int(permission_id))
        
        try:
            response = requests.post(f'{BASE_URL}/roles/{role_id}/permissions', json={
                'permission_ids': permission_ids
            })
            
            if response.status_code == 200:
                messagebox.showinfo('成功', '权限分配成功')
            else:
                messagebox.showerror('错误', response.json().get('error', '权限分配失败'))
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    # 管理员角色分配相关方法
    def show_admin_role_assignment(self):
        """显示管理员角色分配界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        ttk.Label(title_frame, text='管理员角色分配', font=('Arial', 24)).pack()
        
        # 管理员选择
        select_frame = ttk.Frame(self.main_frame)
        select_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(select_frame, text='选择管理员:').pack(side=tk.LEFT, padx=10)
        self.admin_var = tk.StringVar()
        self.admin_combo = ttk.Combobox(select_frame, textvariable=self.admin_var, width=30)
        self.admin_combo.pack(side=tk.LEFT, padx=10)
        
        # 加载管理员数据
        self.load_admins_for_role_assignment()
        
        # 角色列表
        roles_frame = ttk.Frame(self.main_frame)
        roles_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 角色列表标题
        ttk.Label(roles_frame, text='角色列表', font=('Arial', 16)).pack(anchor=tk.W, pady=10)
        
        # 角色列表
        self.roles_listbox = tk.Listbox(roles_frame, selectmode=tk.MULTIPLE, width=80, height=20)
        self.roles_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(roles_frame, orient=tk.VERTICAL, command=self.roles_listbox.yview)
        self.roles_listbox.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 分配按钮
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text='分配角色', command=self.assign_roles).pack(side=tk.RIGHT, padx=10)
        
        # 绑定管理员选择事件
        self.admin_combo.bind('<<ComboboxSelected>>', self.on_admin_selected)
    
    def load_admins_for_role_assignment(self):
        """加载管理员数据用于角色分配"""
        try:
            response = requests.get(f'{BASE_URL}/admins')
            if response.status_code == 200:
                admins = response.json()
                self.admin_combo['values'] = [f"{admin.get('id')} - {admin.get('username')}" for admin in admins]
                if admins:
                    self.admin_combo.current(0)
                    # 加载默认管理员的角色
                    self.on_admin_selected(None)
        except Exception as e:
            messagebox.showerror('错误', f'加载管理员数据失败: {str(e)}')
    
    def on_admin_selected(self, event):
        """管理员选择事件处理"""
        admin_text = self.admin_var.get()
        if admin_text:
            admin_id = admin_text.split(' - ')[0]
            self.load_roles_for_admin(admin_id)
    
    def load_roles_for_admin(self, admin_id):
        """加载管理员的角色"""
        # 清空角色列表
        self.roles_listbox.delete(0, tk.END)
        
        try:
            # 获取所有角色
            response = requests.get(f'{BASE_URL}/roles')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取角色列表')
                return
            all_roles = response.json()
            
            # 获取管理员的角色
            response = requests.get(f'{BASE_URL}/admins/{admin_id}/roles')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取管理员角色')
                return
            admin_roles = response.json()
            
            # 提取管理员角色ID列表
            admin_role_ids = [str(role.get('id')) for role in admin_roles]
            
            # 填充角色列表
            self.roles_dict = {}
            for role in all_roles:
                role_id = str(role.get('id'))
                role_name = role.get('name')
                role_desc = role.get('description')
                self.roles_listbox.insert(tk.END, f"{role_id} - {role_name} ({role_desc})")
                self.roles_dict[role_name] = role_id
                
                # 如果是管理员的角色，选中它
                if role_id in admin_role_ids:
                    self.roles_listbox.select_set(self.roles_listbox.size() - 1)
        except Exception as e:
            messagebox.showerror('错误', f'加载角色数据失败: {str(e)}')
    
    def assign_roles(self):
        """分配角色给管理员"""
        admin_text = self.admin_var.get()
        if not admin_text:
            messagebox.showerror('错误', '请选择管理员')
            return
        
        admin_id = admin_text.split(' - ')[0]
        
        # 获取选中的角色
        selected_indices = self.roles_listbox.curselection()
        selected_roles = [self.roles_listbox.get(index) for index in selected_indices]
        
        # 提取角色ID
        role_ids = []
        for role in selected_roles:
            role_id = role.split(' - ')[0]
            role_ids.append(int(role_id))
        
        try:
            response = requests.post(f'{BASE_URL}/admins/{admin_id}/roles', json={
                'role_ids': role_ids
            })
            
            if response.status_code == 200:
                messagebox.showinfo('成功', '角色分配成功')
            else:
                messagebox.showerror('错误', response.json().get('error', '角色分配失败'))
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    # 模块管理相关方法
    def show_module_management(self):
        """显示模块管理界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='模块管理', font=('Arial', 24)).pack(side=tk.LEFT)
        ttk.Button(title_frame, text='新增模块', command=self.show_add_module_window).pack(side=tk.RIGHT)
        
        # 模块列表
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格
        columns = ('id', 'name', 'description', 'path', 'parent_id', 'actions')
        self.module_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.module_tree.heading('id', text='ID')
        self.module_tree.heading('name', text='模块名称')
        self.module_tree.heading('description', text='描述')
        self.module_tree.heading('path', text='路径')
        self.module_tree.heading('parent_id', text='父模块ID')
        self.module_tree.heading('actions', text='操作')
        
        # 设置列宽
        self.module_tree.column('id', width=50, anchor=tk.CENTER)
        self.module_tree.column('name', width=150, anchor=tk.CENTER)
        self.module_tree.column('description', width=200, anchor=tk.CENTER)
        self.module_tree.column('path', width=150, anchor=tk.CENTER)
        self.module_tree.column('parent_id', width=100, anchor=tk.CENTER)
        self.module_tree.column('actions', width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.module_tree.yview)
        self.module_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.module_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载模块数据
        self.load_modules()
    
    def load_modules(self):
        """加载模块数据"""
        # 清空现有数据
        for item in self.module_tree.get_children():
            self.module_tree.delete(item)
        
        try:
            response = requests.get(f'{BASE_URL}/modules')
            if response.status_code == 200:
                modules = response.json()
                for module in modules:
                    # 添加操作按钮
                    actions = f"编辑 | 删除"
                    self.module_tree.insert('', tk.END, values=(
                        module.get('id'),
                        module.get('name'),
                        module.get('description'),
                        module.get('path'),
                        module.get('parent_id'),
                        actions
                    ))
                
                # 添加点击事件处理
                self.module_tree.bind('<ButtonRelease-1>', self.on_module_tree_click)
            else:
                messagebox.showerror('错误', '无法获取模块列表')
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def on_module_tree_click(self, event):
        """处理模块列表点击事件"""
        # 获取点击的行和列
        item = self.module_tree.identify_row(event.y)
        column = self.module_tree.identify_column(event.x)
        
        # 如果点击了操作列
        if column == '#6':  # actions列
            # 获取行数据
            values = self.module_tree.item(item, 'values')
            if values:
                module_id = values[0]
                # 获取点击位置的x坐标
                x, y, width, height = self.module_tree.bbox(item, column)
                # 判断点击的是编辑还是删除按钮
                if event.x - x < width / 2:
                    # 编辑按钮
                    self.edit_module(module_id)
                else:
                    # 删除按钮
                    self.delete_module(module_id)
    
    def show_add_module_window(self):
        """显示添加模块窗口"""
        # 创建弹窗
        add_window = tk.Toplevel(self.root)
        add_window.title('新增模块')
        add_window.geometry('600x400')
        add_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(add_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 模块名称
        ttk.Label(form_frame, text='模块名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_module_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_module_name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.NE)
        self.new_module_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_module_desc_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 路径
        ttk.Label(form_frame, text='路径:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_module_path_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_module_path_var, width=30).grid(row=2, column=1, padx=10, pady=10)
        
        # 父模块ID
        ttk.Label(form_frame, text='父模块ID:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_module_parent_id_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_module_parent_id_var, width=30).grid(row=3, column=1, padx=10, pady=10)
        ttk.Label(form_frame, text='（留空表示顶级模块）').grid(row=3, column=2, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        def save_module():
            """保存模块"""
            name = self.new_module_name_var.get()
            description = self.new_module_desc_var.get()
            path = self.new_module_path_var.get()
            parent_id = self.new_module_parent_id_var.get()
            
            if not name:
                messagebox.showerror('错误', '模块名称不能为空')
                return
            
            # 处理父模块ID
            parent_id = int(parent_id) if parent_id else None
            
            try:
                response = requests.post(f'{BASE_URL}/modules', json={
                    'name': name,
                    'description': description,
                    'path': path,
                    'parent_id': parent_id
                })
                
                if response.status_code == 201:
                    messagebox.showinfo('成功', '模块添加成功')
                    add_window.destroy()
                    self.load_modules()  # 刷新模块列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '添加模块失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_module).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=add_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_module(self, module_id):
        """编辑模块"""
        # 获取模块详情
        try:
            response = requests.get(f'{BASE_URL}/modules/{module_id}')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取模块详情')
                return
            module = response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title('编辑模块')
        edit_window.geometry('600x400')
        edit_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 模块名称
        ttk.Label(form_frame, text='模块名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_module_name_var = tk.StringVar(value=module.get('name'))
        ttk.Entry(form_frame, textvariable=self.edit_module_name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 描述
        ttk.Label(form_frame, text='描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.NE)
        self.edit_module_desc_var = tk.StringVar(value=module.get('description'))
        ttk.Entry(form_frame, textvariable=self.edit_module_desc_var, width=30).grid(row=1, column=1, padx=10, pady=10)
        
        # 路径
        ttk.Label(form_frame, text='路径:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_module_path_var = tk.StringVar(value=module.get('path'))
        ttk.Entry(form_frame, textvariable=self.edit_module_path_var, width=30).grid(row=2, column=1, padx=10, pady=10)
        
        # 父模块ID
        ttk.Label(form_frame, text='父模块ID:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_module_parent_id_var = tk.StringVar(value=str(module.get('parent_id')) if module.get('parent_id') else '')
        ttk.Entry(form_frame, textvariable=self.edit_module_parent_id_var, width=30).grid(row=3, column=1, padx=10, pady=10)
        ttk.Label(form_frame, text='（留空表示顶级模块）').grid(row=3, column=2, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        def save_edited_module():
            """保存编辑后的模块"""
            name = self.edit_module_name_var.get()
            description = self.edit_module_desc_var.get()
            path = self.edit_module_path_var.get()
            parent_id = self.edit_module_parent_id_var.get()
            
            if not name:
                messagebox.showerror('错误', '模块名称不能为空')
                return
            
            # 处理父模块ID
            parent_id = int(parent_id) if parent_id else None
            
            try:
                response = requests.put(f'{BASE_URL}/modules/{module_id}', json={
                    'name': name,
                    'description': description,
                    'path': path,
                    'parent_id': parent_id
                })
                
                if response.status_code == 200:
                    messagebox.showinfo('成功', '模块编辑成功')
                    edit_window.destroy()
                    self.load_modules()  # 刷新模块列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '编辑模块失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_edited_module).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_module(self, module_id):
        """删除模块"""
        if messagebox.askyesno('确认', f'确定要删除ID为 {module_id} 的模块吗？'):
            try:
                response = requests.delete(f'{BASE_URL}/modules/{module_id}')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '模块删除成功')
                    self.load_modules()  # 刷新模块列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '删除模块失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    # 操作日志相关方法
    def show_operation_logs(self):
        """显示操作日志界面"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        ttk.Label(title_frame, text='操作日志', font=('Arial', 24)).pack()
        
        # 筛选条件
        filter_frame = ttk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(filter_frame, text='筛选条件:').pack(side=tk.LEFT, padx=10)
        
        # 模块筛选
        ttk.Label(filter_frame, text='模块:').pack(side=tk.LEFT, padx=10)
        self.log_module_var = tk.StringVar()
        self.log_module_entry = ttk.Entry(filter_frame, textvariable=self.log_module_var, width=20)
        self.log_module_entry.pack(side=tk.LEFT, padx=10)
        
        # 操作筛选
        ttk.Label(filter_frame, text='操作:').pack(side=tk.LEFT, padx=10)
        self.log_action_var = tk.StringVar()
        self.log_action_entry = ttk.Entry(filter_frame, textvariable=self.log_action_var, width=20)
        self.log_action_entry.pack(side=tk.LEFT, padx=10)
        
        # 筛选按钮
        ttk.Button(filter_frame, text='筛选', command=self.load_operation_logs).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text='重置', command=self.reset_log_filters).pack(side=tk.LEFT, padx=10)
        
        # 操作日志列表
        logs_frame = ttk.Frame(self.main_frame)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 表格
        columns = ('id', 'admin_id', 'module', 'action', 'target_id', 'target_type', 'details', 'ip_address', 'created_at')
        self.logs_tree = ttk.Treeview(logs_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.logs_tree.heading('id', text='ID')
        self.logs_tree.heading('admin_id', text='管理员ID')
        self.logs_tree.heading('module', text='模块')
        self.logs_tree.heading('action', text='操作')
        self.logs_tree.heading('target_id', text='目标ID')
        self.logs_tree.heading('target_type', text='目标类型')
        self.logs_tree.heading('details', text='详情')
        self.logs_tree.heading('ip_address', text='IP地址')
        self.logs_tree.heading('created_at', text='创建时间')
        
        # 设置列宽
        self.logs_tree.column('id', width=50, anchor=tk.CENTER)
        self.logs_tree.column('admin_id', width=100, anchor=tk.CENTER)
        self.logs_tree.column('module', width=100, anchor=tk.CENTER)
        self.logs_tree.column('action', width=100, anchor=tk.CENTER)
        self.logs_tree.column('target_id', width=100, anchor=tk.CENTER)
        self.logs_tree.column('target_type', width=100, anchor=tk.CENTER)
        self.logs_tree.column('details', width=200, anchor=tk.CENTER)
        self.logs_tree.column('ip_address', width=150, anchor=tk.CENTER)
        self.logs_tree.column('created_at', width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        self.logs_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载操作日志数据
        self.load_operation_logs()
    
    def load_operation_logs(self):
        """加载操作日志数据"""
        # 清空现有数据
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)
        
        try:
            # 获取筛选条件
            module = self.log_module_var.get()
            action = self.log_action_var.get()
            
            # 构建URL
            url = f'{BASE_URL}/operation-logs'
            params = {}
            
            if module:
                params['module'] = module
            if action:
                params['action'] = action
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                logs = response.json()
                for log in logs:
                    self.logs_tree.insert('', tk.END, values=(
                        log.get('id'),
                        log.get('admin_id'),
                        log.get('module'),
                        log.get('action'),
                        log.get('target_id'),
                        log.get('target_type'),
                        log.get('details'),
                        log.get('ip_address'),
                        log.get('created_at')
                    ))
            else:
                messagebox.showerror('错误', '无法获取操作日志')
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def reset_log_filters(self):
        """重置日志筛选条件"""
        self.log_module_var.set('')
        self.log_action_var.set('')
        self.load_operation_logs()
        copy_window.geometry('600x500')
        copy_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(copy_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 源用户选择
        ttk.Label(form_frame, text='源用户:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.copy_source_user_var = tk.StringVar()
        self.copy_source_user_combo = ttk.Combobox(form_frame, textvariable=self.copy_source_user_var, width=30)
        self.copy_source_user_combo.grid(row=0, column=1, padx=10, pady=10)
        
        # 目标用户选择
        ttk.Label(form_frame, text='目标用户:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.copy_target_users_var = tk.StringVar()
        self.copy_target_users_list = tk.Listbox(form_frame, selectmode=tk.MULTIPLE, width=30, height=10)
        self.copy_target_users_list.grid(row=1, column=1, padx=10, pady=10)
        
        # 日期范围
        ttk.Label(form_frame, text='开始日期:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        from tkcalendar import DateEntry
        self.copy_start_date = DateEntry(form_frame, width=28, date_pattern='yyyy-MM-dd')
        self.copy_start_date.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(form_frame, text='结束日期:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        self.copy_end_date = DateEntry(form_frame, width=28, date_pattern='yyyy-MM-dd')
        self.copy_end_date.grid(row=3, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # 加载用户数据
        def load_users():
            try:
                response = requests.get(f'{BASE_URL}/users')
                if response.status_code == 200:
                    users = response.json()
                    # 设置源用户下拉选项
                    self.copy_source_user_combo['values'] = [f"{user.get('id')} - {user.get('username')}" for user in users]
                    if users:
                        self.copy_source_user_combo.current(0)  # 默认选择第一个用户
                    
                    # 设置目标用户列表
                    self.copy_target_users_list.delete(0, tk.END)
                    for user in users:
                        self.copy_target_users_list.insert(tk.END, f"{user.get('id')} - {user.get('username')}")
            except Exception as e:
                messagebox.showerror('错误', f'加载用户数据失败: {str(e)}')
        
        # 加载用户数据
        load_users()
        
        def copy_time_records():
            """执行批量复制工时记录"""
            # 获取源用户
            source_user_text = self.copy_source_user_var.get()
            if not source_user_text:
                messagebox.showerror('错误', '请选择源用户')
                return
            source_user_id = source_user_text.split(' - ')[0]
            
            # 获取目标用户
            selected_indices = self.copy_target_users_list.curselection()
            if not selected_indices:
                messagebox.showerror('错误', '请选择目标用户')
                return
            target_user_ids = []
            for index in selected_indices:
                target_user_text = self.copy_target_users_list.get(index)
                target_user_id = target_user_text.split(' - ')[0]
                target_user_ids.append(target_user_id)
            
            # 获取日期范围
            start_date = self.copy_start_date.get()
            end_date = self.copy_end_date.get()
            if not start_date or not end_date:
                messagebox.showerror('错误', '请选择开始日期和结束日期')
                return
            
            try:
                response = requests.post(f'{BASE_URL}/time-records/copy', json={
                    'source_user_id': source_user_id,
                    'target_user_ids': target_user_ids,
                    'start_date': start_date,
                    'end_date': end_date
                })
                if response.status_code == 200:
                    messagebox.showinfo('成功', response.json().get('message', '批量复制成功'))
                    copy_window.destroy()
                else:
                    messagebox.showerror('错误', response.json().get('error', '批量复制失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='复制', command=copy_time_records).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=copy_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_selected_records(self):
        """编辑选中的工时记录"""
        # 检查是否有选中记录
        if not self.selected_records:
            messagebox.showerror('错误', '请先选择要修改的记录')
            return
        
        # 创建弹窗
        edit_window = tk.Toplevel(self.root)
        edit_window.title('修改选中记录')
        edit_window.geometry('500x400')
        edit_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 是否请假
        ttk.Label(form_frame, text='是否请假:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_is_leave_var = tk.BooleanVar(value=False)
        leave_checkbox = ttk.Checkbutton(form_frame, variable=self.edit_is_leave_var)
        leave_checkbox.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        
        # 班别
        ttk.Label(form_frame, text='班别:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_shift_type_var = tk.StringVar()
        shift_combo = ttk.Combobox(form_frame, textvariable=self.edit_shift_type_var, width=30)
        shift_combo['values'] = ['白班', '夜班']
        shift_combo.grid(row=1, column=1, padx=10, pady=10)
        
        # 工时/请假时长
        ttk.Label(form_frame, text='时长(小时):').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.edit_hours_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.edit_hours_var, width=30).grid(row=2, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def save_edited_records():
            """保存修改后的记录"""
            is_leave = self.edit_is_leave_var.get()
            shift_type = self.edit_shift_type_var.get()
            hours_text = self.edit_hours_var.get()
            
            # 至少需要设置一个字段
            if not is_leave and not shift_type and not hours_text:
                messagebox.showerror('错误', '请至少修改一个字段')
                return
            
            hours = None
            if hours_text:
                try:
                    hours = float(hours_text)
                except:
                    messagebox.showerror('错误', '时长必须是数字')
                    return
            
            # 获取选中记录的用户ID
            user_ids = []
            for item in self.selected_records:
                values = self.daily_report_tree.item(item, 'values')
                if values:
                    user_ids.append(values[1])  # user_id
            
            try:
                # 获取报表日期
                report_date = self.daily_report_date.get()
                if not report_date:
                    messagebox.showerror('错误', '请选择日期')
                    return
                
                # 只获取一次当天的所有工时记录，避免多次网络请求
                records_response = requests.get(f'{BASE_URL}/time-records/date/{report_date}')
                if records_response.status_code != 200:
                    messagebox.showerror('错误', '无法获取工时记录数据')
                    return
                time_records = records_response.json()
                
                # 构建用户ID到记录的映射，提高查询效率
                records_by_user = {}
                for record in time_records:
                    uid = record['user_id']
                    if uid not in records_by_user:
                        records_by_user[uid] = []
                    records_by_user[uid].append(record)
                
                # 对于每个选中的用户，处理其记录
                # 使用集合去重，避免同一个用户被多次处理
                unique_user_ids = list(set(user_ids))
                
                for user_id in unique_user_ids:
                    # 找到当前用户的记录
                    user_records = records_by_user.get(user_id, [])
                    
                    # 如果没有记录，则创建新记录
                    if len(user_records) == 0:
                        # 创建新记录，处理hours可能为None的情况
                        create_data = {
                            'user_id': user_id,
                            'start_time': f'{report_date}T08:00:00',
                            'shift_type': shift_type,
                            'is_leave': is_leave,
                            'description': '管理员批量修改'
                        }
                        
                        # 计算结束时间和时长，确保格式正确
                        if hours is not None:
                            if is_leave:
                                # 请假记录，开始时间和结束时间可以相同，或者根据请假时长计算
                                start_time = f'{report_date}T00:00:00'
                                end_time = f'{report_date}T23:59:59'
                                duration = round(hours * 60)
                            else:
                                # 正常出勤，计算结束时间
                                start_time = f'{report_date}T08:00:00'
                                duration = round(hours * 60)
                                # 计算结束时间
                                end_time = f'{report_date}T{int(hours):02d}:{int((hours - int(hours)) * 60):02d}:00'
                            
                            create_data['start_time'] = start_time
                            create_data['end_time'] = end_time
                            create_data['duration'] = duration
                        
                        # 使用正确的time-records API URL，而不是admin API URL
                        time_records_url = BASE_URL.replace('/api/admin', '/api/time-records')
                        response = requests.post(f'{time_records_url}', json=create_data)
                        if response.status_code != 201:
                            error_msg = response.text
                            try:
                                error_msg = response.json().get('error', error_msg)
                            except:
                                pass
                            messagebox.showerror('错误', f'创建记录失败: {error_msg}')
                            return
                        
                        # 更新records_by_user字典，避免重复创建
                        if user_id not in records_by_user:
                            records_by_user[user_id] = []
                        # 假设创建成功，添加一个虚拟记录到字典中
                        records_by_user[user_id].append({'id': 'new', 'user_id': user_id})
                    else:
                        # 更新现有记录
                        for record in user_records:
                            update_data = {
                                'is_leave': is_leave
                            }
                            
                            if shift_type:
                                update_data['shift_type'] = shift_type
                            
                            if hours is not None:
                                duration = round(hours * 60)  # 转换为分钟
                                update_data['duration'] = duration
                                
                                if is_leave:
                                    # 请假记录，设置全天时间
                                    update_data['start_time'] = f'{report_date}T00:00:00'
                                    update_data['end_time'] = f'{report_date}T23:59:59'
                                else:
                                    # 正常出勤，重新计算结束时间
                                    update_data['start_time'] = f'{report_date}T08:00:00'
                                    end_time = f'{report_date}T{int(hours):02d}:{int((hours - int(hours)) * 60):02d}:00'
                                    update_data['end_time'] = end_time
                            
                            # 使用正确的time-records API URL，而不是admin API URL
                            time_records_url = BASE_URL.replace('/api/admin', '/api/time-records')
                            # 发送PUT请求时包含user_id参数
                            response = requests.put(f'{time_records_url}/{record['id']}?user_id={user_id}', json=update_data, timeout=10)  # 添加超时设置
                            if response.status_code != 200:
                                error_msg = response.text
                                try:
                                    error_msg = response.json().get('error', error_msg)
                                except:
                                    pass
                                messagebox.showerror('错误', f'更新记录失败: {error_msg}')
                                return
                
                messagebox.showinfo('成功', f'成功修改 {len(user_ids)} 条记录')
                edit_window.destroy()
                # 刷新报表
                self.generate_daily_attendance_report()
            except Exception as e:
                messagebox.showerror('错误', f'修改记录失败: {str(e)}')
        
        ttk.Button(button_frame, text='保存修改', command=save_edited_records).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text='取消', command=edit_window.destroy).grid(row=0, column=1, padx=10)
    
    def logout(self):
        """退出登录"""
        if messagebox.askyesno('确认', '确定要退出登录吗？'):
            self.logged_in = False
            self.token = None
            self.admin_info = None
            
            # 删除登录状态文件
            if os.path.exists(LOGIN_FILE):
                os.remove(LOGIN_FILE)
            
            self.show_login_window()
    
    def exit_app(self):
        """退出应用"""
        if messagebox.askyesno('确认', '确定要退出应用吗？'):
            self.root.quit()
    
    def show_auto_task_manager(self):
        """显示自动任务管理器"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='自动任务管理器', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text='刷新任务列表', command=self.load_tasks).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='添加定时任务', command=self.show_add_task_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='手动执行任务', command=self.show_manual_execute_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='查看任务日志', command=self.show_task_logs).pack(side=tk.LEFT, padx=5)
        
        # 任务列表框架
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 表格
        columns = ('id', 'job_name', 'description', 'trigger_type', 'cron_expression', 'status', 'actions')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.task_tree.heading('id', text='ID')
        self.task_tree.heading('job_name', text='任务名称')
        self.task_tree.heading('description', text='任务描述')
        self.task_tree.heading('trigger_type', text='触发类型')
        self.task_tree.heading('cron_expression', text='执行时间')
        self.task_tree.heading('status', text='状态')
        self.task_tree.heading('actions', text='操作')
        
        # 设置列宽
        self.task_tree.column('id', width=80, anchor=tk.CENTER)
        self.task_tree.column('job_name', width=150, anchor=tk.CENTER)
        self.task_tree.column('description', width=200, anchor=tk.CENTER)
        self.task_tree.column('trigger_type', width=100, anchor=tk.CENTER)
        self.task_tree.column('cron_expression', width=150, anchor=tk.CENTER)
        self.task_tree.column('status', width=100, anchor=tk.CENTER)
        self.task_tree.column('actions', width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.task_tree.xview)
        self.task_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        
        # 布局
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 加载任务列表
        self.load_tasks()
        
        # 添加点击事件处理
        self.task_tree.bind('<ButtonRelease-1>', self.on_task_tree_click)
    
    def load_tasks(self):
        """加载任务列表"""
        # 清空现有数据
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        try:
            # 获取定时任务列表
            response = requests.get('http://localhost:5000/api/scheduler/jobs')
            if response.status_code == 200:
                tasks = response.json()
                for task in tasks:
                    # 添加操作按钮
                    actions = f"编辑 | 删除 | 启用/禁用"
                    self.task_tree.insert('', tk.END, values=(
                        task.get('id', ''),
                        task.get('job_name', ''),
                        task.get('description', ''),
                        task.get('trigger_type', ''),
                        task.get('cron_expression', ''),
                        task.get('status', ''),
                        actions
                    ))
            else:
                messagebox.showerror('错误', '无法获取任务列表')
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def on_task_tree_click(self, event):
        """处理任务列表点击事件"""
        # 获取点击的行和列
        item = self.task_tree.identify_row(event.y)
        column = self.task_tree.identify_column(event.x)
        
        # 如果点击了操作列
        if column == '#7':  # actions列
            # 获取行数据
            values = self.task_tree.item(item, 'values')
            if values:
                task_id = values[0]
                # 获取Treeview控件的坐标
                tree_x = self.task_tree.winfo_x()
                tree_y = self.task_tree.winfo_y()
                # 转换event坐标为相对于Treeview控件的坐标
                tree_event_x = event.x - tree_x
                tree_event_y = event.y - tree_y
                # 获取操作列的坐标和宽度
                x, y, width, height = self.task_tree.bbox(item, column)
                # 计算相对点击位置
                relative_x = tree_event_x - x
                # 计算每个按钮的宽度
                button_width = width / 3
                # 判断点击的是哪个按钮
                if relative_x < button_width:
                    # 编辑按钮
                    self.edit_task(task_id)
                elif relative_x < button_width * 2:
                    # 删除按钮
                    self.delete_task(task_id)
                else:
                    # 启用/禁用按钮
                    self.toggle_task_status(task_id)
    
    def show_add_task_window(self):
        """显示添加任务窗口"""
        # 创建弹窗
        add_window = tk.Toplevel(self.root)
        add_window.title('添加定时任务')
        add_window.geometry('600x500')
        add_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(add_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 任务名称
        ttk.Label(form_frame, text='任务名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        job_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=job_name_var, width=40).grid(row=0, column=1, padx=10, pady=10)
        
        # 任务描述
        ttk.Label(form_frame, text='任务描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        description_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=description_var, width=40).grid(row=1, column=1, padx=10, pady=10)
        
        # 触发类型
        ttk.Label(form_frame, text='触发类型:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        trigger_type_var = tk.StringVar(value='cron')
        trigger_types = ['cron', 'interval']
        trigger_combo = ttk.Combobox(form_frame, textvariable=trigger_type_var, width=38, values=trigger_types, state='readonly')
        trigger_combo.grid(row=2, column=1, padx=10, pady=10)
        
        # 执行时间
        ttk.Label(form_frame, text='执行时间:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        cron_expression_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=cron_expression_var, width=40).grid(row=3, column=1, padx=10, pady=10)
        ttk.Label(form_frame, text='例如: 0 4,8,12,16,22 * * * (每天4:00,8:00,12:00,16:00,22:00执行)').grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)
        
        # 任务类型
        ttk.Label(form_frame, text='任务类型:').grid(row=5, column=0, padx=10, pady=10, sticky=tk.E)
        task_type_var = tk.StringVar()
        task_types = ['auto_add_time_records', 'send_system_message', 'other']
        task_type_combo = ttk.Combobox(form_frame, textvariable=task_type_var, width=38, values=task_types, state='readonly')
        task_type_combo.grid(row=5, column=1, padx=10, pady=10)
        
        # 状态
        ttk.Label(form_frame, text='状态:').grid(row=6, column=0, padx=10, pady=10, sticky=tk.E)
        status_var = tk.StringVar(value='enabled')
        status_types = ['enabled', 'disabled']
        status_combo = ttk.Combobox(form_frame, textvariable=status_var, width=38, values=status_types, state='readonly')
        status_combo.grid(row=6, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        def save_task():
            """保存任务"""
            job_name = job_name_var.get()
            description = description_var.get()
            trigger_type = trigger_type_var.get()
            cron_expression = cron_expression_var.get()
            task_type = task_type_var.get()
            status = status_var.get()
            
            if not job_name or not description or not cron_expression or not task_type:
                messagebox.showerror('错误', '请填写所有必填字段')
                return
            
            try:
                response = requests.post('http://localhost:5000/api/scheduler/jobs', json={
                    'job_name': job_name,
                    'description': description,
                    'trigger_type': trigger_type,
                    'cron_expression': cron_expression,
                    'task_type': task_type,
                    'status': status
                })
                if response.status_code == 201:
                    messagebox.showinfo('成功', '任务添加成功')
                    add_window.destroy()
                    self.load_tasks()  # 刷新任务列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '添加任务失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=save_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=add_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_task(self, task_id):
        """编辑任务"""
        # 获取任务详情
        try:
            response = requests.get(f'http://localhost:5000/api/scheduler/jobs/{task_id}')
            if response.status_code != 200:
                messagebox.showerror('错误', '无法获取任务详情')
                return
            task = response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
            return
        
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f'编辑任务 - {task.get('job_name')}')
        edit_window.geometry('600x500')
        edit_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 任务名称
        ttk.Label(form_frame, text='任务名称:').grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        job_name_var = tk.StringVar(value=task.get('job_name'))
        ttk.Entry(form_frame, textvariable=job_name_var, width=40).grid(row=0, column=1, padx=10, pady=10)
        
        # 任务描述
        ttk.Label(form_frame, text='任务描述:').grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        description_var = tk.StringVar(value=task.get('description'))
        ttk.Entry(form_frame, textvariable=description_var, width=40).grid(row=1, column=1, padx=10, pady=10)
        
        # 触发类型
        ttk.Label(form_frame, text='触发类型:').grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        trigger_type_var = tk.StringVar(value=task.get('trigger_type'))
        trigger_types = ['cron', 'interval']
        trigger_combo = ttk.Combobox(form_frame, textvariable=trigger_type_var, width=38, values=trigger_types, state='readonly')
        trigger_combo.grid(row=2, column=1, padx=10, pady=10)
        
        # 执行时间
        ttk.Label(form_frame, text='执行时间:').grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        cron_expression_var = tk.StringVar(value=task.get('cron_expression'))
        ttk.Entry(form_frame, textvariable=cron_expression_var, width=40).grid(row=3, column=1, padx=10, pady=10)
        ttk.Label(form_frame, text='例如: 0 4,8,12,16,22 * * * (每天4:00,8:00,12:00,16:00,22:00执行)').grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)
        
        # 任务类型
        ttk.Label(form_frame, text='任务类型:').grid(row=5, column=0, padx=10, pady=10, sticky=tk.E)
        task_type_var = tk.StringVar(value=task.get('task_type'))
        task_types = ['auto_add_time_records', 'send_system_message', 'other']
        task_type_combo = ttk.Combobox(form_frame, textvariable=task_type_var, width=38, values=task_types, state='readonly')
        task_type_combo.grid(row=5, column=1, padx=10, pady=10)
        
        # 状态
        ttk.Label(form_frame, text='状态:').grid(row=6, column=0, padx=10, pady=10, sticky=tk.E)
        status_var = tk.StringVar(value=task.get('status'))
        status_types = ['enabled', 'disabled']
        status_combo = ttk.Combobox(form_frame, textvariable=status_var, width=38, values=status_types, state='readonly')
        status_combo.grid(row=6, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        def update_task():
            """更新任务"""
            job_name = job_name_var.get()
            description = description_var.get()
            trigger_type = trigger_type_var.get()
            cron_expression = cron_expression_var.get()
            task_type = task_type_var.get()
            status = status_var.get()
            
            if not job_name or not description or not cron_expression or not task_type:
                messagebox.showerror('错误', '请填写所有必填字段')
                return
            
            try:
                response = requests.put(f'http://localhost:5000/api/scheduler/jobs/{task_id}', json={
                    'job_name': job_name,
                    'description': description,
                    'trigger_type': trigger_type,
                    'cron_expression': cron_expression,
                    'task_type': task_type,
                    'status': status
                })
                if response.status_code == 200:
                    messagebox.showinfo('成功', '任务更新成功')
                    edit_window.destroy()
                    self.load_tasks()  # 刷新任务列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '更新任务失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='保存', command=update_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=edit_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_task(self, task_id):
        """删除任务"""
        if messagebox.askyesno('确认', f'确定要删除ID为 {task_id} 的任务吗？'):
            try:
                response = requests.delete(f'http://localhost:5000/api/scheduler/jobs/{task_id}')
                if response.status_code == 200:
                    messagebox.showinfo('成功', '任务删除成功')
                    self.load_tasks()  # 刷新任务列表
                else:
                    messagebox.showerror('错误', response.json().get('error', '删除任务失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def toggle_task_status(self, task_id):
        """切换任务状态"""
        try:
            response = requests.patch(f'http://localhost:5000/api/scheduler/jobs/{task_id}/toggle')
            if response.status_code == 200:
                messagebox.showinfo('成功', '任务状态切换成功')
                self.load_tasks()  # 刷新任务列表
            else:
                messagebox.showerror('错误', response.json().get('error', '切换任务状态失败'))
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
    
    def show_manual_execute_window(self):
        """显示手动执行任务窗口"""
        # 创建弹窗
        execute_window = tk.Toplevel(self.root)
        execute_window.title('手动执行任务')
        execute_window.geometry('400x300')
        execute_window.resizable(False, False)
        
        # 表单框架
        form_frame = ttk.Frame(execute_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 任务列表
        ttk.Label(form_frame, text='选择要执行的任务:').pack(anchor=tk.W, pady=10)
        
        # 获取任务列表
        tasks = []
        try:
            response = requests.get('http://localhost:5000/api/scheduler/jobs')
            if response.status_code == 200:
                tasks = response.json()
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        # 任务下拉菜单
        task_var = tk.StringVar()
        task_options = [task['job_name'] for task in tasks]
        if task_options:
            task_var.set(task_options[0])
        
        task_combo = ttk.Combobox(form_frame, textvariable=task_var, values=task_options, state='readonly')
        task_combo.pack(fill=tk.X, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        def execute_task():
            """执行任务"""
            selected_task_name = task_var.get()
            if not selected_task_name:
                messagebox.showerror('错误', '请选择一个任务')
                return
            
            try:
                response = requests.post(f'http://localhost:5000/api/scheduler/jobs/execute', json={
                    'job_name': selected_task_name
                })
                if response.status_code == 200:
                    messagebox.showinfo('成功', '任务执行成功')
                    execute_window.destroy()
                else:
                    messagebox.showerror('错误', response.json().get('error', '执行任务失败'))
            except Exception as e:
                messagebox.showerror('错误', f'网络错误: {str(e)}')
        
        ttk.Button(button_frame, text='执行', command=execute_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='取消', command=execute_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def show_task_logs(self):
        """显示任务执行日志"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(title_frame, text='任务执行日志', font=('Arial', 24)).pack(side=tk.LEFT)
        
        # 日志列表框架
        logs_frame = ttk.Frame(self.main_frame)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        try:
            # 获取任务执行日志
            logs_response = requests.get('http://localhost:5000/api/scheduler/logs')
            if logs_response.status_code != 200:
                raise Exception('获取任务执行日志失败')
            
            logs_data = logs_response.json()
            logs = logs_data.get('logs', [])
            
            # 表格
            columns = ('id', 'job_name', 'status', 'start_time', 'execution_time', 'message')
            logs_tree = ttk.Treeview(logs_frame, columns=columns, show='headings')
            
            # 设置列标题
            logs_tree.heading('id', text='ID')
            logs_tree.heading('job_name', text='任务名称')
            logs_tree.heading('status', text='状态')
            logs_tree.heading('start_time', text='执行时间')
            logs_tree.heading('execution_time', text='执行时长(秒)')
            logs_tree.heading('message', text='消息')
            
            # 设置列宽
            logs_tree.column('id', width=80, anchor=tk.CENTER)
            logs_tree.column('job_name', width=150, anchor=tk.CENTER)
            logs_tree.column('status', width=100, anchor=tk.CENTER)
            logs_tree.column('start_time', width=180, anchor=tk.CENTER)
            logs_tree.column('execution_time', width=120, anchor=tk.CENTER)
            logs_tree.column('message', width=400, anchor=tk.W)
            
            # 添加数据
            for log in logs:
                logs_tree.insert('', tk.END, values=(
                    log['id'],
                    log['job_name'],
                    log['status'],
                    log['start_time'],
                    f"{log['execution_time']:.2f}",
                    log['message']
                ))
            
            # 添加滚动条
            scrollbar_y = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=logs_tree.yview)
            scrollbar_x = ttk.Scrollbar(logs_frame, orient=tk.HORIZONTAL, command=logs_tree.xview)
            logs_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
            
            # 布局
            logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            ttk.Label(self.main_frame, text=f'获取任务执行日志失败: {str(e)}', font=('Arial', 12), foreground='red').pack(anchor=tk.W, padx=20, pady=10)

if __name__ == '__main__':
    root = tk.Tk()
    app = AdminApp(root)
    root.mainloop()
