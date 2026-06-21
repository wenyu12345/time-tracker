from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db
from datetime import datetime, date, timedelta
from functools import wraps

# 生成一个简单的JWT-like token（实际项目中应使用JWT库）
def generate_token(username):
    return f"admin_{username}_token"

bp = Blueprint('admin', __name__)

# 记录操作日志的装饰器
def log_operation(module, action):
    """记录操作日志的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 记录操作日志
            try:
                # 获取管理员ID（实际项目中应从认证信息中获取）
                admin_id = 1  # 临时固定值，实际项目中应替换为真实的管理员ID
                
                # 获取请求IP
                ip_address = request.remote_addr
                
                # 获取目标ID和类型
                target_id = kwargs.get('user_id') or kwargs.get('schedule_id') or kwargs.get('permission_id') or kwargs.get('role_id') or kwargs.get('module_id')
                target_type = 'user' if 'user_id' in kwargs else 'schedule' if 'schedule_id' in kwargs else 'permission' if 'permission_id' in kwargs else 'role' if 'role_id' in kwargs else 'module' if 'module_id' in kwargs else None
                
                # 获取请求详情
                details = str(request.get_json() or {})
                
                # 记录日志
                db = get_db()
                db.execute(
                    '''INSERT INTO operation_logs (admin_id, module, action, target_id, target_type, details, ip_address) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (admin_id, module, action, target_id, target_type, details, ip_address)
                )
                db.commit()
            except Exception as e:
                # 日志记录失败不影响原函数执行
                print(f'Failed to log operation: {str(e)}')
            
            return result
        return decorated_function
    return decorator

@bp.route('/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    db = get_db()
    admin = db.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
    
    if not admin or not check_password_hash(admin['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # 生成token（实际项目中应使用JWT库）
    token = generate_token(username)
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'admin': {
            'id': admin['id'],
            'username': admin['username']
        }
    }), 200

@bp.route('/register', methods=['POST'])
def admin_register():
    """管理员注册（仅首次使用）"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    db = get_db()
    
    # 检查是否已有管理员
    existing_admins = db.execute('SELECT COUNT(*) as count FROM admins').fetchone()['count']
    if existing_admins > 0:
        return jsonify({'error': 'Admin already exists'}), 400
    
    # 检查用户名是否已存在
    if db.execute('SELECT id FROM admins WHERE username = ?', (username,)).fetchone():
        return jsonify({'error': 'Username already exists'}), 400
    
    # 创建管理员
    hashed_password = generate_password_hash(password)
    db.execute(
        'INSERT INTO admins (username, password) VALUES (?, ?)',
        (username, hashed_password)
    )
    db.commit()
    
    return jsonify({'message': 'Admin registered successfully'}), 201

@bp.route('/logout', methods=['POST'])
def admin_logout():
    """管理员登出"""
    # 实际项目中应使用JWT库，这里简化处理
    return jsonify({'message': 'Logout successful'}), 200

# 用户管理API
@bp.route('/users', methods=['GET'])
def get_users():
    """获取所有用户列表，包含用户角色信息"""
    db = get_db()
    # 查询用户及其角色信息，使用GROUP_CONCAT将多个角色ID合并为一个字符串
    users = db.execute(
        '''SELECT u.*, GROUP_CONCAT(ur.role_id) as role_ids
           FROM users u
           LEFT JOIN user_roles ur ON u.id = ur.user_id
           GROUP BY u.id'''
    ).fetchall()
    
    # 将角色ID字符串转换为数组
    users_with_roles = []
    for user in users:
        user_dict = dict(user)
        # 处理role_ids，将字符串转换为整数数组
        if user_dict['role_ids']:
            user_dict['role_ids'] = list(map(int, user_dict['role_ids'].split(',')))
        else:
            user_dict['role_ids'] = []
        users_with_roles.append(user_dict)
    
    return jsonify(users_with_roles), 200

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取单个用户详情"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(dict(user)), 200

@bp.route('/users', methods=['POST'])
def add_user():
    """新增用户"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    hire_date = data.get('hire_date')
    role_ids = data.get('role_ids', [])
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    db = get_db()
    
    # 检查用户名是否已存在
    if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return jsonify({'error': 'Username already exists'}), 400
    
    # 检查邮箱是否已存在
    if email and db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return jsonify({'error': 'Email already exists'}), 400
    
    # 创建用户
    hashed_password = generate_password_hash(password)
    cursor = db.execute(
        'INSERT INTO users (username, password, email, hire_date) VALUES (?, ?, ?, ?)',
        (username, hashed_password, email, hire_date)
    )
    user_id = cursor.lastrowid
    
    # 分配角色
    if role_ids:
        for role_id in role_ids:
            if db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
                db.execute(
                    'INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)',
                    (user_id, role_id)
                )
    
    db.commit()
    
    return jsonify({'message': 'User added successfully'}), 201

@bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    data = request.get_json()
    db = get_db()
    
    # 检查用户是否存在
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 构建更新字段
    update_fields = []
    update_params = []
    
    if 'username' in data:
        # 检查新用户名是否已存在
        new_username = data['username']
        if db.execute('SELECT id FROM users WHERE username = ? AND id != ?', (new_username, user_id)).fetchone():
            return jsonify({'error': 'Username already exists'}), 400
        update_fields.append('username = ?')
        update_params.append(new_username)
    
    if 'email' in data:
        new_email = data['email']
        if new_email:
            # 检查新邮箱是否已存在
            if db.execute('SELECT id FROM users WHERE email = ? AND id != ?', (new_email, user_id)).fetchone():
                return jsonify({'error': 'Email already exists'}), 400
        update_fields.append('email = ?')
        update_params.append(new_email)
    
    if 'hire_date' in data:
        update_fields.append('hire_date = ?')
        update_params.append(data['hire_date'])
    
    if 'salary_level' in data:
        update_fields.append('salary_level = ?')
        update_params.append(data['salary_level'])
    
    if 'role' in data:
        update_fields.append('role = ?')
        update_params.append(data['role'])
    
    if 'password' in data:
        new_password = data['password']
        if new_password:
            hashed_password = generate_password_hash(new_password)
            update_fields.append('password = ?')
            update_params.append(hashed_password)
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    # 执行更新
    update_params.append(user_id)
    db.execute(
        f'UPDATE users SET {', '.join(update_fields)} WHERE id = ?',
        update_params
    )
    db.commit()
    
    return jsonify({'message': 'User updated successfully'}), 200

@bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    db = get_db()
    
    # 检查用户是否存在
    if not db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone():
        return jsonify({'error': 'User not found'}), 404
    
    # 删除用户
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

# 用户角色管理API
@bp.route('/users/<int:user_id>/roles', methods=['GET'])
def get_user_roles(user_id):
    """获取用户的角色"""
    db = get_db()
    
    # 检查用户是否存在
    if not db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone():
        return jsonify({'error': 'User not found'}), 404
    
    # 获取用户的角色
    roles = db.execute(
        '''SELECT r.* 
        FROM roles r 
        JOIN user_roles ur ON r.id = ur.role_id 
        WHERE ur.user_id = ?''',
        (user_id,)
    ).fetchall()
    
    return jsonify([dict(role) for role in roles]), 200

@bp.route('/roles/<int:role_id>/users', methods=['GET'])
def get_users_by_role(role_id):
    """获取指定角色下的所有用户"""
    db = get_db()
    
    # 检查角色是否存在
    if not db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
        return jsonify({'error': 'Role not found'}), 404
    
    # 获取该角色下的所有用户
    users = db.execute(
        '''SELECT u.* 
        FROM users u 
        JOIN user_roles ur ON u.id = ur.user_id 
        WHERE ur.role_id = ?''',
        (role_id,)
    ).fetchall()
    
    return jsonify([dict(user) for user in users]), 200

@bp.route('/users/<int:user_id>/roles', methods=['POST'])
def assign_roles_to_user(user_id):
    """分配角色给用户"""
    data = request.get_json()
    role_ids = data.get('role_ids', [])
    
    db = get_db()
    
    # 检查用户是否存在
    if not db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone():
        return jsonify({'error': 'User not found'}), 404
    
    # 删除用户现有的所有角色
    db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
    
    # 分配新的角色
    for role_id in role_ids:
        # 验证角色是否存在
        if db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
            db.execute(
                'INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)',
                (user_id, role_id)
            )
    
    db.commit()
    
    return jsonify({'message': 'Roles assigned to user successfully'}), 200

# 排班管理API
@bp.route('/schedules', methods=['GET'])
def get_schedules():
    """获取所有排班"""
    db = get_db()
    schedules = db.execute('SELECT * FROM schedules').fetchall()
    
    return jsonify([dict(schedule) for schedule in schedules]), 200

@bp.route('/schedules/user/<int:user_id>', methods=['GET'])
def get_schedules_by_user(user_id):
    """获取指定用户排班"""
    db = get_db()
    schedules = db.execute('SELECT * FROM schedules WHERE user_id = ?', (user_id,)).fetchall()
    
    return jsonify([dict(schedule) for schedule in schedules]), 200

@bp.route('/schedules/date/<date>', methods=['GET'])
def get_schedules_by_date(date):
    """根据日期获取排班"""
    db = get_db()
    schedules = db.execute(
        'SELECT * FROM schedules WHERE start_date <= ? AND end_date >= ?',
        (date, date)
    ).fetchall()
    return jsonify([dict(schedule) for schedule in schedules]), 200

@bp.route('/schedules/user/<int:user_id>/date/<date>', methods=['GET'])
def get_schedules_by_user_and_date(user_id, date):
    """根据用户ID和日期获取排班"""
    db = get_db()
    schedules = db.execute(
        'SELECT * FROM schedules WHERE user_id = ? AND start_date <= ? AND end_date >= ?',
        (user_id, date, date)
    ).fetchall()
    return jsonify([dict(schedule) for schedule in schedules]), 200

@bp.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """获取单个排班详情"""
    db = get_db()
    schedule = db.execute('SELECT * FROM schedules WHERE id = ?', (schedule_id,)).fetchone()
    
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    return jsonify(dict(schedule)), 200

@bp.route('/schedules', methods=['POST'])
@log_operation('schedules', 'add')
def add_schedule():
    """新增排班"""
    data = request.get_json()
    user_id = data.get('user_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    shift_type = data.get('shift_type')
    hours = data.get('hours')
    description = data.get('description')
    
    if not user_id or not start_date or not end_date or not shift_type or hours is None:
        return jsonify({'error': 'User ID, start date, end date, shift type and hours are required'}), 400
    
    db = get_db()
    
    # 检查用户是否存在
    if not db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone():
        return jsonify({'error': 'User not found'}), 404
    
    # 检查是否存在重复排班：同一个用户在同一日期范围内的排班
    existing_schedule = db.execute(
        '''SELECT id FROM schedules 
        WHERE user_id = ? 
        AND ((start_date <= ? AND end_date >= ?) 
        OR (start_date <= ? AND end_date >= ?) 
        OR (start_date >= ? AND end_date <= ?))''',
        (user_id, start_date, start_date, end_date, end_date, start_date, end_date)
    ).fetchone()
    
    if existing_schedule:
        return jsonify({'error': '该用户在所选日期范围内已存在排班'}), 400
    
    # 新增排班
    db.execute(
        '''INSERT INTO schedules (user_id, start_date, end_date, shift_type, hours, description) 
        VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, start_date, end_date, shift_type, hours, description)
    )
    db.commit()
    
    return jsonify({'message': 'Schedule added successfully'}), 201

@bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@log_operation('schedules', 'update')
def update_schedule(schedule_id):
    """更新排班"""
    data = request.get_json()
    db = get_db()
    
    # 检查排班是否存在
    schedule = db.execute('SELECT * FROM schedules WHERE id = ?', (schedule_id,)).fetchone()
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    # 构建更新字段
    update_fields = []
    update_params = []
    
    if 'user_id' in data:
        user_id = data['user_id']
        # 检查用户是否存在
        if not db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone():
            return jsonify({'error': 'User not found'}), 404
        update_fields.append('user_id = ?')
        update_params.append(user_id)
    
    if 'start_date' in data:
        update_fields.append('start_date = ?')
        update_params.append(data['start_date'])
    
    if 'end_date' in data:
        update_fields.append('end_date = ?')
        update_params.append(data['end_date'])
    
    if 'shift_type' in data:
        update_fields.append('shift_type = ?')
        update_params.append(data['shift_type'])
    
    if 'hours' in data:
        update_fields.append('hours = ?')
        update_params.append(data['hours'])
    
    if 'description' in data:
        update_fields.append('description = ?')
        update_params.append(data['description'])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    # 执行更新
    update_params.append(schedule_id)
    db.execute(
        f'UPDATE schedules SET {', '.join(update_fields)} WHERE id = ?',
        update_params
    )
    db.commit()
    
    return jsonify({'message': 'Schedule updated successfully'}), 200

@bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@log_operation('schedules', 'delete')
def delete_schedule(schedule_id):
    """删除排班"""
    db = get_db()
    
    # 检查排班是否存在
    if not db.execute('SELECT id FROM schedules WHERE id = ?', (schedule_id,)).fetchone():
        return jsonify({'error': 'Schedule not found'}), 404
    
    # 删除排班
    db.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
    db.commit()
    
    return jsonify({'message': 'Schedule deleted successfully'}), 200

@bp.route('/schedules/batch', methods=['POST'])
@log_operation('schedules', 'batch_add')
def batch_add_schedules():
    """批量排班"""
    data = request.get_json()
    schedules = data.get('schedules')
    
    if not schedules or not isinstance(schedules, list):
        return jsonify({'error': 'Schedules list is required'}), 400
    
    db = get_db()
    
    try:
        for schedule_data in schedules:
            user_id = schedule_data.get('user_id')
            start_date = schedule_data.get('start_date')
            end_date = schedule_data.get('end_date')
            shift_type = schedule_data.get('shift_type')
            hours = schedule_data.get('hours')
            description = schedule_data.get('description')
            
            if not user_id or not start_date or not end_date or not shift_type or hours is None:
                continue  # 跳过无效数据
            
            # 检查用户是否存在
            if not db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone():
                continue  # 跳过无效用户
            
            # 新增排班
            db.execute(
                '''INSERT INTO schedules (user_id, start_date, end_date, shift_type, hours, description) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, start_date, end_date, shift_type, hours, description)
            )
        
        db.commit()
        return jsonify({'message': 'Batch schedules added successfully'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/schedules/expired', methods=['DELETE'])
@log_operation('schedules', 'delete_expired')
def delete_expired_schedules():
    """删除过期排班"""
    from datetime import datetime
    
    db = get_db()
    
    try:
        # 获取当前日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 删除过期排班
        result = db.execute('DELETE FROM schedules WHERE end_date < ?', (today,))
        db.commit()
        
        return jsonify({'message': f'Successfully deleted {result.rowcount} expired schedules'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# 工资算法配置API
@bp.route('/salary-config', methods=['GET'])
def get_salary_config():
    """获取工资算法配置"""
    db = get_db()
    configs = db.execute('SELECT * FROM salary_config').fetchall()
    
    return jsonify([dict(config) for config in configs]), 200

@bp.route('/salary-config', methods=['PUT'])
def update_salary_config():
    """更新工资算法配置"""
    data = request.get_json()
    config_key = data.get('config_key')
    config_value = data.get('config_value')
    description = data.get('description')
    
    if not config_key or config_value is None:
        return jsonify({'error': 'Config key and value are required'}), 400
    
    db = get_db()
    
    # 检查配置是否存在
    existing = db.execute('SELECT id FROM salary_config WHERE config_key = ?', (config_key,)).fetchone()
    
    if existing:
        # 更新现有配置
        db.execute(
            '''UPDATE salary_config SET config_value = ?, description = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE config_key = ?''',
            (config_value, description, config_key)
        )
    else:
        # 创建新配置
        db.execute(
            '''INSERT INTO salary_config (config_key, config_value, description) 
            VALUES (?, ?, ?)''',
            (config_key, config_value, description)
        )
    
    db.commit()
    
    return jsonify({'message': 'Salary config updated successfully'}), 200

@bp.route('/salary-config/reset', methods=['POST'])
def reset_salary_config():
    """重置工资算法配置为默认值"""
    db = get_db()
    
    # 删除所有现有配置
    db.execute('DELETE FROM salary_config')
    
    # 插入默认配置
    default_configs = [
        ('overtime_rate', 19.65, '加班费标准（元/小时）'),
        ('standard_hours', 167, '标准工时（小时/月）'),
        ('attendance_bonus_amount', 400, '满勤奖金额（元）'),
        ('max_leave_hours', 8, '满勤奖允许的最大请假小时数'),
        ('night_shift_allowance', 10, '夜班补贴（元/天）'),
        ('tax_threshold', 5000, '个人所得税起征点（元）')
    ]
    
    for config in default_configs:
        db.execute(
            '''INSERT INTO salary_config (config_key, config_value, description) 
            VALUES (?, ?, ?)''',
            config
        )
    
    db.commit()
    
    return jsonify({'message': 'Salary config reset to default values'}), 200

# 统计汇总API
@bp.route('/stats/today', methods=['GET'])
def get_today_stats():
    """获取当天统计信息"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    db = get_db()
    
    # 获取当天上班人数（不包括请假）
    working_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) = ? AND is_leave = 0''',
        (today,)
    ).fetchone()['count']
    
    # 获取当天请假人数
    leave_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) = ? AND is_leave = 1''',
        (today,)
    ).fetchone()['count']
    
    # 获取当天总工时（不包括请假）
    total_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_hours 
        FROM time_records 
        WHERE DATE(start_time) = ? AND is_leave = 0''',
        (today,)
    ).fetchone()['total_hours'] or 0
    
    # 获取当天总请假时长
    total_leave_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_leave_hours 
        FROM time_records 
        WHERE DATE(start_time) = ? AND is_leave = 1''',
        (today,)
    ).fetchone()['total_leave_hours'] or 0
    
    # 获取当天白班人数（不包括请假）
    day_shift_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) = ? AND shift_type = '白班' AND is_leave = 0''',
        (today,)
    ).fetchone()['count']
    
    # 获取当天夜班人数（不包括请假）
    night_shift_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) = ? AND shift_type = '夜班' AND is_leave = 0''',
        (today,)
    ).fetchone()['count']
    
    # 获取当天所有人员列表（包括出勤和请假）
    all_users = db.execute(
        '''SELECT DISTINCT u.id, u.username, u.email, tr.shift_type, tr.is_leave, SUM(tr.duration)/60 as today_hours 
        FROM time_records tr 
        JOIN users u ON tr.user_id = u.id 
        WHERE DATE(tr.start_time) = ? 
        GROUP BY u.id, u.username, u.email, tr.shift_type, tr.is_leave''',
        (today,)
    ).fetchall()
    
    attendance_list = []
    leave_list = []
    
    for user in all_users:
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'shift_type': user['shift_type'],
            'today_hours': round(user['today_hours'], 2)
        }
        
        if user['is_leave']:
            leave_list.append(user_info)
        else:
            attendance_list.append(user_info)
    
    return jsonify({
        'date': today,
        'working_users': working_users,
        'leave_users': leave_users,
        'total_hours': round(total_hours, 2),
        'total_leave_hours': round(total_leave_hours, 2),
        'day_shift_users': day_shift_users,
        'night_shift_users': night_shift_users,
        'attendance_users': attendance_list,
        'leave_users_list': leave_list
    }), 200

@bp.route('/stats/week', methods=['GET'])
def get_week_stats():
    """获取本周统计信息"""
    from datetime import datetime, timedelta
    
    # 计算本周一和周日
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    start_date = start_of_week.strftime('%Y-%m-%d')
    end_date = end_of_week.strftime('%Y-%m-%d')
    
    db = get_db()
    
    # 获取本周上班人数（不包括请假）
    working_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本周请假人数
    leave_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本周总工时（不包括请假）
    total_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_hours 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['total_hours'] or 0
    
    # 获取本周总请假时长
    total_leave_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_leave_hours 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['total_leave_hours'] or 0
    
    # 获取本周白班天数
    day_shifts = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND shift_type = '白班' AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本周夜班天数
    night_shifts = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND shift_type = '夜班' AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本周请假天数
    leave_days = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['count']
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'working_users': working_users,
        'leave_users': leave_users,
        'total_hours': round(total_hours, 2),
        'total_leave_hours': round(total_leave_hours, 2),
        'day_shifts': day_shifts,
        'night_shifts': night_shifts,
        'leave_days': leave_days
    }), 200

@bp.route('/stats/month', methods=['GET'])
def get_month_stats():
    """获取本月统计信息"""
    from datetime import datetime
    
    # 计算本月第一天和最后一天
    today = datetime.now()
    start_of_month = today.replace(day=1)
    if today.month == 12:
        end_of_month = start_of_month.replace(year=today.year + 1, month=1) - timedelta(days=1)
    else:
        end_of_month = start_of_month.replace(month=today.month + 1) - timedelta(days=1)
    
    start_date = start_of_month.strftime('%Y-%m-%d')
    end_date = end_of_month.strftime('%Y-%m-%d')
    
    db = get_db()
    
    # 获取本月上班人数（不包括请假）
    working_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本月请假人数
    leave_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本月总工时（不包括请假）
    total_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_hours 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['total_hours'] or 0
    
    # 获取本月总请假时长
    total_leave_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_leave_hours 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['total_leave_hours'] or 0
    
    # 获取本月白班天数
    day_shifts = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND shift_type = '白班' AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本月夜班天数
    night_shifts = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND shift_type = '夜班' AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取本月请假天数
    leave_days = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['count']
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'working_users': working_users,
        'leave_users': leave_users,
        'total_hours': round(total_hours, 2),
        'total_leave_hours': round(total_leave_hours, 2),
        'day_shifts': day_shifts,
        'night_shifts': night_shifts,
        'leave_days': leave_days
    }), 200

@bp.route('/stats/custom', methods=['GET'])
def get_custom_stats():
    """获取自定义时间范围统计信息"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    db = get_db()
    
    # 获取自定义时间范围上班人数（不包括请假）
    working_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取自定义时间范围请假人数
    leave_users = db.execute(
        '''SELECT COUNT(DISTINCT user_id) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取自定义时间范围总工时（不包括请假）
    total_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_hours 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['total_hours'] or 0
    
    # 获取自定义时间范围总请假时长
    total_leave_hours = db.execute(
        '''SELECT SUM(duration) / 60 as total_leave_hours 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['total_leave_hours'] or 0
    
    # 获取自定义时间范围白班天数
    day_shifts = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND shift_type = '白班' AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取自定义时间范围夜班天数
    night_shifts = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND shift_type = '夜班' AND is_leave = 0''',
        (start_date, end_date)
    ).fetchone()['count']
    
    # 获取自定义时间范围请假天数
    leave_days = db.execute(
        '''SELECT COUNT(*) as count 
        FROM time_records 
        WHERE DATE(start_time) BETWEEN ? AND ? AND is_leave = 1''',
        (start_date, end_date)
    ).fetchone()['count']
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'working_users': working_users,
        'leave_users': leave_users,
        'total_hours': round(total_hours, 2),
        'total_leave_hours': round(total_leave_hours, 2),
        'day_shifts': day_shifts,
        'night_shifts': night_shifts,
        'leave_days': leave_days
    }), 200

@bp.route('/time-records/date/<date>', methods=['GET'])
def get_time_records_by_date(date):
    """获取指定日期的所有用户工时记录"""
    db = get_db()
    
    try:
        # 获取指定日期的所有用户工时记录
        records = db.execute(
            '''SELECT tr.*, u.username 
            FROM time_records tr 
            JOIN users u ON tr.user_id = u.id 
            WHERE DATE(tr.start_time) = ?''',
            (date,)
        ).fetchall()
        
        return jsonify([dict(record) for record in records]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/range/<start_date>/<end_date>', methods=['GET'])
def get_time_records_by_range(start_date, end_date):
    """获取指定日期范围的所有用户工时记录，支持按角色筛选"""
    db = get_db()
    
    try:
        # 获取角色ID查询参数
        role_id = request.args.get('role_id')
        
        # 构建SQL查询
        base_query = '''
            SELECT tr.*, u.username 
            FROM time_records tr 
            JOIN users u ON tr.user_id = u.id 
        '''
        
        where_clauses = ['DATE(tr.start_time) BETWEEN ? AND ?']
        params = [start_date, end_date]
        
        # 如果提供了角色ID，加入角色筛选条件
        if role_id:
            base_query += ' JOIN user_roles ur ON u.id = ur.user_id '
            where_clauses.append('ur.role_id = ?')
            params.append(int(role_id))
        
        # 组合完整SQL查询
        full_query = base_query + ' WHERE ' + ' AND '.join(where_clauses)
        
        # 执行查询
        records = db.execute(full_query, params).fetchall()
        
        return jsonify([dict(record) for record in records]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/user/<int:user_id>/range', methods=['GET'])
def get_time_records_by_user_and_range(user_id, start_date=None, end_date=None):
    """获取指定用户在日期范围内的工时记录"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    db = get_db()
    
    try:
        # 获取指定用户在日期范围内的工时记录
        records = db.execute(
            '''SELECT * 
            FROM time_records 
            WHERE user_id = ? AND DATE(start_time) BETWEEN ? AND ?''',
            (user_id, start_date, end_date)
        ).fetchall()
        
        return jsonify([dict(record) for record in records]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/batch', methods=['PUT'])
def batch_update_time_records():
    """批量更新工时记录，支持按角色批量修改"""
    data = request.get_json()
    
    # 获取批量更新参数
    role_id = data.get('role_id')
    shift_type = data.get('shift_type')
    hours = data.get('hours')
    is_leave = data.get('is_leave')
    leave_hours = data.get('leave_hours')
    status = data.get('status')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    db = get_db()
    
    try:
        # 构建更新字段和参数
        update_fields = []
        update_params = []
        
        if shift_type is not None:
            update_fields.append('shift_type = ?')
            update_params.append(shift_type)
        
        if hours is not None:
            # 将小时转换为分钟
            duration = int(hours * 60)
            update_fields.append('duration = ?')
            update_params.append(duration)
        
        if is_leave is not None:
            update_fields.append('is_leave = ?')
            update_params.append(is_leave)
        
        if leave_hours is not None:
            update_fields.append('leave_hours = ?')
            update_params.append(leave_hours)
        
        if status is not None:
            update_fields.append('description = ?')
            update_params.append(status)
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        # 构建查询条件
        query = 'UPDATE time_records SET '
        query += ', '.join(update_fields)
        query += ' WHERE DATE(start_time) BETWEEN ? AND ?'
        update_params.extend([start_date, end_date])
        
        # 如果指定了角色ID，添加角色过滤条件
        if role_id is not None:
            query += ' AND user_id IN (SELECT user_id FROM user_roles WHERE role_id = ?)'
            update_params.append(role_id)
        
        # 执行批量更新
        result = db.execute(query, update_params)
        db.commit()
        
        return jsonify({'message': f'Successfully updated {result.rowcount} records'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/copy', methods=['POST'])
def copy_time_records():
    """批量复制工时记录"""
    data = request.get_json()
    source_user_id = data.get('source_user_id')
    target_user_ids = data.get('target_user_ids')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not source_user_id or not target_user_ids or not isinstance(target_user_ids, list) or not start_date or not end_date:
        return jsonify({'error': 'Source user ID, target user IDs, start date and end date are required'}), 400
    
    db = get_db()
    
    try:
        # 获取源用户在日期范围内的工时记录
        source_records = db.execute(
            '''SELECT * 
            FROM time_records 
            WHERE user_id = ? AND DATE(start_time) BETWEEN ? AND ?''',
            (source_user_id, start_date, end_date)
        ).fetchall()
        
        # 复制记录到目标用户
        for target_user_id in target_user_ids:
            for record in source_records:
                # 提取时间部分
                start_time = datetime.strptime(record['start_time'], '%Y-%m-%dT%H:%M:%S')
                end_time = datetime.strptime(record['end_time'], '%Y-%m-%dT%H:%M:%S')
                time_part = start_time.strftime('%H:%M:%S')
                
                # 插入新记录
                db.execute(
                    '''INSERT INTO time_records (user_id, project_id, start_time, end_time, duration, shift_type, is_leave, description) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (target_user_id, record['project_id'], record['start_time'], record['end_time'], 
                     record['duration'], record['shift_type'], record['is_leave'], record['description'])
                )
        
        db.commit()
        
        return jsonify({'message': f'Successfully copied {len(source_records)} records to {len(target_user_ids)} users'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/schedules/to-time-records', methods=['POST'])
def schedules_to_time_records():
    """将所有没有工时记录的排班写入工时记录"""
    db = get_db()
    
    try:
        # 查询所有排班记录
        schedules = db.execute('SELECT * FROM schedules').fetchall()
        
        created_records = 0
        
        for schedule in schedules:
            schedule_id = schedule['id']
            user_id = schedule['user_id']
            start_date = schedule['start_date']
            end_date = schedule['end_date']
            shift_type = schedule['shift_type']
            hours = schedule['hours']
            description = schedule['description']
            
            # 将date对象转换为datetime对象
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.min.time())
            
            # 遍历日期范围内的每一天
            current_dt = start_dt
            while current_dt <= end_dt:
                record_date = current_dt.strftime('%Y-%m-%d')
                
                # 检查该用户在该日期是否已经有工时记录
                existing_record = db.execute(
                    '''SELECT id FROM time_records 
                    WHERE user_id = ? AND DATE(start_time) = ?''',
                    (user_id, record_date)
                ).fetchone()
                
                if not existing_record:
                    # 根据班别类型设置默认的开始和结束时间
                    if shift_type == '白班':
                        start_time = f'{record_date}T08:00:00'
                        end_time = f'{record_date}T18:00:00'
                    elif shift_type == '夜班':
                        start_time = f'{record_date}T20:00:00'
                        # 夜班结束时间是第二天早上6点
                        next_day = (current_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                        end_time = f'{next_day}T06:00:00'
                    else:
                        # 默认白班时间
                        start_time = f'{record_date}T08:00:00'
                        end_time = f'{record_date}T18:00:00'
                    
                    # 计算时长（分钟）
                    duration = int(hours * 60)
                    
                    # 插入工时记录
                    db.execute(
                        '''INSERT INTO time_records (user_id, start_time, end_time, duration, shift_type, is_leave, description) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (user_id, start_time, end_time, duration, shift_type, False, description)
                    )
                    
                    created_records += 1
                
                # 移动到下一天
                current_dt += timedelta(days=1)
        
        db.commit()
        
        return jsonify({'message': f'Successfully created {created_records} time records from schedules'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/arrange-leave', methods=['POST'])
@log_operation('schedules', 'arrange_leave')
def arrange_leave():
    """批量安排调休"""
    data = request.get_json()
    user_ids = data.get('user_ids')
    dates = data.get('dates')
    
    if not user_ids or not isinstance(user_ids, list) or not dates or not isinstance(dates, list):
        return jsonify({'error': 'User IDs and dates list are required'}), 400
    
    db = get_db()
    
    try:
        # 遍历每个用户和日期，安排调休
        total_processed = 0
        
        for user_id in user_ids:
            for leave_date in dates:
                # 1. 确保leave_date是YYYY-MM-DD格式的字符串
                leave_date_str = leave_date if isinstance(leave_date, str) else leave_date.strftime('%Y-%m-%d')
                
                # 2. 转换为日期对象用于比较
                leave_date_dt = datetime.strptime(leave_date_str, '%Y-%m-%d').date()
                
                # 3. 删除当天的工时记录
                # 使用参数化查询，确保日期格式正确处理
                db.execute(
                    '''DELETE FROM time_records 
                    WHERE user_id = ? AND DATE(start_time) = ?''',
                    (user_id, leave_date_str)
                )
                
                # 4. 查询包含该日期的排班 - 使用字符串格式的日期进行数据库查询
                schedules = db.execute(
                    '''SELECT * FROM schedules 
                    WHERE user_id = ? AND start_date <= ? AND end_date >= ?''',
                    (user_id, leave_date_str, leave_date_str)
                ).fetchall()
                
                for schedule in schedules:
                    schedule_id = schedule['id']
                    start_date = schedule['start_date']
                    end_date = schedule['end_date']
                    shift_type = schedule['shift_type']
                    hours = schedule['hours']
                    description = schedule['description']
                    
                    # 确保start_date和end_date是日期对象
                    start_date_dt = start_date if isinstance(start_date, date) else datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date_dt = end_date if isinstance(end_date, date) else datetime.strptime(end_date, '%Y-%m-%d').date()
                    
                    # 3. 拆分排班
                    if start_date_dt < leave_date_dt < end_date_dt:
                        # 情况1: 调休日期在排班中间，拆分为两个排班
                        # 创建第一个排班：从原开始日期到调休日期前一天
                        new_end_date1 = leave_date_dt - timedelta(days=1)
                        db.execute(
                            '''INSERT INTO schedules (user_id, start_date, end_date, shift_type, hours, description) 
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (user_id, start_date_dt, new_end_date1, shift_type, hours, description)
                        )
                        
                        # 创建第二个排班：从调休日期后一天到原结束日期
                        new_start_date2 = leave_date_dt + timedelta(days=1)
                        db.execute(
                            '''INSERT INTO schedules (user_id, start_date, end_date, shift_type, hours, description) 
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (user_id, new_start_date2, end_date_dt, shift_type, hours, description)
                        )
                        
                        # 删除原排班
                        db.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
                    elif leave_date_dt == start_date_dt and start_date_dt < end_date_dt:
                        # 情况2: 调休日期是排班开始日期，更新开始日期为调休日期+1
                        new_start_date = leave_date_dt + timedelta(days=1)
                        db.execute(
                            '''UPDATE schedules SET start_date = ? WHERE id = ?''',
                            (new_start_date, schedule_id)
                        )
                    elif leave_date_dt == end_date_dt and start_date_dt < end_date_dt:
                        # 情况3: 调休日期是排班结束日期，更新结束日期为调休日期-1
                        new_end_date = leave_date_dt - timedelta(days=1)
                        db.execute(
                            '''UPDATE schedules SET end_date = ? WHERE id = ?''',
                            (new_end_date, schedule_id)
                        )
                    elif leave_date_dt == start_date_dt and leave_date_dt == end_date_dt:
                        # 情况4: 调休日期是排班的唯一日期，直接删除该排班
                        db.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
                
                total_processed += 1
        
        db.commit()
        
        return jsonify({'message': f'Successfully arranged leave for {total_processed} user-date pairs'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# 权限管理API
@bp.route('/permissions', methods=['GET'])
def get_permissions():
    """获取所有权限"""
    db = get_db()
    permissions = db.execute('SELECT * FROM permissions').fetchall()
    
    return jsonify([dict(permission) for permission in permissions]), 200

@bp.route('/permissions', methods=['POST'])
def add_permission():
    """添加权限"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        return jsonify({'error': 'Permission name is required'}), 400
    
    db = get_db()
    
    # 检查权限是否已存在
    if db.execute('SELECT id FROM permissions WHERE name = ?', (name,)).fetchone():
        return jsonify({'error': 'Permission already exists'}), 400
    
    # 添加权限
    db.execute(
        'INSERT INTO permissions (name, description) VALUES (?, ?)',
        (name, description)
    )
    db.commit()
    
    return jsonify({'message': 'Permission added successfully'}), 201

@bp.route('/permissions/<int:permission_id>', methods=['PUT'])
def update_permission(permission_id):
    """更新权限"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    
    db = get_db()
    
    # 检查权限是否存在
    if not db.execute('SELECT id FROM permissions WHERE id = ?', (permission_id,)).fetchone():
        return jsonify({'error': 'Permission not found'}), 404
    
    # 检查新名称是否已存在
    if name:
        existing = db.execute('SELECT id FROM permissions WHERE name = ? AND id != ?', (name, permission_id)).fetchone()
        if existing:
            return jsonify({'error': 'Permission name already exists'}), 400
    
    # 构建更新字段
    update_fields = []
    update_params = []
    
    if name:
        update_fields.append('name = ?')
        update_params.append(name)
    
    if description is not None:
        update_fields.append('description = ?')
        update_params.append(description)
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    # 执行更新
    update_params.append(permission_id)
    db.execute(
        f'UPDATE permissions SET {', '.join(update_fields)} WHERE id = ?',
        update_params
    )
    db.commit()
    
    return jsonify({'message': 'Permission updated successfully'}), 200

@bp.route('/permissions/<int:permission_id>', methods=['DELETE'])
def delete_permission(permission_id):
    """删除权限"""
    db = get_db()
    
    # 检查权限是否存在
    if not db.execute('SELECT id FROM permissions WHERE id = ?', (permission_id,)).fetchone():
        return jsonify({'error': 'Permission not found'}), 404
    
    # 删除权限
    db.execute('DELETE FROM permissions WHERE id = ?', (permission_id,))
    db.commit()
    
    return jsonify({'message': 'Permission deleted successfully'}), 200

# 角色管理API
@bp.route('/roles', methods=['GET'])
def get_roles():
    """获取所有角色"""
    db = get_db()
    roles = db.execute('SELECT * FROM roles').fetchall()
    
    return jsonify([dict(role) for role in roles]), 200

@bp.route('/roles', methods=['POST'])
def add_role():
    """添加角色"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        return jsonify({'error': 'Role name is required'}), 400
    
    db = get_db()
    
    # 检查角色是否已存在
    if db.execute('SELECT id FROM roles WHERE name = ?', (name,)).fetchone():
        return jsonify({'error': 'Role already exists'}), 400
    
    # 添加角色
    db.execute(
        'INSERT INTO roles (name, description) VALUES (?, ?)',
        (name, description)
    )
    db.commit()
    
    return jsonify({'message': 'Role added successfully'}), 201

@bp.route('/roles/<int:role_id>', methods=['GET'])
def get_role(role_id):
    """获取指定角色的详情"""
    db = get_db()
    
    # 检查角色是否存在
    role = db.execute('SELECT * FROM roles WHERE id = ?', (role_id,)).fetchone()
    if not role:
        return jsonify({'error': 'Role not found'}), 404
    
    return jsonify(dict(role)), 200

@bp.route('/roles/<int:role_id>', methods=['PUT'])
def update_role(role_id):
    """更新角色"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    
    db = get_db()
    
    # 检查角色是否存在
    if not db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
        return jsonify({'error': 'Role not found'}), 404
    
    # 检查新名称是否已存在
    if name:
        existing = db.execute('SELECT id FROM roles WHERE name = ? AND id != ?', (name, role_id)).fetchone()
        if existing:
            return jsonify({'error': 'Role name already exists'}), 400
    
    # 构建更新字段
    update_fields = []
    update_params = []
    
    if name:
        update_fields.append('name = ?')
        update_params.append(name)
    
    if description is not None:
        update_fields.append('description = ?')
        update_params.append(description)
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    # 执行更新
    update_params.append(role_id)
    db.execute(
        f'UPDATE roles SET {', '.join(update_fields)} WHERE id = ?',
        update_params
    )
    db.commit()
    
    return jsonify({'message': 'Role updated successfully'}), 200

@bp.route('/roles/<int:role_id>', methods=['DELETE'])
def delete_role(role_id):
    """删除角色"""
    db = get_db()
    
    # 检查角色是否存在
    if not db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
        return jsonify({'error': 'Role not found'}), 404
    
    # 删除角色
    db.execute('DELETE FROM roles WHERE id = ?', (role_id,))
    db.commit()
    
    return jsonify({'message': 'Role deleted successfully'}), 200

# 角色权限管理API
@bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
def get_role_permissions(role_id):
    """获取角色的权限"""
    db = get_db()
    
    # 检查角色是否存在
    if not db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
        return jsonify({'error': 'Role not found'}), 404
    
    # 获取角色的权限
    permissions = db.execute(
        '''SELECT p.* 
        FROM permissions p 
        JOIN role_permissions rp ON p.id = rp.permission_id 
        WHERE rp.role_id = ?''',
        (role_id,)
    ).fetchall()
    
    return jsonify([dict(permission) for permission in permissions]), 200

@bp.route('/roles/<int:role_id>/permissions', methods=['POST'])
def assign_permissions_to_role(role_id):
    """分配权限给角色"""
    data = request.get_json()
    permission_ids = data.get('permission_ids')
    
    if not permission_ids or not isinstance(permission_ids, list):
        return jsonify({'error': 'Permission IDs list is required'}), 400
    
    db = get_db()
    
    # 检查角色是否存在
    if not db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
        return jsonify({'error': 'Role not found'}), 404
    
    # 检查权限是否存在
    for permission_id in permission_ids:
        if not db.execute('SELECT id FROM permissions WHERE id = ?', (permission_id,)).fetchone():
            return jsonify({'error': f'Permission {permission_id} not found'}), 404
    
    # 删除角色现有的所有权限
    db.execute('DELETE FROM role_permissions WHERE role_id = ?', (role_id,))
    
    # 分配新的权限
    for permission_id in permission_ids:
        db.execute(
            'INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)',
            (role_id, permission_id)
        )
    
    db.commit()
    
    return jsonify({'message': 'Permissions assigned to role successfully'}), 200

# 管理员角色管理API
@bp.route('/admins/<int:admin_id>/roles', methods=['GET'])
def get_admin_roles(admin_id):
    """获取管理员的角色"""
    db = get_db()
    
    # 检查管理员是否存在
    if not db.execute('SELECT id FROM admins WHERE id = ?', (admin_id,)).fetchone():
        return jsonify({'error': 'Admin not found'}), 404
    
    # 获取管理员的角色
    roles = db.execute(
        '''SELECT r.* 
        FROM roles r 
        JOIN admin_roles ar ON r.id = ar.role_id 
        WHERE ar.admin_id = ?''',
        (admin_id,)
    ).fetchall()
    
    return jsonify([dict(role) for role in roles]), 200

@bp.route('/admins/<int:admin_id>/roles', methods=['POST'])
def assign_roles_to_admin(admin_id):
    """分配角色给管理员"""
    data = request.get_json()
    role_ids = data.get('role_ids')
    
    if not role_ids or not isinstance(role_ids, list):
        return jsonify({'error': 'Role IDs list is required'}), 400
    
    db = get_db()
    
    # 检查管理员是否存在
    if not db.execute('SELECT id FROM admins WHERE id = ?', (admin_id,)).fetchone():
        return jsonify({'error': 'Admin not found'}), 404
    
    # 检查角色是否存在
    for role_id in role_ids:
        if not db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone():
            return jsonify({'error': f'Role {role_id} not found'}), 404
    
    # 删除管理员现有的所有角色
    db.execute('DELETE FROM admin_roles WHERE admin_id = ?', (admin_id,))
    
    # 分配新的角色
    for role_id in role_ids:
        db.execute(
            'INSERT INTO admin_roles (admin_id, role_id) VALUES (?, ?)',
            (admin_id, role_id)
        )
    
    db.commit()
    
    return jsonify({'message': 'Roles assigned to admin successfully'}), 200

# 模块管理API
@bp.route('/modules', methods=['GET'])
def get_modules():
    """获取所有模块"""
    db = get_db()
    modules = db.execute('SELECT * FROM modules').fetchall()
    
    return jsonify([dict(module) for module in modules]), 200

@bp.route('/modules', methods=['POST'])
def add_module():
    """添加模块"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    path = data.get('path')
    parent_id = data.get('parent_id')
    
    if not name:
        return jsonify({'error': 'Module name is required'}), 400
    
    db = get_db()
    
    # 检查模块是否已存在
    if db.execute('SELECT id FROM modules WHERE name = ?', (name,)).fetchone():
        return jsonify({'error': 'Module already exists'}), 400
    
    # 检查父模块是否存在
    if parent_id:
        if not db.execute('SELECT id FROM modules WHERE id = ?', (parent_id,)).fetchone():
            return jsonify({'error': 'Parent module not found'}), 404
    
    # 添加模块
    db.execute(
        'INSERT INTO modules (name, description, path, parent_id) VALUES (?, ?, ?, ?)',
        (name, description, path, parent_id)
    )
    db.commit()
    
    return jsonify({'message': 'Module added successfully'}), 201

@bp.route('/modules/<int:module_id>', methods=['PUT'])
def update_module(module_id):
    """更新模块"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    path = data.get('path')
    parent_id = data.get('parent_id')
    
    db = get_db()
    
    # 检查模块是否存在
    if not db.execute('SELECT id FROM modules WHERE id = ?', (module_id,)).fetchone():
        return jsonify({'error': 'Module not found'}), 404
    
    # 检查新名称是否已存在
    if name:
        existing = db.execute('SELECT id FROM modules WHERE name = ? AND id != ?', (name, module_id)).fetchone()
        if existing:
            return jsonify({'error': 'Module name already exists'}), 400
    
    # 检查父模块是否存在
    if parent_id:
        if not db.execute('SELECT id FROM modules WHERE id = ?', (parent_id,)).fetchone():
            return jsonify({'error': 'Parent module not found'}), 404
    
    # 构建更新字段
    update_fields = []
    update_params = []
    
    if name:
        update_fields.append('name = ?')
        update_params.append(name)
    
    if description is not None:
        update_fields.append('description = ?')
        update_params.append(description)
    
    if path is not None:
        update_fields.append('path = ?')
        update_params.append(path)
    
    if parent_id is not None:
        update_fields.append('parent_id = ?')
        update_params.append(parent_id)
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    # 执行更新
    update_params.append(module_id)
    db.execute(
        f'UPDATE modules SET {', '.join(update_fields)} WHERE id = ?',
        update_params
    )
    db.commit()
    
    return jsonify({'message': 'Module updated successfully'}), 200

@bp.route('/modules/<int:module_id>', methods=['DELETE'])
def delete_module(module_id):
    """删除模块"""
    db = get_db()
    
    # 检查模块是否存在
    if not db.execute('SELECT id FROM modules WHERE id = ?', (module_id,)).fetchone():
        return jsonify({'error': 'Module not found'}), 404
    
    # 删除模块
    db.execute('DELETE FROM modules WHERE id = ?', (module_id,))
    db.commit()
    
    return jsonify({'message': 'Module deleted successfully'}), 200

# 操作日志API
@bp.route('/operation-logs', methods=['GET'])
def get_operation_logs():
    """获取操作日志"""
    db = get_db()
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    module = request.args.get('module')
    action = request.args.get('action')
    admin_id = request.args.get('admin_id')
    
    # 构建查询条件
    query = 'SELECT * FROM operation_logs WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND DATE(created_at) >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND DATE(created_at) <= ?'
        params.append(end_date)
    
    if module:
        query += ' AND module = ?'
        params.append(module)
    
    if action:
        query += ' AND action = ?'
        params.append(action)
    
    if admin_id:
        query += ' AND admin_id = ?'
        params.append(admin_id)
    
    # 添加排序
    query += ' ORDER BY created_at DESC'
    
    # 执行查询
    logs = db.execute(query, params).fetchall()
    
    return jsonify([dict(log) for log in logs]), 200

@bp.route('/operation-logs/<int:log_id>', methods=['GET'])
def get_operation_log(log_id):
    """获取操作日志详情"""
    db = get_db()
    
    # 检查日志是否存在
    log = db.execute('SELECT * FROM operation_logs WHERE id = ?', (log_id,)).fetchone()
    if not log:
        return jsonify({'error': 'Operation log not found'}), 404
    
    return jsonify(dict(log)), 200

@bp.route('/schedules/manual-add-time-records', methods=['POST'])
def manual_add_time_records():
    """手动将排班写入工时和班别"""
    from app import auto_add_time_records
    import logging
    
    try:
        # 调用自动添加工时记录函数
        auto_add_time_records()
        return jsonify({'message': '手动添加工时记录成功'}), 200
    except Exception as e:
        logging.error(f"手动添加工时记录失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/duplicates', methods=['GET'])
def get_duplicate_time_records():
    """查询重复的工时记录"""
    db = get_db()
    
    # 查询重复的工时记录：同一用户同一天有多个工时记录
    duplicates = db.execute(
        '''SELECT user_id, DATE(start_time) as record_date, COUNT(*) as record_count 
        FROM time_records 
        GROUP BY user_id, DATE(start_time) 
        HAVING COUNT(*) > 1'''
    ).fetchall()
    
    duplicate_details = []
    for duplicate in duplicates:
        user_id = duplicate['user_id']
        record_date = duplicate['record_date']
        
        # 获取该用户当天的所有工时记录详情
        records = db.execute(
            '''SELECT id, start_time, end_time, duration, shift_type, description 
            FROM time_records 
            WHERE user_id = ? AND DATE(start_time) = ?''',
            (user_id, record_date)
        ).fetchall()
        
        # 获取用户名
        user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        username = user['username'] if user else f"用户{user_id}"
        
        duplicate_details.append({
            'user_id': user_id,
            'username': username,
            'record_date': record_date,
            'record_count': duplicate['record_count'],
            'records': [dict(record) for record in records]
        })
    
    return jsonify(duplicate_details), 200

@bp.route('/time-records/<int:record_id>', methods=['DELETE'])
def delete_time_record(record_id):
    """删除指定的工时记录"""
    db = get_db()
    
    try:
        # 检查记录是否存在
        record = db.execute('SELECT id FROM time_records WHERE id = ?', (record_id,)).fetchone()
        if not record:
            return jsonify({'error': '记录不存在'}), 404
        
        # 删除记录
        db.execute('DELETE FROM time_records WHERE id = ?', (record_id,))
        db.commit()
        
        return jsonify({'message': '记录删除成功'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/<int:record_id>', methods=['PUT'])
def update_time_record_admin(record_id):
    """更新指定的工时记录（管理员版本）"""
    data = request.get_json()
    db = get_db()
    
    try:
        # 检查记录是否存在
        record = db.execute('SELECT id FROM time_records WHERE id = ?', (record_id,)).fetchone()
        if not record:
            return jsonify({'error': '记录不存在'}), 404
        
        # 准备更新字段
        update_fields = []
        update_params = []
        
        if 'shift_type' in data:
            update_fields.append('shift_type = ?')
            update_params.append(data['shift_type'])
        if 'is_leave' in data:
            update_fields.append('is_leave = ?')
            update_params.append(data['is_leave'])
        if 'start_time' in data:
            update_fields.append('start_time = ?')
            update_params.append(data['start_time'])
        if 'end_time' in data:
            update_fields.append('end_time = ?')
            update_params.append(data['end_time'])
        if 'duration' in data:
            update_fields.append('duration = ?')
            update_params.append(data['duration'])
        if 'description' in data:
            update_fields.append('description = ?')
            update_params.append(data['description'])
        
        # 如果没有要更新的字段，直接返回成功
        if not update_fields:
            return jsonify({'message': 'No fields to update'}), 200
        
        # 执行更新
        update_params.append(record_id)
        query = f'UPDATE time_records SET {', '.join(update_fields)} WHERE id = ?'
        db.execute(query, update_params)
        db.commit()
        
        return jsonify({'message': 'Time record updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records', methods=['POST'])
def add_time_record_admin():
    """添加新的工时记录（管理员版本）"""
    data = request.get_json()
    db = get_db()
    
    try:
        # 验证必填字段
        user_id = data.get('user_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        duration = data.get('duration')
        
        if not user_id or not start_time or not end_time or duration is None:
            return jsonify({'error': 'User ID, start time, end time and duration are required'}), 400
        
        # 检查该用户当天是否已经有工时记录
        record_date = start_time.split('T')[0] if 'T' in start_time else start_time.split(' ')[0]
        existing_record = db.execute(
            '''SELECT id FROM time_records 
            WHERE user_id = ? AND DATE(start_time) = ?''',
            (user_id, record_date)
        ).fetchone()
        
        if existing_record:
            # 如果已经有记录，先删除旧记录
            db.execute('DELETE FROM time_records WHERE id = ?', (existing_record['id'],))
        
        # 添加新记录
        db.execute(
            '''INSERT INTO time_records 
            (user_id, start_time, end_time, duration, shift_type, is_leave, description) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                user_id,
                start_time,
                end_time,
                duration,
                data.get('shift_type', '白班'),
                data.get('is_leave', False),
                data.get('description', '')
            )
        )
        db.commit()
        
        return jsonify({'message': 'Time record added successfully'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/batch-delete', methods=['DELETE'])
def batch_delete_time_records():
    """批量删除工时记录，支持按角色批量删除"""
    data = request.get_json()
    
    # 获取批量删除参数
    role_id = data.get('role_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    db = get_db()
    
    try:
        # 构建查询条件
        query = 'DELETE FROM time_records WHERE DATE(start_time) BETWEEN ? AND ?'
        params = [start_date, end_date]
        
        # 如果指定了角色ID，添加角色过滤条件
        if role_id is not None:
            query += ' AND user_id IN (SELECT user_id FROM user_roles WHERE role_id = ?)'
            params.append(role_id)
        
        # 执行批量删除
        result = db.execute(query, params)
        db.commit()
        
        return jsonify({'message': f'Successfully deleted {result.rowcount} records'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/batch-add', methods=['POST'])
def batch_add_time_records():
    """批量添加工时记录，支持按角色或用户列表批量添加"""
    data = request.get_json()
    
    # 获取批量添加参数
    users = data.get('users')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    shift_type = data.get('shift_type', '白班')
    hours = data.get('hours')
    is_leave = data.get('is_leave', False)
    description = data.get('description', '')
    
    if not users or not isinstance(users, list) or len(users) == 0:
        return jsonify({'error': 'Users list is required and must be non-empty'}), 400
    
    if not start_date or not end_date or hours is None:
        return jsonify({'error': 'Start date, end date and hours are required'}), 400
    
    db = get_db()
    
    try:
        added_count = 0
        
        # 遍历日期范围
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end:
            record_date = current_date.strftime('%Y-%m-%d')
            
            # 构建开始时间和结束时间
            start_time = f'{record_date}T08:00:00'
            end_time = f'{record_date}T18:00:00'
            
            # 将小时转换为分钟
            duration = int(hours * 60)
            
            # 为每个用户添加记录
            for user_id in users:
                # 检查该用户当天是否已经有工时记录
                existing_record = db.execute(
                    '''SELECT id FROM time_records 
                    WHERE user_id = ? AND DATE(start_time) = ?''',
                    (user_id, record_date)
                ).fetchone()
                
                if existing_record:
                    # 如果已经有记录，先删除旧记录
                    db.execute('DELETE FROM time_records WHERE id = ?', (existing_record['id'],))
                
                # 添加新记录
                db.execute(
                    '''INSERT INTO time_records 
                    (user_id, start_time, end_time, duration, shift_type, is_leave, description) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        user_id,
                        start_time,
                        end_time,
                        duration,
                        shift_type,
                        is_leave,
                        description
                    )
                )
                
                added_count += 1
            
            # 增加一天
            current_date += timedelta(days=1)
        
        db.commit()
        
        return jsonify({'message': f'Successfully added {added_count} records'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records', methods=['GET'])
def get_all_time_records():
    """获取所有工时记录"""
    db = get_db()
    
    try:
        # 获取所有工时记录
        records = db.execute(
            '''SELECT tr.*, u.username 
            FROM time_records tr 
            JOIN users u ON tr.user_id = u.id 
            ORDER BY tr.start_time DESC'''
        ).fetchall()
        
        return jsonify([dict(record) for record in records]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/search', methods=['GET'])
def search_time_records():
    """搜索工时记录"""
    db = get_db()
    keyword = request.args.get('keyword', '')
    
    try:
        # 搜索工时记录
        records = db.execute(
            '''SELECT tr.*, u.username 
            FROM time_records tr 
            JOIN users u ON tr.user_id = u.id 
            WHERE u.username LIKE ? OR tr.description LIKE ? 
            ORDER BY tr.start_time DESC''',
            (f'%{keyword}%', f'%{keyword}%')
        ).fetchall()
        
        return jsonify([dict(record) for record in records]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/time-records/check-duplicates', methods=['GET'])
def check_duplicate_time_records():
    """检查重复的工时记录（兼容前端调用）"""
    # 直接调用已有的获取重复记录函数
    return get_duplicate_time_records()

# 用户登录日志API
@bp.route('/user-login-logs', methods=['GET'])
def get_user_login_logs():
    """获取用户登录日志"""
    db = get_db()
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    username = request.args.get('username')
    ip_address = request.args.get('ip_address')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    offset = (page - 1) * per_page
    
    # 构建查询条件
    query = 'SELECT * FROM user_login_logs WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND DATE(login_time) >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND DATE(login_time) <= ?'
        params.append(end_date)
    
    if user_id:
        query += ' AND user_id = ?'
        params.append(user_id)
    
    if username:
        query += ' AND username LIKE ?'
        params.append(f'%{username}%')
    
    if ip_address:
        query += ' AND ip_address LIKE ?'
        params.append(f'%{ip_address}%')
    
    # 查询总记录数
    count_query = query.replace('*', 'COUNT(*) as count')
    total = db.execute(count_query, params).fetchone()['count']
    
    # 添加排序和分页
    query += ' ORDER BY login_time DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    # 执行查询
    logs = db.execute(query, params).fetchall()
    
    # 处理登录时间，转换为北京时间
    logs_list = []
    for log in logs:
        log_dict = dict(log)
        # 转换登录时间为北京时间
        if log_dict['login_time']:
            from datetime import datetime, timezone
            from config import BEIJING_TIMEZONE
            # 解析时间字符串
            login_time = datetime.strptime(log_dict['login_time'], '%Y-%m-%d %H:%M:%S')
            # 设置为UTC时区
            utc_time = login_time.replace(tzinfo=timezone.utc)
            # 转换为北京时间
            beijing_time = utc_time.astimezone(BEIJING_TIMEZONE)
            # 格式化为北京时间字符串
            log_dict['login_time'] = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        logs_list.append(log_dict)
    
    return jsonify({
        'logs': logs_list,
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@bp.route('/user-login-logs/stats', methods=['GET'])
def get_user_login_stats():
    """获取用户登录统计信息"""
    db = get_db()
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 构建查询条件
    query = 'SELECT * FROM user_login_logs WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND DATE(login_time) >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND DATE(login_time) <= ?'
        params.append(end_date)
    
    # 执行查询
    logs = db.execute(query, params).fetchall()
    
    # 计算统计信息
    total_logins = len(logs)
    unique_users = len(set(log['user_id'] for log in logs))
    unique_ips = len(set(log['ip_address'] for log in logs))
    
    # 按日期统计登录次数
    login_by_date = {}
    for log in logs:
        # 转换登录时间为北京时间
        from datetime import datetime, timezone
        from config import BEIJING_TIMEZONE
        # 解析时间字符串
        login_time = datetime.strptime(log['login_time'], '%Y-%m-%d %H:%M:%S')
        # 设置为UTC时区
        utc_time = login_time.replace(tzinfo=timezone.utc)
        # 转换为北京时间
        beijing_time = utc_time.astimezone(BEIJING_TIMEZONE)
        # 格式化为北京时间日期字符串
        date = beijing_time.strftime('%Y-%m-%d')
        if date not in login_by_date:
            login_by_date[date] = 0
        login_by_date[date] += 1
    
    # 按用户统计登录次数
    login_by_user = {}
    for log in logs:
        username = log['username']
        if username not in login_by_user:
            login_by_user[username] = 0
        login_by_user[username] += 1
    
    return jsonify({
        'total_logins': total_logins,
        'unique_users': unique_users,
        'unique_ips': unique_ips,
        'login_by_date': login_by_date,
        'login_by_user': login_by_user
    }), 200

# 用户在线记录API
@bp.route('/user-online-logs', methods=['POST'])
def record_user_online():
    """记录用户在线访问"""
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    
    try:
        db = get_db()
        
        # 获取当前用户信息
        user_id = request.args.get('user_id', type=int)
        username = request.args.get('username')
        ip_address = request.remote_addr
        
        if not user_id or not username:
            return jsonify({'error': 'User ID and username are required'}), 400
        
        # 获取当前日期（北京时间）
        now = datetime.now(BEIJING_TIMEZONE)
        visit_date = now.strftime('%Y-%m-%d')
        
        # 尝试更新现有记录
        result = db.execute(
            '''UPDATE user_online_logs 
            SET last_visit_time = ?, visit_count = visit_count + 1 
            WHERE user_id = ? AND visit_date = ?''',
            (now, user_id, visit_date)
        )
        
        # 如果没有更新到记录，说明是今天第一次访问，插入新记录
        if result.rowcount == 0:
            db.execute(
                '''INSERT INTO user_online_logs 
                (user_id, username, ip_address, visit_date, last_visit_time, visit_count) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, username, ip_address, visit_date, now, 1)
            )
        
        db.commit()
        return jsonify({'message': 'User online record updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/user-online-logs', methods=['GET'])
def get_user_online_logs():
    """获取用户在线记录"""
    db = get_db()
    
    # 获取查询参数
    date = request.args.get('date')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 构建查询条件
    query = 'SELECT * FROM user_online_logs WHERE 1=1'
    params = []
    
    if date:
        query += ' AND visit_date = ?'
        params.append(date)
    elif start_date and end_date:
        query += ' AND visit_date BETWEEN ? AND ?'
        params.append(start_date)
        params.append(end_date)
    
    # 添加排序
    query += ' ORDER BY visit_date DESC, last_visit_time DESC'
    
    # 执行查询
    logs = db.execute(query, params).fetchall()
    
    return jsonify([dict(log) for log in logs]), 200

@bp.route('/user-online-logs/today', methods=['GET'])
def get_today_user_online_logs():
    """获取今天的用户在线记录"""
    from datetime import datetime
    from config import BEIJING_TIMEZONE
    
    db = get_db()
    
    # 获取今天的日期（北京时间）
    today = datetime.now(BEIJING_TIMEZONE).strftime('%Y-%m-%d')
    
    # 执行查询
    logs = db.execute(
        '''SELECT * FROM user_online_logs 
        WHERE visit_date = ? 
        ORDER BY last_visit_time DESC''',
        (today,)
    ).fetchall()
    
    return jsonify([dict(log) for log in logs]), 200

@bp.route('/user-online-logs/stats', methods=['GET'])
def get_user_online_stats():
    """获取用户在线统计信息"""
    db = get_db()
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 构建查询条件
    query = 'SELECT * FROM user_online_logs WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND visit_date >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND visit_date <= ?'
        params.append(end_date)
    
    # 执行查询
    logs = db.execute(query, params).fetchall()
    
    # 计算统计信息
    total_visits = len(logs)
    unique_users = len(set(log['user_id'] for log in logs))
    unique_ips = len(set(log['ip_address'] for log in logs))
    
    # 按日期统计在线人数
    online_by_date = {}
    for log in logs:
        visit_date = log['visit_date']
        if visit_date not in online_by_date:
            online_by_date[visit_date] = 0
        online_by_date[visit_date] += 1
    
    # 按用户统计访问次数
    visits_by_user = {}
    for log in logs:
        username = log['username']
        if username not in visits_by_user:
            visits_by_user[username] = 0
        visits_by_user[username] += log['visit_count']
    
    return jsonify({
        'total_visits': total_visits,
        'unique_users': unique_users,
        'unique_ips': unique_ips,
        'online_by_date': online_by_date,
        'visits_by_user': visits_by_user
    }), 200


