from flask import Flask, jsonify, request, redirect, send_from_directory
from flask_cors import CORS
from config import Config
from utils.db import init_db, init_app as init_db_app
from utils.role_mapping import get_base_role, BASE_ROLES
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
import logging
import json
import socket
from utils.db import get_db

# 自定义JSON编码器，处理datetime对象
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # 将datetime对象转换为北京时间格式的字符串
            from config import BEIJING_TIMEZONE
            beijing_time = obj.astimezone(BEIJING_TIMEZONE)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        return super().default(obj)

app = Flask(__name__)
app.config.from_object(Config)
app.url_map.strict_slashes = False

# 使用自定义JSON编码器
app.json_encoder = CustomJSONEncoder

# 配置CORS - 允许所有来源，支持所有HTTP方法
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Type"],
    "supports_credentials": False
}})

# 初始化数据库
init_db_app(app)

# 创建数据库表
with app.app_context():
    init_db()
    # 更新数据库结构
    db = get_db()
    cursor = db.execute("PRAGMA table_info(users)")
    cols = cursor.fetchall()
    col_names = [col[1] for col in cols]
    if 'shift_type' not in col_names:
        db.execute("ALTER TABLE users ADD COLUMN shift_type TEXT")
        db.commit()
    # 初始化默认角色
    role_count = db.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    if role_count == 0:
        # 只初始化简化的8个基础岗位
        default_roles = ['配料', '涂布', '辊压', '分条', '发片', '领班', '物料', '主管']
        for role in default_roles:
            db.execute("INSERT OR IGNORE INTO roles (name) VALUES (?)", (role,))
        db.commit()
    # 为 users 表补充 employee_id 字段
    cursor = db.execute("PRAGMA table_info(users)")
    user_cols = [row[1] for row in cursor.fetchall()]
    if 'employee_id' not in user_cols:
        db.execute("ALTER TABLE users ADD COLUMN employee_id TEXT")
        db.commit()
    # 创建通知表
    db.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL DEFAULT 'user_login',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)')
    db.commit()
    # ★ 给工时表加关键索引（根因修复：查日期/用户时避免全表扫描）
    db.execute('CREATE INDEX IF NOT EXISTS idx_time_records_start_time ON time_records(start_time)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_time_records_user_start ON time_records(user_id, start_time)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id)')
    db.commit()
    # 创建用户通知已读表
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_notification_read (
            user_id INTEGER NOT NULL,
            notification_id INTEGER NOT NULL,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, notification_id)
        )
    ''')
    db.commit()

# 导入路由
from routes.auth import bp as auth_bp
from routes.project import bp as project_bp
from routes.time_record import bp as time_record_bp
from routes.stats import bp as stats_bp
from routes.salary import bp as salary_bp
from routes.backup import bp as backup_bp
from routes.admin import bp as admin_bp
from routes.message import message_bp
from routes.wooden_fish import wooden_fish_bp
from routes.sudoku import sudoku_bp
from routes.guess_number import bp as guess_number_bp
from routes.user_config import bp as user_config_bp
from routes.fund import fund_bp, auto_refresh_fund_prices, push_fund_report, push_fund_loss_alert, record_daily_fund_returns
from routes.mentorship import mentorship_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(project_bp, url_prefix='/api/projects')
app.register_blueprint(time_record_bp, url_prefix='/api/time-records')
app.register_blueprint(stats_bp, url_prefix='/api/stats')
app.register_blueprint(salary_bp, url_prefix='/api/salary')
app.register_blueprint(backup_bp, url_prefix='/api/backup')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(message_bp, url_prefix='/api/messages')
app.register_blueprint(wooden_fish_bp, url_prefix='/api/wooden-fish')
app.register_blueprint(sudoku_bp, url_prefix='/api/sudoku')
app.register_blueprint(guess_number_bp, url_prefix='/api/guess-number')
app.register_blueprint(user_config_bp, url_prefix='/api/user-config')
app.register_blueprint(fund_bp, url_prefix='/api/funds')
app.register_blueprint(mentorship_bp, url_prefix='/api/mentorship')

# 提供静态文件服务
@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('../frontend', path)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

# 记录定时任务日志的函数
def log_scheduler_job(job_name, status, message=None):
    """记录定时任务的执行情况到数据库"""
    from utils.db import get_db
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    
    try:
        db = get_db()
        now = datetime.now(BEIJING_TIMEZONE)
        db.execute(
            '''INSERT INTO scheduler_logs 
            (job_name, status, message, start_time, end_time, execution_time) 
            VALUES (?, ?, ?, ?, ?, ?)''',
            (job_name, status, message, now, now, 0.0)
        )
        db.commit()
    except Exception as e:
        logging.error(f"记录定时任务日志失败: {str(e)}")

# 自动添加工时记录的函数
def auto_add_time_records():
    """每天在固定时间根据排班添加当天的班别和工时记录"""
    from utils.db import get_db
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    
    start_time = datetime.now(BEIJING_TIMEZONE)
    logging.info(f"开始执行自动添加工时记录任务，当前时间: {start_time}")
    log_scheduler_job("auto_add_time_records", "running", "开始执行自动添加工时记录任务")
    
    try:
        db = get_db()
        today = start_time.strftime('%Y-%m-%d')
        
        # 查询今天的排班记录 - 确保使用最新的排班数据
        schedules = db.execute(
            '''SELECT s.*, u.username 
            FROM schedules s 
            JOIN users u ON s.user_id = u.id 
            WHERE DATE(?) BETWEEN DATE(s.start_date) AND DATE(s.end_date)''',
            (today,)
        ).fetchall()
        
        logging.info(f"今天的排班记录数量: {len(schedules)}")
        
        added_count = 0
        for schedule in schedules:
            user_id = schedule['user_id']
            shift_type = schedule['shift_type']
            hours = schedule['hours']
            description = schedule['description'] or f"自动生成的{shift_type}工时记录"
            
            # 检查今天是否已经为该用户创建了工时记录 - 使用更严格的查询条件
            existing_record = db.execute(
                '''SELECT id FROM time_records 
                WHERE user_id = ? AND DATE(start_time) = DATE(?)''',
                (user_id, today)
            ).fetchone()
            
            if existing_record:
                logging.info(f"用户 {user_id} 今天已经有工时记录，跳过")
                continue
            
            # 创建今天的工时记录
            # 假设白班开始时间为08:00，夜班开始时间为20:00
            if shift_type == '白班':
                start_time_str = f"{today}T08:00:00"
                end_time_str = f"{today}T18:00:00"
            elif shift_type == '夜班':
                start_time_str = f"{today}T20:00:00"
                # 夜班结束时间是第二天06:00，计算第二天的日期
                from datetime import datetime, timedelta
                today_date = datetime.strptime(today, '%Y-%m-%d')
                tomorrow_date = today_date + timedelta(days=1)
                tomorrow = tomorrow_date.strftime('%Y-%m-%d')
                end_time_str = f"{tomorrow}T06:00:00"
            else:
                # 默认白班
                start_time_str = f"{today}T08:00:00"
                end_time_str = f"{today}T18:00:00"
            
            # 计算时长（分钟）
            duration = int(hours * 60)
            
            # 插入工时记录
            db.execute(
                '''INSERT INTO time_records 
                (user_id, start_time, end_time, duration, shift_type, is_leave, description) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, start_time_str, end_time_str, duration, shift_type, False, description)
            )
            
            logging.info(f"为用户 {user_id} 添加了 {shift_type} 工时记录，时长: {hours} 小时")
            added_count += 1
        
        db.commit()
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        message = f"自动添加工时记录任务执行完成，成功添加 {added_count} 条记录，执行时间: {execution_time:.2f} 秒"
        logging.info(message)
        log_scheduler_job("auto_add_time_records", "success", message)
    except Exception as e:
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        error_message = f"自动添加工时记录任务执行失败: {str(e)}，执行时间: {execution_time:.2f} 秒"
        logging.error(error_message)
        log_scheduler_job("auto_add_time_records", "failed", error_message)
        db.rollback()

# 发送系统消息的函数
def send_system_message():
    """发送系统消息，包含当天出勤人数、班别工时数据和具体出勤名单"""
    from utils.db import get_db
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    import requests
    
    start_time = datetime.now(BEIJING_TIMEZONE)
    logging.info(f"开始执行发送系统消息任务，当前时间: {start_time}")
    log_scheduler_job("send_system_message", "running", "开始执行发送系统消息任务")
    
    try:
        db = get_db()
        today = start_time.strftime('%Y-%m-%d')
        
        # 查询当天的出勤人数
        attendance_count = db.execute(
            '''SELECT COUNT(DISTINCT user_id) as count 
            FROM time_records 
            WHERE DATE(start_time) = DATE(?)''',
            (today,)
        ).fetchone()['count']
        
        # 查询当天的班别工时数据
        shift_stats = db.execute(
            '''SELECT shift_type, COUNT(*) as count, SUM(duration) as total_minutes 
            FROM time_records 
            WHERE DATE(start_time) = DATE(?) 
            GROUP BY shift_type''',
            (today,)
        ).fetchall()
        
        # 查询当天的具体出勤名单
        attendance_users = db.execute(
            '''SELECT DISTINCT u.username 
            FROM time_records tr 
            JOIN users u ON tr.user_id = u.id 
            WHERE DATE(tr.start_time) = DATE(?)''',
            (today,)
        ).fetchall()
        
        # 构建系统消息内容
        message_content = f"【系统消息】{today} 出勤情况\n"
        message_content += f"出勤人数: {attendance_count} 人\n"
        message_content += "班别工时数据:\n"
        
        for shift in shift_stats:
            shift_type = shift['shift_type']
            count = shift['count']
            total_hours = round(shift['total_minutes'] / 60, 2)
            message_content += f"  - {shift_type}: {count} 人，总工时 {total_hours} 小时\n"
        
        message_content += "出勤名单:\n"
        for user in attendance_users:
            message_content += f"  - {user['username']}\n"
        
        # 发送系统消息
        # 使用requests库调用自己的API，添加系统消息
        try:
            requests.post(
                'http://127.0.0.1:5000/api/messages/system',
                json={'content': message_content}, 
                timeout=10  # 添加超时设置，避免任务一直等待
            )
        except requests.exceptions.RequestException as e:
            logging.warning(f"发送系统消息API调用失败: {str(e)}")
        
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        message = f"系统消息发送成功，执行时间: {execution_time:.2f} 秒"
        logging.info(message)
        log_scheduler_job("send_system_message", "success", message)
    except Exception as e:
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        error_message = f"发送系统消息任务执行失败: {str(e)}，执行时间: {execution_time:.2f} 秒"
        logging.error(error_message)
        log_scheduler_job("send_system_message", "failed", error_message)

# 删除过期排班的函数
def delete_expired_schedules():
    """删除过期的排班记录"""
    from utils.db import get_db
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    
    start_time = datetime.now(BEIJING_TIMEZONE)
    logging.info(f"开始执行删除过期排班任务，当前时间: {start_time}")
    log_scheduler_job("delete_expired_schedules", "running", "开始执行删除过期排班任务")
    
    try:
        db = get_db()
        
        # 获取当前日期
        today = start_time.strftime('%Y-%m-%d')
        
        # 删除过期排班
        result = db.execute('DELETE FROM schedules WHERE end_date < ?', (today,))
        db.commit()
        
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        message = f"删除过期排班任务执行完成，成功删除 {result.rowcount} 条记录，执行时间: {execution_time:.2f} 秒"
        logging.info(message)
        log_scheduler_job("delete_expired_schedules", "success", message)
    except Exception as e:
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        error_message = f"删除过期排班任务执行失败: {str(e)}，执行时间: {execution_time:.2f} 秒"
        logging.error(error_message)
        log_scheduler_job("delete_expired_schedules", "failed", error_message)
        db.rollback()

# 检查重复工时记录的函数
def check_duplicate_time_records():
    """检查并处理重复的工时记录"""
    from utils.db import get_db
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    
    start_time = datetime.now(BEIJING_TIMEZONE)
    logging.info(f"开始执行检查重复工时记录任务，当前时间: {start_time}")
    log_scheduler_job("check_duplicate_time_records", "running", "开始执行检查重复工时记录任务")
    
    db = None
    try:
        db = get_db()
        
        # 查询重复的工时记录
        # 重复条件：同一用户、同一天、同一班别
        duplicates = db.execute(
            '''SELECT user_id, DATE(start_time) as record_date, shift_type, COUNT(*) as count 
            FROM time_records 
            GROUP BY user_id, DATE(start_time), shift_type 
            HAVING COUNT(*) > 1'''
        ).fetchall()
        
        total_duplicates = len(duplicates)
        
        # 处理重复记录
        deleted_count = 0
        for duplicate in duplicates:
            user_id = duplicate['user_id']
            record_date = duplicate['record_date']
            shift_type = duplicate['shift_type']
            
            # 获取该用户当天该班别的所有记录
            records = db.execute(
                '''SELECT id, start_time 
                FROM time_records 
                WHERE user_id = ? AND DATE(start_time) = ? AND shift_type = ? 
                ORDER BY start_time''',
                (user_id, record_date, shift_type)
            ).fetchall()
            
            # 保留第一条记录，删除其余记录
            for record in records[1:]:
                db.execute('DELETE FROM time_records WHERE id = ?', (record['id'],))
                deleted_count += 1
        
        db.commit()
        
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        message = f"检查重复工时记录任务执行完成，发现 {total_duplicates} 组重复记录，成功删除 {deleted_count} 条记录，执行时间: {execution_time:.2f} 秒"
        logging.info(message)
        log_scheduler_job("check_duplicate_time_records", "success", message)
    except Exception as e:
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        error_message = f"检查重复工时记录任务执行失败: {str(e)}，执行时间: {execution_time:.2f} 秒"
        logging.error(error_message)
        log_scheduler_job("check_duplicate_time_records", "failed", error_message)
        if db:
            db.rollback()


# 删除过期出勤脚本的函数
def cleanup_expired_attendance_scripts():
    """清理过期的出勤脚本"""
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    import logging
    
    start_time = datetime.now(BEIJING_TIMEZONE)
    logging.info("开始执行清理过期出勤脚本任务")
    log_scheduler_job("cleanup_expired_attendance_scripts", "running", "开始执行清理过期出勤脚本任务")
    
    try:
        # 导入管理器
        from attendance_skill_manager import get_manager
        manager = get_manager()
        
        # 清理过期脚本（30天）
        cleaned_files = manager.cleanup_expired_scripts(expire_days=30)
        
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        message = f"清理过期出勤脚本任务执行完成，删除了 {len(cleaned_files)} 个脚本，执行时间: {execution_time:.2f} 秒"
        logging.info(message)
        log_scheduler_job("cleanup_expired_attendance_scripts", "success", message)
    except Exception as e:
        end_time = datetime.now(BEIJING_TIMEZONE)
        execution_time = (end_time - start_time).total_seconds()
        error_message = f"清理过期出勤脚本任务执行失败: {str(e)}，执行时间: {execution_time:.2f} 秒"
        logging.error(error_message)
        log_scheduler_job("cleanup_expired_attendance_scripts", "failed", error_message)

# 内存中的任务列表，用于管理定时任务
scheduled_jobs = [
    {
        'id': 1,
        'job_name': 'auto_add_time_records',
        'description': '根据排班自动添加当天的班别和工时记录',
        'trigger_type': 'cron',
        'cron_expression': '0 4,8,12,16,22 * * *',
        'task_type': 'auto_add_time_records',
        'status': 'enabled',
        'function': auto_add_time_records
    },
    {
        'id': 2,
        'job_name': 'send_system_message',
        'description': '发送当天出勤情况的系统消息',
        'trigger_type': 'cron',
        'cron_expression': '0 8,12,16,22 * * *',
        'task_type': 'send_system_message',
        'status': 'enabled',
        'function': send_system_message
    },
    {
        'id': 3,
        'job_name': 'delete_expired_schedules',
        'description': '删除过期的排班记录',
        'trigger_type': 'cron',
        'cron_expression': '0 0,4,8,13,20 * * *',
        'task_type': 'delete_expired_schedules',
        'status': 'enabled',
        'function': delete_expired_schedules
    },
    {
        'id': 4,
        'job_name': 'check_duplicate_time_records',
        'description': '检查并处理重复的工时记录',
        'trigger_type': 'cron',
        'cron_expression': '0 0,4,8,13,20 * * *',
        'task_type': 'check_duplicate_time_records',
        'status': 'enabled',
        'function': check_duplicate_time_records
    },
    {
        'id': 5,
        'job_name': 'cleanup_expired_attendance_scripts',
        'description': '清理过期的出勤脚本（30天前）',
        'trigger_type': 'cron',
        'cron_expression': '0 1 * * 0',
        'task_type': 'cleanup_expired_attendance_scripts',
        'status': 'enabled',
        'function': cleanup_expired_attendance_scripts
    },
    {
        'id': 6,
        'job_name': 'auto_refresh_fund_prices',
        'description': '每天晚上8点自动刷新所有基金净值',
        'trigger_type': 'cron',
        'cron_expression': '0 20 * * *',
        'task_type': 'auto_refresh_fund_prices',
        'status': 'enabled',
        'function': auto_refresh_fund_prices
    },
    {
        'id': 7,
        'job_name': 'push_fund_report',
        'description': '交易日9:05-15:05每两小时推送基金报告到钉钉',
        'trigger_type': 'cron',
        'cron_expression': '5 9,11,13,15 * * 1-5',
        'task_type': 'push_fund_report',
        'status': 'disabled',
        'function': push_fund_report
    },
    {
        'id': 8,
        'job_name': 'push_fund_loss_alert',
        'description': '交易日9:30-15:00每半小时检查基金亏损，超过3%推送提醒',
        'trigger_type': 'cron',
        'cron_expression': '30,0 9-15 * * 1-5',
        'task_type': 'push_fund_loss_alert',
        'status': 'enabled',
        'function': push_fund_loss_alert
    }
]

# 初始化定时任务
def init_scheduler():
    """初始化并启动定时任务"""
    global scheduler
    scheduler = BackgroundScheduler()
    
    # 从任务列表中加载任务
    for job in scheduled_jobs:
        if job['status'] == 'enabled':
            # 解析cron表达式
            # cron表达式格式：分 时 日 月 周
            cron_parts = job['cron_expression'].split()
            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts
                scheduler.add_job(
                    job['function'],
                    'cron',
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    id=str(job['id']),
                    name=job['job_name']
                )
    
    scheduler.start()
    logging.info("定时任务调度器已启动")

# 手动触发发送系统消息的API端点
@app.route('/api/messages/test-system-message', methods=['POST'])
def test_system_message():
    """测试发送系统消息"""
    try:
        send_system_message()
        return jsonify({'message': '系统消息发送成功'}), 200
    except Exception as e:
        logging.error(f"发送系统消息失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 手动触发钉钉基金报告推送的API端点
@app.route('/api/funds/test-push', methods=['POST'])
def test_fund_push():
    """测试推送基金报告到钉钉"""
    try:
        success = push_fund_report()
        if success:
            return jsonify({'message': '基金报告推送成功'}), 200
        else:
            return jsonify({'error': '基金报告推送失败'}), 500
    except Exception as e:
        logging.error(f"推送基金报告失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 手动触发基金亏损提醒的API端点
@app.route('/api/funds/test-loss-alert', methods=['POST'])
def test_fund_loss_alert():
    """测试推送基金亏损提醒到钉钉"""
    try:
        success = push_fund_loss_alert()
        if success:
            return jsonify({'message': '亏损提醒推送成功'}), 200
        else:
            return jsonify({'message': '没有基金达到亏损阈值，无需提醒'}), 200
    except Exception as e:
        logging.error(f"推送亏损提醒失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 手动触发记录基金收益的API端点
@app.route('/api/funds/record-returns', methods=['POST'])
def test_record_returns():
    """手动触发记录基金收益"""
    try:
        count = record_daily_fund_returns()
        return jsonify({
            'message': '基金收益记录完成',
            'recorded_count': count
        }), 200
    except Exception as e:
        logging.error(f"记录基金收益失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 手动触发刷新基金价格并记录收益的API端点
@app.route('/api/funds/refresh-and-record', methods=['POST'])
def refresh_and_record():
    """刷新基金价格并记录收益"""
    try:
        auto_refresh_fund_prices()
        return jsonify({'message': '基金价格刷新并记录收益完成'}), 200
    except Exception as e:
        logging.error(f"刷新基金价格并记录收益失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 通用批量添加考勤API
@app.route('/api/attendance/batch-add', methods=['POST'])
def batch_add_attendance():
    """批量添加入勤数据

    请求格式：
    {
        "date": "2026-06-10",
        "shift": "白班",
        "should_attend": 36,
        "actual_attend": 33,
        "attendance": {
            "配料": ["刘虎", "蒋江坤"],
            "涂布": ["李景均", "李培嘉"]
        },
        "leave": ["宁福"],
        "absent": ["周雨馨"],
        "resigned": ["赵红丽"],
        "in_lieu": ["李景均"]
    }

    说明：
    - attendance: 正常出勤人员
    - leave: 请假人员
    - absent: 未到岗人员
    - in_lieu: 调休人员（独立分类）
    - resigned: 自离人员（仅当天显示）
    """
    try:
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta

        data = request.get_json()
        date_str = data.get('date')
        shift = data.get('shift', '白班')
        attendance = data.get('attendance', {})
        leave = data.get('leave', [])
        absent = data.get('absent', [])
        resigned = data.get('resigned', [])
        new_employee = data.get('new_employee', [])
        in_lieu = data.get('in_lieu', [])

        # 班别映射
        shift_mapping = {
            '白班': ('白班', 11),
            '夜班': ('夜班', 11.5),
            '长白班': ('长白班', 11)
        }

        shift_type, hours = shift_mapping.get(shift, ('白班', 11))

        db = get_db()
        total_added = 0
        total_updated = 0
        users_created = []
        results = []

        # 通用: 根据用户名查找或创建用户
        def find_or_create_user(username):
            user_row = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if user_row:
                return user_row['id'], False
            hashed_pwd = generate_password_hash('1')
            cur = db.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, hashed_pwd)
            )
            users_created.append(username)
            return cur.lastrowid, True

        # 通用: 为用户写入一条工时记录
        def write_record(user_id, shift, start, end, dur, desc, is_leave_flag):
            existing_row = db.execute(
                'SELECT id FROM time_records WHERE user_id = ? AND DATE(start_time) = ?',
                (user_id, date_str)
            ).fetchone()
            if existing_row:
                db.execute(
                    '''UPDATE time_records
                       SET start_time=?, end_time=?, shift_type=?,
                           duration=?, description=?, is_leave=? WHERE id=?''',
                    (start, end, shift, dur, desc, is_leave_flag, existing_row['id'])
                )
                return 'updated'
            db.execute(
                '''INSERT INTO time_records
                   (user_id, start_time, end_time, duration, shift_type, description, is_leave)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, start, end, dur, shift, desc, is_leave_flag)
            )
            return 'added'

        # 通用: 清理用户旧角色, 仅保留指定角色(新员工/自离等不在此流程中使用)
        # ★ 使用关键字匹配映射到基础岗位
        def set_user_role(user_id, role_name):
            from utils.role_mapping import get_base_role
            base_role = get_base_role(role_name)

            db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
            role_row = db.execute('SELECT id FROM roles WHERE name = ?', (base_role,)).fetchone()
            if role_row:
                db.execute(
                    'INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)',
                    (user_id, role_row['id'])
                )

        # 计算上下班时间
        if shift_type == '夜班':
            start_time_str = f"{date_str} 20:00:00"
            tomorrow_date = datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)
            end_time_str = f"{tomorrow_date.strftime('%Y-%m-%d')} 06:00:00"
        else:
            start_time_str = f"{date_str} 08:00:00"
            end_time_str = f"{date_str} 18:00:00"

        duration_minutes = int(hours * 60)

        # 1. 处理出勤人员
        for role_name, members in attendance.items():
            if not members:
                continue
            if not isinstance(members, list):
                members = [members]
            for username in members:
                username = username.strip()
                if not username:
                    continue
                user_id, _ = find_or_create_user(username)
                db.execute('UPDATE users SET shift_type = ? WHERE id = ?', (shift_type, user_id))
                set_user_role(user_id, role_name)
                status = write_record(user_id, shift_type, start_time_str, end_time_str, duration_minutes, '', 0)
                if status == 'added':
                    total_added += 1
                else:
                    total_updated += 1
                results.append({'username': username, 'status': status, 'role': role_name})

        # 2. 处理请假人员 (is_leave=1, description='请假') — 清理旧角色避免与调休混淆
        for username in leave:
            username = username.strip()
            if not username:
                continue
            user_id, _ = find_or_create_user(username)
            db.execute('UPDATE users SET shift_type = ? WHERE id = ?', (shift_type, user_id))
            # 清理旧角色，避免角色判断覆盖description判断
            db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
            status = write_record(user_id, shift_type, start_time_str, end_time_str, 0, '请假', 1)
            if status == 'added':
                total_added += 1
            else:
                total_updated += 1
            results.append({'username': username, 'status': status, 'role': '请假'})

        # 3. 处理未到岗人员 (is_leave=1, description='未到岗') — 清理旧角色
        for username in absent:
            username = username.strip()
            if not username:
                continue
            user_id, _ = find_or_create_user(username)
            db.execute('UPDATE users SET shift_type = ? WHERE id = ?', (shift_type, user_id))
            # 清理旧角色，避免角色判断覆盖description判断
            db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
            status = write_record(user_id, shift_type, start_time_str, end_time_str, 0, '未到岗', 1)
            if status == 'added':
                total_added += 1
            else:
                total_updated += 1
            results.append({'username': username, 'status': status, 'role': '未到岗'})

        # 4. 处理自离人员 (is_leave=1, description='自离') — 仅当天考勤记录标记，不再写角色
        for username in resigned:
            username = username.strip()
            if not username:
                continue
            user_id, _ = find_or_create_user(username)
            user_id = int(user_id)  # ★ 确保是 int 类型
            db.execute('UPDATE users SET shift_type = ? WHERE id = ?', (shift_type, user_id))
            # ★ 清理历史角色关联（避免看板显示在原岗位下）
            db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id))
            # ★ 新逻辑：不再给"自离"用户添加角色，只在当天工时记录 description 标记为"自离"
            # 这样第二天若没有新的考勤记录，看板上就不会再显示此人
            status = write_record(user_id, shift_type, start_time_str, end_time_str, 0, '自离', 1)
            if status == 'added':
                total_added += 1
            else:
                total_updated += 1
            results.append({'username': username, 'status': status, 'role': '自离'})

        # 5. 处理调休人员 (is_leave=1, description='调休') — 独立分类
        for username in in_lieu:
            username = username.strip()
            if not username:
                continue
            user_id, _ = find_or_create_user(username)
            db.execute('UPDATE users SET shift_type = ? WHERE id = ?', (shift_type, user_id))
            # 调休人员不写入角色表，仅在当天工时记录 description 标记为"调休"
            status = write_record(user_id, shift_type, start_time_str, end_time_str, 0, '调休', 1)
            if status == 'added':
                total_added += 1
            else:
                total_updated += 1
            results.append({'username': username, 'status': status, 'role': '调休'})

        # 6. 处理新员工 (is_leave=0, 角色='新员工')
        for username in new_employee:
            username = username.strip()
            if not username:
                continue
            user_id, is_new = find_or_create_user(username)
            db.execute('UPDATE users SET shift_type = ? WHERE id = ?', (shift_type, user_id))
            # 清除旧角色，设置'新员工'角色
            db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
            role_row = db.execute("SELECT id FROM roles WHERE name = '新员工'").fetchone()
            if role_row:
                db.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, role_row['id']))
            else:
                cur = db.execute("INSERT INTO roles (name) VALUES ('新员工')")
                db.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, cur.lastrowid))
            status = write_record(user_id, shift_type, start_time_str, end_time_str, duration_minutes, '', 0)
            if status == 'added':
                total_added += 1
            else:
                total_updated += 1
            results.append({'username': username, 'status': status, 'role': '新员工'})

        db.commit()

        # 统计
        attend_count = db.execute(
            '''SELECT COUNT(DISTINCT user_id) FROM time_records
               WHERE DATE(start_time)=? AND is_leave=0''', (date_str,)
        ).fetchone()[0]

        leave_count = db.execute(
            '''SELECT COUNT(DISTINCT user_id) FROM time_records
               WHERE DATE(start_time)=? AND is_leave=1''', (date_str,)
        ).fetchone()[0]

        in_lieu_count = len(in_lieu)

        return jsonify({
            'message': '出勤数据添加成功',
            'date': date_str,
            'shift': shift,
            'shift_type': shift_type,
            'attend_count': attend_count,
            'leave_count': leave_count,
            'in_lieu_count': in_lieu_count,
            'new_employee_count': len(new_employee),
            'total_count': attend_count + leave_count,
            'added': total_added,
            'updated': total_updated,
            'users_created': users_created,
            'results': results
        }), 200

    except Exception as e:
        logging.error(f"批量添加入勤数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 文本解析导入接口（考勤技能 - 中文文本一键导入）
@app.route('/api/attendance/text-import', methods=['POST'])
def text_import_attendance():
    """中文文本解析导入

    支持格式：在请求体中发送纯文本，系统自动解析岗位和人员

    POST Body 示例:
        6月11日，白班应出36人，实际出勤32人，请假1人，自离3人，
        配料：刘虎、蒋江坤、黄春、宋春祥、郑成功
        正1D836涂布人员：李景均、李培嘉
        正2D648涂布人员：林树良、姚艺
        正3A322涂布人员：王硕、洪安飞
        负1D836涂布人员：杨武、张全忠
        负2D648涂布人员：高子昂、尉李峰
        负3A322涂布人员：张瑞鼎、彭晓康、李杰
        正1A322辊压人员：张世运、任保帅
        正2D648辊压人员：惠留阳
        负1D648/C951辊压人员：张治衡
        负2A322辊压人员：王新龙、王腾
        正极激光切人员：李新杰、苏景航
        负极激光切人员：韦承泽
        发片人员：王忠江
        物料：赵恩辉
        领班：单文线、王金浩
        主管：黎俊
        请假：宁福
        自离：赵红丽、韦广阔、周雨馨

    返回: 与 batch-add 相同的 JSON 格式
    """
    try:
        from utils.attendance_parser import parse_attendance_text

        # 支持两种输入：raw text 或 {"text": "..."}
        content_type = request.content_type or ''
        if 'application/json' in content_type:
            data = request.get_json()
            text = data.get('text', '') if data else ''
        else:
            text = request.get_data(as_text=True)

        if not text:
            return jsonify({'error': '请输入考勤文本'}), 400

        # 解析文本
        parsed = parse_attendance_text(text)

        # 直接调用 batch_add_attendance 函数（而非通过 test_client）
        # 创建一个模拟的 request 对象
        from flask import Request
        mock_data = {
            'date': parsed['date'],
            'shift': parsed['shift'],
            'attendance': parsed['attendance'],
            'leave': parsed['leave'],
            'absent': parsed['absent'],
            'in_lieu': parsed.get('in_lieu', []),
            'resigned': parsed['resigned']
        }

        # 直接调用 batch_add_attendance（它内部会处理数据）
        # 使用 app.test_request_context 创建请求上下文
        with app.test_request_context('/api/attendance/batch-add', method='POST', json=mock_data):
            result = batch_add_attendance()
            # batch_add_attendance 返回的是 (jsonify_result, status_code)
            if isinstance(result, tuple):
                response_data, status_code = result
                response_json = response_data.get_json()
            else:
                response_json = result.get_json()
                status_code = 200

        # 增加解析结果信息（方便前端展示）
        response_json['parsed_date'] = parsed['date']
        response_json['parsed_shift'] = parsed['shift']
        response_json['parsed_roles'] = list(parsed['attendance'].keys())
        response_json['parsed_leave'] = parsed['leave']
        response_json['parsed_absent'] = parsed['absent']
        response_json['parsed_in_lieu'] = parsed.get('in_lieu', [])
        response_json['parsed_resigned'] = parsed['resigned']

        return jsonify(response_json), status_code

    except Exception as e:
        logging.error(f"文本导入考勤失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/import-prev-day', methods=['POST'])
def import_prev_day_attendance():
    """导入前一天出勤数据

    POST Body:
        {
            "prev_date": "2026-06-14",
            "target_date": "2026-06-15",
            "shift": "day" | "night" | "all",
            "override": true | false
        }

    返回:
        {
            "message": "导入成功",
            "copied_count": 30,
            "prev_total": 30,
            "target_total": 30
        }
    """
    try:
        data = request.get_json()
        prev_date = data.get('prev_date')
        target_date = data.get('target_date')
        shift = data.get('shift', 'all')
        override = data.get('override', False)

        if not prev_date or not target_date:
            return jsonify({'error': '缺少日期参数'}), 400

        db = get_db()

        # 如果选择覆盖，先删除目标日期的记录
        deleted_count = 0
        if override:
            if shift == 'all':
                delete_cursor = db.execute(
                    "DELETE FROM time_records WHERE DATE(start_time) = ?",
                    (target_date,)
                )
            else:
                shift_type_map = {'day': '白班', 'night': '夜班', 'long': '长白班'}
                shift_type = shift_type_map.get(shift, shift)
                delete_cursor = db.execute(
                    "DELETE FROM time_records WHERE DATE(start_time) = ? AND shift_type = ?",
                    (target_date, shift_type)
                )
            deleted_count = delete_cursor.rowcount
            db.commit()

        # 查询前一天的记录
        if shift == 'all':
            prev_records = db.execute(
                """SELECT user_id, shift_type, start_time, end_time,
                          duration, is_leave, description, leave_hours,
                          is_early_leave, is_early_off
                   FROM time_records WHERE DATE(start_time) = ?""",
                (prev_date,)
            ).fetchall()
        else:
            shift_type_map = {'day': '白班', 'night': '夜班', 'long': '长白班'}
            shift_type = shift_type_map.get(shift, shift)
            prev_records = db.execute(
                """SELECT user_id, shift_type, start_time, end_time,
                          duration, is_leave, description, leave_hours,
                          is_early_leave, is_early_off
                   FROM time_records WHERE DATE(start_time) = ? AND shift_type = ?""",
                (prev_date, shift_type)
            ).fetchall()

        if not prev_records:
            return jsonify({
                'message': '前一天无出勤记录',
                'copied_count': 0,
                'prev_total': 0,
                'deleted_count': deleted_count
            }), 200

        # 复制记录到目标日期
        copied_count = 0
        for record in prev_records:
            # 转换日期：保持时间部分，只替换日期
            prev_start = record['start_time']
            prev_end = record['end_time']

            # 构造新的时间字符串
            if prev_start:
                # 格式：YYYY-MM-DD HH:MM:SS
                new_start = target_date + ' ' + prev_start.split(' ')[1] if ' ' in prev_start else target_date + ' 08:00:00'
            else:
                new_start = target_date + ' 08:00:00'

            if prev_end:
                new_end = target_date + ' ' + prev_end.split(' ')[1] if ' ' in prev_end else target_date + ' 19:30:00'
            else:
                new_end = target_date + ' 19:30:00'

            # 检查是否已存在（非覆盖模式）
            if not override:
                existing = db.execute(
                    """SELECT id FROM time_records
                       WHERE DATE(start_time) = ? AND user_id = ? AND shift_type = ?""",
                    (target_date, record['user_id'], record['shift_type'])
                ).fetchone()
                if existing:
                    continue  # 跳过已存在的记录

            # 插入新记录
            db.execute(
                """INSERT INTO time_records
                   (user_id, shift_type, start_time, end_time, duration,
                    is_leave, description, leave_hours, is_early_leave, is_early_off)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record['user_id'], record['shift_type'], new_start, new_end,
                 record['duration'], record['is_leave'], record['description'],
                 record['leave_hours'], record['is_early_leave'], record['is_early_off'])
            )
            copied_count += 1

        db.commit()

        # 统计结果
        target_total = db.execute(
            "SELECT COUNT(*) as cnt FROM time_records WHERE DATE(start_time) = ?",
            (target_date,)
        ).fetchone()['cnt']

        return jsonify({
            'message': '导入成功',
            'copied_count': copied_count,
            'prev_total': len(prev_records),
            'target_total': target_total,
            'deleted_count': deleted_count
        }), 200

    except Exception as e:
        logging.error(f"导入前一天数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/batch-delete', methods=['POST'])
def batch_delete_attendance():
    """批量删除考勤记录

    POST Body:
        {
            "date": "2026-06-15",
            "shift": "all" | "白班" | "夜班" | "长白班",
            "names": ["张三", "李四", "王五"]
        }

    返回:
        {
            "message": "删除成功",
            "deleted_count": 3,
            "deleted_names": ["张三", "李四", "王五"]
        }
    """
    try:
        data = request.get_json()
        date = data.get('date')
        shift = data.get('shift', 'all')
        names = data.get('names', [])

        if not date or not names:
            return jsonify({'error': '缺少日期或人员名单'}), 400

        db = get_db()

        deleted_count = 0
        deleted_names = []

        for name in names:
            name = name.strip()
            if not name:
                continue

            # 查找用户
            user = db.execute(
                "SELECT id, username FROM users WHERE username = ? OR username LIKE ?",
                (name, f'%{name}%')
            ).fetchone()

            if not user:
                continue

            # 删除记录
            if shift == 'all':
                cursor = db.execute(
                    "DELETE FROM time_records WHERE DATE(start_time) = ? AND user_id = ?",
                    (date, user['id'])
                )
            else:
                cursor = db.execute(
                    "DELETE FROM time_records WHERE DATE(start_time) = ? AND user_id = ? AND shift_type = ?",
                    (date, user['id'], shift)
                )

            if cursor.rowcount > 0:
                deleted_count += cursor.rowcount
                deleted_names.append(user['username'])

        db.commit()

        return jsonify({
            'message': '删除成功',
            'deleted_count': deleted_count,
            'deleted_names': deleted_names
        }), 200

    except Exception as e:
        logging.error(f"批量删除考勤失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# =============================================
# 数据体检API
# =============================================
@app.route('/api/admin/checkup', methods=['GET'])
def admin_checkup():
    """数据体检 - 检查数据库健康度

    GET /api/admin/checkup

    返回体检报告：
    - health_score: 健康评分（0-100）
    - health_level: 健康等级（excellent/good/warning/critical）
    - stats: 基础统计（用户数、记录数等）
    - summary: 问题汇总（严重/警告/提示数量）
    - issues: 问题详情列表
    """
    try:
        from utils.data_health_checker import DataHealthChecker
        checker = DataHealthChecker(get_db())
        report = checker.run_all_checks()
        return jsonify(report), 200
    except Exception as e:
        logging.error(f"数据体检失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/checkup/<category>/fix', methods=['POST'])
def admin_checkup_fix(category):
    """自动修复指定类别的问题

    POST /api/admin/checkup/{category}/fix

    支持的 category:
    - duplicate_records: 重复工时记录（保留最早，删除其余）
    - orphan_users: 孤立用户记录（删除）
    - abnormal_dates: 日期异常记录（删除）

    注意：warning/info级别的问题暂无自动修复，需要手动处理。
    """
    try:
        # 定义可自动修复的SQL
        fix_sqls = {
            'duplicate_records': (
                '''DELETE FROM time_records
                   WHERE id NOT IN (
                       SELECT MIN(id) FROM time_records
                       GROUP BY user_id, DATE(start_time)
                   )''',
                None
            ),
            'orphan_users': (
                '''DELETE FROM time_records
                   WHERE user_id NOT IN (SELECT id FROM users)''',
                None
            ),
            'abnormal_dates': (
                '''DELETE FROM time_records
                   WHERE DATE(start_time) < '2024-01-01'
                      OR DATE(start_time) > date('now', '+7 days')''',
                None
            ),
        }

        if category not in fix_sqls:
            return jsonify({'error': f'不支持的修复类别: {category}'}), 400

        sql, params = fix_sqls[category]
        db = get_db()
        cur = db.execute(sql, params or ())
        db.commit()

        return jsonify({
            'success': True,
            'message': f'已修复 {category}，影响 {cur.rowcount} 条记录',
            'affected': cur.rowcount
        }), 200

    except Exception as e:
        logging.error(f"自动修复失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 岗位API
@app.route('/api/positions', methods=['GET'])
def get_positions():
    """获取岗位列表"""
    try:
        db = get_db()
        # 从 roles 表获取所有岗位名称
        roles = db.execute('SELECT name FROM roles ORDER BY name').fetchall()
        positions = [r['name'] for r in roles]
        
        # 如果没有岗位，返回默认列表
        if not positions:
            positions = ['配料', '涂布', '辊压', '分条', '发片', '领班', '物料', '主管']
        
        return jsonify({'positions': positions}), 200
    except Exception as e:
        logging.error(f"获取岗位列表失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['POST'])
def add_position():
    """添加新岗位"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'error': '岗位名称不能为空'}), 400
        
        db = get_db()
        
        # 检查岗位是否已存在
        existing = db.execute('SELECT id FROM roles WHERE name = ?', (name,)).fetchone()
        if not existing:
            db.execute('INSERT INTO roles (name) VALUES (?)', (name,))
            db.commit()
        
        # 返回所有岗位
        roles = db.execute('SELECT name FROM roles ORDER BY name').fetchall()
        positions = [r['name'] for r in roles]
        
        return jsonify({'positions': positions}), 201
    except Exception as e:
        logging.error(f"添加岗位失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 获取单个用户当天考勤记录
@app.route('/api/attendance/user-record', methods=['GET'])
def get_user_attendance_record():
    """获取指定用户当天的考勤记录，用于编辑弹窗"""
    try:
        user_id = request.args.get('user_id')
        date_str = request.args.get('date')

        if not user_id or not date_str:
            return jsonify({'error': '缺少必要参数'}), 400

        db = get_db()

        # 获取用户基本信息
        user = db.execute('SELECT id, username, shift_type FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 获取该用户当天最新的工时记录
        record = db.execute("""
            SELECT id, shift_type, duration, is_leave, description,
                   DATE(start_time) as date
            FROM time_records
            WHERE user_id = ? AND DATE(start_time) = ?
            ORDER BY id DESC
            LIMIT 1
        """, (user_id, date_str)).fetchone()

        # 获取用户的岗位角色
        role_rows = db.execute("""
            SELECT r.name as role_name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = ?
        """, (user_id,)).fetchall()

        role_names = [row['role_name'] for row in role_rows] if role_rows else []
        primary_role = role_names[0] if role_names else None
        logging.info(f"[get_user_attendance_record] user_id={user_id}, date={date_str}, primary_role='{primary_role}', roles={role_names}")

        # 构建返回数据
        result = {
            'user_id': user['id'],
            'username': user['username'],
            'shift_type': user['shift_type'],
            'record': None,
            'roleName': primary_role,
            'roles': role_names
        }

        if record:
            desc = record['description'] or ''
            # 根据 description 细化工时状态（调休/年假/未到岗 都有特殊 description）
            if desc == '调休':
                status_text = '调休'
            elif desc == '年假':
                status_text = '年假'
            elif desc == '未到岗':
                status_text = '未到岗'
            elif record['is_leave']:
                status_text = '请假'
            else:
                status_text = '出勤'

            result['record'] = {
                'id': record['id'],
                'shift_type': record['shift_type'],
                'hours': (record['duration'] or 0) / 60 if record['duration'] else 0,
                'status': status_text,
                'remark': record['description'] or '',
                'role': primary_role  # 前端期望的 role 字段
            }

        return jsonify(result), 200

    except Exception as e:
        logging.error(f"获取考勤记录失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 出勤保存API
@app.route('/api/attendance/save', methods=['POST'])
def save_attendance():
    """保存出勤信息"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        date_str = data.get('date')
        status = data.get('status')
        shift_type = data.get('shift_type')
        hours = data.get('hours', 0)
        early_leave = data.get('early_leave', False)
        role = data.get('role')
        remark = data.get('remark', '')
        
        if not user_id or not date_str:
            return jsonify({'error': '缺少必要参数'}), 400
        
        db = get_db()
        
        # 检查用户是否存在
        user = db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 更新用户的班别（如果有）
        if shift_type:
            db.execute('UPDATE users SET shift_type = ? WHERE id = ?', (shift_type, user_id))
        
        # 如果标记为自离，跳过角色更新（自离角色已由 mark-resigned API 设置）
        is_resigned = data.get('is_resigned', False)

        # 防呆：如果状态是正常出勤，但 role 却是特殊状态（调休/请假等），覆盖为默认岗位
        special_statuses_for_role = ['请假', '调休', '年假', '未到岗']
        is_special = status in special_statuses_for_role
        if not is_special and role in special_statuses_for_role:
            logging.info(f"[save_attendance] user_id={user_id} status='{status}' 但 role='{role}'，覆盖 role 为默认")
            recent_record = db.execute(
                "SELECT description FROM time_records WHERE user_id = ? AND is_leave = 0 AND description NOT IN ('请假', '调休', '年假', '未到岗') AND description != '' ORDER BY start_time DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            if recent_record and recent_record['description']:
                role = recent_record['description']
            else:
                role_record = db.execute(
                    "SELECT r.name as role_name FROM user_roles ur JOIN roles r ON ur.role_id = r.id WHERE ur.user_id = ?",
                    (user_id,)
                ).fetchone()
                if role_record and role_record['role_name'] not in special_statuses_for_role:
                    role = role_record['role_name']
                else:
                    role = '一一车间'

        logging.info(f"[save_attendance] user_id={user_id}, role='{role}', is_resigned={is_resigned}")
        if role and not is_resigned:
            # 先清除该用户的旧角色
            db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
            # 获取或创建角色
            role_obj = db.execute('SELECT id FROM roles WHERE name = ?', (role,)).fetchone()
            if role_obj:
                role_id = role_obj['id']
                logging.info(f"[save_attendance] Found existing role '{role}' with id={role_id}")
            else:
                # 创建新角色
                cursor = db.execute('INSERT INTO roles (name) VALUES (?)', (role,))
                role_id = cursor.lastrowid
                logging.info(f"[save_attendance] Created new role '{role}' with id={role_id}")
            # 分配角色给用户
            db.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, role_id))
            logging.info(f"[save_attendance] Assigned role '{role}' (id={role_id}) to user_id={user_id}")
        elif not is_resigned:
            # 没有显式传入岗位时，尝试从历史 description 推断并自动设置
            inferred = _infer_role_from_descriptions(db, user_id, remark)
            if inferred:
                existing_roles = db.execute("""
                    SELECT r.name as role_name
                    FROM user_roles ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = ?
                """, (user_id,)).fetchall()
                has_base = any(r['role_name'] in BASE_ROLES for r in existing_roles)
                if not has_base:
                    # 清除非基础岗位的角色，设置新的推断岗位
                    db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
                    role_obj = db.execute(
                        'SELECT id FROM roles WHERE name = ?', (inferred,)
                    ).fetchone()
                    if role_obj:
                        role_id = role_obj['id']
                    else:
                        cursor = db.execute(
                            'INSERT INTO roles (name) VALUES (?)', (inferred,)
                        )
                        role_id = cursor.lastrowid
                    db.execute(
                        'INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)',
                        (user_id, role_id)
                    )
        
        # 根据 status 决定 description、is_leave 和 duration
        # 特殊状态（请假/调休/年假/未到岗）：description=status, is_leave=1, duration=0
        # 正常出勤：description=remark, is_leave=0, duration=normalized
        special_statuses = ['请假', '调休', '年假', '未到岗']
        is_special_status = status in special_statuses

        if is_special_status:
            save_description = status  # 如 "调休"
            save_is_leave = 1
            save_duration = 0
        else:
            save_description = remark or ''
            save_is_leave = 0

        # 查找当天是否已有工时记录
        start_time_str = f"{date_str} 08:00:00"
        end_time_str = f"{date_str} 18:00:00"
        raw_hours = hours if hours else 0

        def normalize_duration(hours):
            """将工时转换为30分钟的倍数"""
            minutes = int(hours * 60)
            if minutes <= 0:
                return 0
            # 四舍五入到最接近的30分钟倍数
            normalized = round(minutes / 30) * 30
            if normalized != minutes:
                logging.info(f"[save_attendance] 工时 {minutes}分钟 调整为30分钟倍数 {normalized}分钟")
            return normalized

        if is_special_status:
            duration = 0
        else:
            duration = normalize_duration(raw_hours) if raw_hours else 600
        
        existing_record = db.execute(
            'SELECT id FROM time_records WHERE user_id = ? AND DATE(start_time) = ?',
            (user_id, date_str)
        ).fetchone()
        
        if existing_record:
            # 更新已有记录
            if is_resigned:
                # 自离状态：保持 mark-resigned API 设置的自离格式 description，只更新班次、is_leave=0、duration=0
                db.execute(
                    '''UPDATE time_records 
                    SET shift_type = ?, is_leave = 0, duration = 0
                    WHERE id = ?''',
                    (shift_type, existing_record['id'])
                )
            else:
                db.execute(
                    '''UPDATE time_records 
                    SET shift_type = ?, duration = ?, description = ?, is_leave = ?
                    WHERE id = ?''',
                    (shift_type, save_duration if is_special_status else duration, save_description, save_is_leave, existing_record['id'])
                )
        else:
            # 创建新记录
            if is_resigned:
                # 自离状态：使用自离格式（mark-resigned API 已经设置了，这里不应走到，但兜底）
                resigned_desc = f"自离|原岗位:{role}|原工时:{duration}|原班次:{shift_type}"
                db.execute(
                    '''INSERT INTO time_records 
                    (user_id, start_time, end_time, duration, shift_type, description, is_leave)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, start_time_str, end_time_str, 0, shift_type, resigned_desc, 0)
                )
            else:
                db.execute(
                    '''INSERT INTO time_records 
                    (user_id, start_time, end_time, duration, shift_type, description, is_leave)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, start_time_str, end_time_str, save_duration if is_special_status else duration, shift_type, save_description, save_is_leave)
                )
        
        db.commit()

        return jsonify({'message': '保存成功'}), 200
    except Exception as e:
        logging.error(f"保存出勤失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _infer_role_from_descriptions(db, user_id, current_desc):
    """从 time_records.description 字段中推断岗位

    策略：
    1. 优先使用当天记录的 description
    2. 再查询最近 30 天的 time_records.description 提取岗位关键词
    3. 用 get_base_role 将文本映射到基础岗位

    Args:
        db: 数据库连接
        user_id: 用户ID
        current_desc: 当前记录的 description（当天考勤中的文本）

    Returns:
        基础岗位名称（如 '配料'、'涂布' 等）或 None
    """
    if not user_id:
        return None

    # 1. 收集候选文本
    candidate_texts = []
    if current_desc:
        candidate_texts.append(current_desc)

    # 2. 查询最近 30 天的 time_records.description
    try:
        recent_rows = db.execute("""
            SELECT COALESCE(description, '') as desc_text
            FROM time_records
            WHERE user_id = ?
              AND description IS NOT NULL
              AND description != ''
              AND start_time >= datetime('now', '-30 days')
            ORDER BY start_time DESC
            LIMIT 10
        """, (user_id,)).fetchall()

        for row in recent_rows:
            if row['desc_text'] and row['desc_text'] not in candidate_texts:
                candidate_texts.append(row['desc_text'])
    except Exception:
        pass

    # 3. 尝试从这些文本中推断岗位
    for text in candidate_texts:
        mapped = get_base_role(text)
        if mapped and mapped in BASE_ROLES:
            return mapped

    # 4. 兜底：直接检查关键字包含
    for text in candidate_texts:
        for keyword, base_role in [
            ('配料', '配料'), ('辊压', '辊压'), ('涂布', '涂布'),
            ('分条', '激光切'), ('激光切', '激光切'), ('职能', '职能'),
            ('物料员', '物料'), ('物料', '物料'), ('主管', '主管'),
            ('领班', '领班'), ('发片', '发片'),
        ]:
            if keyword in text:
                return base_role

    return None


# 获取按角色分类的出勤名单API
@app.route('/api/attendance/list', methods=['GET'])
def get_attendance_list():
    """获取出勤名单（两阶段加载：quick=1 仅工时，full=1 或默认含角色分组）"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        shift_filter = request.args.get('shift', 'all')  # 班别筛选：all, day, night, long
        mode = request.args.get('mode', 'full')  # 'quick' 仅返回工时用户 | 'full' 返回分组看板

        db = get_db()

        # 班别筛选
        shift_conditions = {
            'day': "tr.shift_type = '白班'",
            'night': "tr.shift_type = '夜班'",
            'long': "tr.shift_type = '长白班'"
        }

        # ★ 用范围查询替代 DATE() 函数，确保能走 idx_time_records_start_time 索引
        where_clause = "tr.start_time >= ? AND tr.start_time < ?"
        params = [date, date + 'Z']

        if shift_filter in shift_conditions:
            where_clause += f" AND {shift_conditions[shift_filter]}"

        # === 第一步：一次性获取当天有工时记录的用户（去除 GROUP BY，改为 DISTINCT）===
        # ★ 关键性能修复：用 start_time 前缀范围查询替代 DATE() 函数，使其可以走索引
        # 增加 duration 字段，用于后续计算 work_count 和 total_duration（与分组逻辑天然一致）
        # 兼容 '2026-06-09' / '2026-06-09 08:00:00' / '2026-06-09T08:00:00' 三种格式
        attendance_query = f'''
            SELECT DISTINCT
                u.id as user_id,
                u.username,
                tr.shift_type,
                tr.is_leave,
                COALESCE(tr.description, '') as description,
                COALESCE(tr.duration, 0) as duration
            FROM time_records tr
            JOIN users u ON tr.user_id = u.id
            WHERE tr.start_time >= ? AND tr.start_time < ?
        '''
        if shift_filter in shift_conditions:
            attendance_query += f" AND {shift_conditions[shift_filter]}"
        attendance_query += " ORDER BY u.username"
        attendance_rows = db.execute(
            attendance_query,
            [date, date + 'Z']
        ).fetchall()

        # === 模式 quick：只返回扁平化列表，秒开页面 ===
        if mode == 'quick':
            all_records = []
            leave_users_quick = []
            for row in attendance_rows:
                uid = row['user_id']
                uname = row['username']
                stype = row['shift_type'] if 'shift_type' in row.keys() else ''
                is_leave = row['is_leave'] if 'is_leave' in row.keys() else 0
                item = {
                    'user_id': uid,
                    'username': uname,
                    'shift_type': stype,
                    'is_leave': bool(is_leave)
                }
                if is_leave:
                    leave_users_quick.append(item)
                else:
                    all_records.append(item)

            return jsonify({
                'date': date,
                'mode': 'quick',
                'total_count': len(attendance_rows),
                'work_users': all_records,
                'leave_users': leave_users_quick
            })

        # 角色优先级（9个基础岗位 + 4个特殊状态）
        role_priority = ['配料', '涂布', '辊压', '激光切', '发片', '领班', '主管', '物料', '职能', '支援', '新员工', '调休', '自离', '未到岗']

        # === 阶段 B：查询所有用户的角色（IN 查询，一次完成）===
        all_user_ids = [row['user_id'] for row in attendance_rows]
        all_roles_by_user = {}

        if all_user_ids:
            placeholders = ','.join('?' * len(all_user_ids))
            roles_rows = db.execute(f"""
                SELECT ur.user_id, r.name as role_name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id IN ({placeholders})
            """, all_user_ids).fetchall()
            for r in roles_rows:
                all_roles_by_user.setdefault(r['user_id'], []).append(r['role_name'])
        
        # === 第三步：按角色分类组织数据（纯内存操作，无DB查询）===
        role_data = {}
        leave_users = []
        absent_users = []
        resigned_users = []
        new_employee_users = []
        in_lieu_users = []
        user_processed = set()
        work_count_val = 0
        total_duration_minutes = 0

        for row in attendance_rows:
            user_id = row['user_id']
            username = row['username']
            shift_type = row['shift_type'] if 'shift_type' in row.keys() else '未知'
            is_leave = row['is_leave'] if 'is_leave' in row.keys() else 0
            desc = (row['description'] if 'description' in row.keys() else '') or ''
            duration = row['duration'] if 'duration' in row.keys() else 0

            if user_id in user_processed:
                continue

            # === 阶段A：基于 description 的优先判断（优先级最高） ===
            # 1. 未到岗 (description='未到岗')
            if desc == '未到岗':
                absent_users.append({
                    'user_id': user_id,
                    'username': username,
                    'shift_type': shift_type
                })
                user_processed.add(user_id)
                continue

            # 2. 调休 (description='调休')
            if desc == '调休':
                in_lieu_users.append({
                    'user_id': user_id,
                    'username': username,
                    'shift_type': shift_type
                })
                user_processed.add(user_id)
                continue

            # 3. 自离 (description 以 '自离' 开头)
            if desc and desc.startswith('自离'):
                resigned_users.append({
                    'user_id': user_id,
                    'username': username,
                    'shift_type': shift_type,
                    'is_resigned': True
                })
                user_processed.add(user_id)
                continue

            # 4. 请假 (description='请假')
            if desc == '请假' or is_leave:
                leave_users.append({
                    'user_id': user_id,
                    'username': username,
                    'shift_type': shift_type
                })
                user_processed.add(user_id)
                continue

            # === 阶段B：基于角色的备选判断（description为空时使用） ===
            user_roles = all_roles_by_user.get(user_id, [])

            # 调休角色兜底
            if '调休' in user_roles:
                in_lieu_users.append({
                    'user_id': user_id,
                    'username': username,
                    'shift_type': shift_type
                })
                user_processed.add(user_id)
                continue

            # 自离角色兜底
            if '自离' in user_roles:
                resigned_users.append({
                    'user_id': user_id,
                    'username': username,
                    'shift_type': shift_type,
                    'is_resigned': True
                })
                user_processed.add(user_id)
                continue

            # 如果没有角色分配，先尝试从当天/历史 description 推断岗位
            if not user_roles:
                inferred = _infer_role_from_descriptions(db, user_id, desc)
                if inferred:
                    user_roles = [inferred]

            # 再根据名字推断角色（兜底逻辑）
            if not user_roles:
                if username in ['范晓鹏', '范小鹏']:
                    user_roles = ['发片']
                elif username in ['李名', '单文线', '王金浩']:
                    user_roles = ['领班']
                elif username in ['赵恩辉']:
                    user_roles = ['物料']
                elif username in ['吕赛浦', '毛春华', '翟万淇']:
                    user_roles = ['激光切']
                elif username in ['周雨馨']:
                    user_roles = []

            # 选择优先级最高的角色
            primary_role = None
            for role in role_priority:
                if role in user_roles:
                    primary_role = role
                    break

            if not primary_role:
                primary_role = user_roles[0] if user_roles else '其他'

            if primary_role not in role_data:
                role_data[primary_role] = []

            role_data[primary_role].append({
                'user_id': user_id,
                'username': username,
                'shift_type': shift_type,
                'is_new_employee': '新员工' in user_roles
            })

            # 正常岗位：计入实际出勤人数和工时（与分组逻辑一致）
            work_count_val += 1
            total_duration_minutes += duration

            user_processed.add(user_id)
        
        # === 第四步：自离人员兜底查询（从角色表查，兼容旧数据）===
        # 新版: 优先从 description='自离' 识别; 这里保留旧逻辑兜底
        resigned_result = db.execute("""
            SELECT DISTINCT u.id as user_id, u.username, tr.shift_type
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            JOIN time_records tr ON tr.user_id = u.id
            WHERE r.name = '自离'
              AND tr.start_time >= ? AND tr.start_time < ?
              {}
            ORDER BY u.username
        """.format(f" AND {shift_conditions[shift_filter]}" if shift_filter in shift_conditions else ""), [date, date + 'Z']).fetchall()

        for row in resigned_result:
            user_id = row['user_id']
            if user_id in user_processed:
                continue
            resigned_users.append({
                'user_id': user_id,
                'username': row['username'],
                'shift_type': row['shift_type'] or '夜班',
                'is_resigned': True
            })
            user_processed.add(user_id)

        # 把请假、未到岗、调休、自离组加入分组数据（都计入应出人数）
        if leave_users:
            role_data['请假'] = leave_users
        if absent_users:
            role_data['未到岗'] = absent_users
        if in_lieu_users:
            role_data['调休'] = in_lieu_users
        if resigned_users:
            role_data['自离'] = resigned_users

        # === 第五步：新员工查询（只有新员工角色且当天无工时记录）===
        # 先一次性获取所有新员工用户ID及其角色数
        new_emp_query = '''
            SELECT u.id as user_id, u.username, u.shift_type,
                   (SELECT COUNT(*) FROM user_roles ur2
                    WHERE ur2.user_id = u.id) as role_count
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE r.name = '新员工'
              {}
        '''
        new_emp_params = []
        shift_mapping = {
            'day': ('白班',),
            'night': ('夜班',),
            'long': ('长白班',)
        }
        if shift_filter in shift_mapping:
            new_emp_query = new_emp_query.format("AND u.shift_type = ?")
            new_emp_params.append(shift_mapping[shift_filter][0])
        else:
            new_emp_query = new_emp_query.format("")
        new_employee_rows = db.execute(new_emp_query, new_emp_params).fetchall()
        
        for row in new_employee_rows:
            user_id = row['user_id']
            if user_id in user_processed:
                continue
            # 子查询已计算角色数，只有1个角色意味着只有"新员工"角色
            if row['role_count'] == 1:
                new_employee_users.append({
                    'user_id': user_id,
                    'username': row['username'],
                    'shift_type': row['shift_type'] or '白班',
                    'is_new_employee': True
                })
                user_processed.add(user_id)
        
        # 按优先级顺序组织结果（所有分组都计入应出total_count，仅正常岗位计入work_count）
        result = []
        total_count = 0

        for role in role_priority:
            if role in role_data:
                users = role_data[role]
                total_count += len(users)
                result.append({
                    'role_name': role,
                    'users': users,
                    'count': len(users)
                })
                # 从字典中移除已处理的角色
                del role_data[role]

        # 添加剩余的角色（也计入total_count）
        for role, users in role_data.items():
            total_count += len(users)
            result.append({
                'role_name': role,
                'users': users,
                'count': len(users)
            })
        
        return jsonify({
            'date': date,
            'shift_filter': shift_filter,
            'total_count': total_count,
            'work_count': work_count_val,
            'total_duration_minutes': total_duration_minutes,
            'total_duration_hours': round(total_duration_minutes / 60.0, 1),
            'leave_count': len(leave_users),
            'leave_users': leave_users,
            'absent_count': len(absent_users),
            'absent_users': absent_users,
            'in_lieu_count': len(in_lieu_users),
            'in_lieu_users': in_lieu_users,
            'resigned_count': len(resigned_users),
            'resigned_users': resigned_users,
            'new_employee_count': len(new_employee_users),
            'new_employee_users': new_employee_users,
            'roles': result
        }), 200
    except Exception as e:
        logging.error(f"获取出勤名单失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 获取所有角色API（前端岗位下拉用）
@app.route('/api/attendance/all-roles', methods=['GET'])
def get_all_roles():
    try:
        db = get_db()
        rows = db.execute("SELECT name FROM roles ORDER BY name").fetchall()
        roles = [row['name'] for row in rows]
        return jsonify({'roles': roles}), 200
    except Exception as e:
        logging.error(f"获取所有角色失败: {str(e)}")
        return jsonify({'error': str(e), 'roles': []}), 200

# 定时任务管理API
@app.route('/api/scheduler/jobs', methods=['GET'])
def get_scheduled_jobs():
    """获取定时任务列表"""
    try:
        # 移除function字段，只返回可序列化的数据
        jobs_response = []
        for job in scheduled_jobs:
            job_copy = job.copy()
            job_copy.pop('function', None)  # 移除不可序列化的function字段
            jobs_response.append(job_copy)
        
        return jsonify(jobs_response), 200
    except Exception as e:
        logging.error(f"获取定时任务列表失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/jobs/<int:job_id>', methods=['GET'])
def get_scheduled_job(job_id):
    """获取单个定时任务详情"""
    try:
        job = next((job for job in scheduled_jobs if job['id'] == job_id), None)
        if not job:
            return jsonify({'error': '任务不存在'}), 404
        
        # 移除function字段
        job_copy = job.copy()
        job_copy.pop('function', None)
        
        return jsonify(job_copy), 200
    except Exception as e:
        logging.error(f"获取定时任务详情失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/jobs', methods=['POST'])
def add_scheduled_job():
    """添加定时任务"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['job_name', 'description', 'trigger_type', 'cron_expression', 'task_type', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 确定任务函数
        task_functions = {
            'auto_add_time_records': auto_add_time_records,
            'send_system_message': send_system_message
        }
        
        if data['task_type'] not in task_functions:
            return jsonify({'error': '不支持的任务类型'}), 400
        
        # 生成新任务ID
        new_id = max(job['id'] for job in scheduled_jobs) + 1 if scheduled_jobs else 1
        
        # 创建新任务
        new_job = {
            'id': new_id,
            'job_name': data['job_name'],
            'description': data['description'],
            'trigger_type': data['trigger_type'],
            'cron_expression': data['cron_expression'],
            'task_type': data['task_type'],
            'status': data['status'],
            'function': task_functions[data['task_type']]
        }
        
        # 添加到任务列表
        scheduled_jobs.append(new_job)
        
        # 如果任务状态为enabled，添加到调度器
        if data['status'] == 'enabled':
            # 解析cron表达式
            cron_parts = new_job['cron_expression'].split()
            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts
                scheduler.add_job(
                    new_job['function'],
                    'cron',
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    id=str(new_job['id']),
                    name=new_job['job_name']
                )
        
        # 移除function字段返回
        new_job_copy = new_job.copy()
        new_job_copy.pop('function', None)
        
        return jsonify(new_job_copy), 201
    except Exception as e:
        logging.error(f"添加定时任务失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/jobs/<int:job_id>', methods=['PUT'])
def update_scheduled_job(job_id):
    """更新定时任务"""
    try:
        data = request.get_json()
        job = next((job for job in scheduled_jobs if job['id'] == job_id), None)
        
        if not job:
            return jsonify({'error': '任务不存在'}), 404
        
        # 更新任务属性
        if 'job_name' in data:
            job['job_name'] = data['job_name']
        if 'description' in data:
            job['description'] = data['description']
        if 'trigger_type' in data:
            job['trigger_type'] = data['trigger_type']
        if 'cron_expression' in data:
            job['cron_expression'] = data['cron_expression']
        if 'task_type' in data:
            # 更新任务函数
            task_functions = {
                'auto_add_time_records': auto_add_time_records,
                'send_system_message': send_system_message
            }
            if data['task_type'] in task_functions:
                job['task_type'] = data['task_type']
                job['function'] = task_functions[data['task_type']]
        if 'status' in data:
            job['status'] = data['status']
        
        # 更新调度器中的任务
        # 先移除旧任务
        scheduler.remove_job(str(job_id))
        
        # 如果状态为enabled，添加新任务
        if job['status'] == 'enabled':
            # 解析cron表达式
            cron_parts = job['cron_expression'].split()
            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts
                scheduler.add_job(
                    job['function'],
                    'cron',
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    id=str(job['id']),
                    name=job['job_name']
                )
        
        # 移除function字段返回
        job_copy = job.copy()
        job_copy.pop('function', None)
        
        return jsonify(job_copy), 200
    except Exception as e:
        logging.error(f"更新定时任务失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/jobs/<int:job_id>', methods=['DELETE'])
def delete_scheduled_job(job_id):
    """删除定时任务"""
    try:
        global scheduled_jobs
        job = next((job for job in scheduled_jobs if job['id'] == job_id), None)
        
        if not job:
            return jsonify({'error': '任务不存在'}), 404
        
        # 从调度器中移除任务
        scheduler.remove_job(str(job_id))
        
        # 从任务列表中移除
        scheduled_jobs = [job for job in scheduled_jobs if job['id'] != job_id]
        
        return jsonify({'message': '任务删除成功'}), 200
    except Exception as e:
        logging.error(f"删除定时任务失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/jobs/<int:job_id>/toggle', methods=['PATCH'])
def toggle_scheduled_job(job_id):
    """切换定时任务状态"""
    try:
        job = next((job for job in scheduled_jobs if job['id'] == job_id), None)
        if not job:
            return jsonify({'error': '任务不存在'}), 404
        
        # 切换状态
        job['status'] = 'enabled' if job['status'] == 'disabled' else 'disabled'
        
        # 更新调度器
        if job['status'] == 'enabled':
            # 添加任务到调度器
            # 解析cron表达式
            cron_parts = job['cron_expression'].split()
            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts
                scheduler.add_job(
                    job['function'],
                    'cron',
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    id=str(job['id']),
                    name=job['job_name']
                )
        else:
            # 从调度器中移除任务
            scheduler.remove_job(str(job_id))
        
        # 移除function字段返回
        job_copy = job.copy()
        job_copy.pop('function', None)
        
        return jsonify(job_copy), 200
    except Exception as e:
        logging.error(f"切换定时任务状态失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/jobs/execute', methods=['POST'])
def execute_scheduled_job():
    """手动执行定时任务"""
    try:
        data = request.get_json()
        if 'job_name' not in data:
            return jsonify({'error': '缺少任务名称'}), 400
        
        job = next((job for job in scheduled_jobs if job['job_name'] == data['job_name']), None)
        if not job:
            return jsonify({'error': '任务不存在'}), 404
        
        # 执行任务
        job['function']()
        
        return jsonify({'message': '任务执行成功'}), 200
    except Exception as e:
        logging.error(f"手动执行定时任务失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 定时任务日志和报表API
@app.route('/api/scheduler/logs', methods=['GET'])
def get_scheduler_logs():
    """获取定时任务日志列表"""
    from utils.db import get_db
    
    try:
        db = get_db()
        logs = db.execute(
            '''SELECT id, job_name, status, message, start_time, end_time, execution_time, created_at 
            FROM scheduler_logs 
            ORDER BY created_at DESC 
            LIMIT 100'''
        ).fetchall()
        
        # 将Row对象转换为字典
        logs_list = [dict(log) for log in logs]
        
        return jsonify({'logs': logs_list}), 200
    except Exception as e:
        logging.error(f"获取定时任务日志失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/stats', methods=['GET'])
def get_scheduler_stats():
    """获取定时任务执行统计报表"""
    from utils.db import get_db
    
    try:
        db = get_db()
        
        # 获取总体统计
        total_stats = db.execute(
            '''SELECT 
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                AVG(execution_time) as avg_execution_time
            FROM scheduler_logs'''
        ).fetchone()
        
        # 获取按任务类型统计
        job_stats = db.execute(
            '''SELECT 
                job_name,
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                AVG(execution_time) as avg_execution_time
            FROM scheduler_logs 
            GROUP BY job_name'''
        ).fetchall()
        
        # 获取最近7天的执行情况
        recent_stats = db.execute(
            '''SELECT 
                DATE(start_time) as date,
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
            FROM scheduler_logs 
            WHERE DATE(start_time) >= DATE('now', '-7 days') 
            GROUP BY DATE(start_time) 
            ORDER BY date'''
        ).fetchall()
        
        # 将Row对象转换为字典
        total_stats_dict = dict(total_stats) if total_stats else {}
        job_stats_list = [dict(job) for job in job_stats]
        recent_stats_list = [dict(stat) for stat in recent_stats]
        
        return jsonify({
            'total_stats': total_stats_dict,
            'job_stats': job_stats_list,
            'recent_stats': recent_stats_list
        }), 200
    except Exception as e:
        logging.error(f"获取定时任务统计报表失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])

    # 端口独占检查：防止多进程抢同一个 5000 端口
    port = Config.PORT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', port))
        if result == 0:
            # 端口已被占用，优雅退出并提示
            logging.error(f'端口 {port} 已被占用，可能已有另一个 Flask 进程在运行。请先关闭它再启动。')
            print(f'❌ 端口 {port} 已被占用 - 请先关闭旧的 Flask 进程再启动')
            s.close()
            import sys
            sys.exit(1)
        # result != 0 表示端口空闲，继续
    except Exception as e:
        logging.warning(f'端口检查异常: {e} - 仍尝试启动')
    finally:
        try: s.close()
        except: pass

    # 初始化定时任务
    init_scheduler()

    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG, use_reloader=False)