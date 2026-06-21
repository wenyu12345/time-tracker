from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db
from utils.salary_calculator import calculate_seniority_bonus
import json

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    hire_date = data.get('hire_date')
    salary_level = data.get('salary_level')
    roles = data.get('roles', [])  # 角色列表，默认为空
    
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
    
    # 处理角色分配
    if roles:
        # 验证角色是否存在
        for role_id in roles:
            role = db.execute('SELECT id FROM roles WHERE id = ?', (role_id,)).fetchone()
            if role:
                # 分配角色
                db.execute(
                    'INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)',
                    (user_id, role_id)
                )
    
    db.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # 检查用户是否被禁用（is_active = 0 表示禁用）
    # sqlite3.Row没有get方法，需要用keys()检查或者用try/except
    is_active = user['is_active'] if 'is_active' in user.keys() else 1  # 默认1为活跃
    if is_active == 0:
        return jsonify({'error': '该账号已被禁用，请联系管理员'}), 403
    
    # 记录登录日志
    ip_address = request.remote_addr
    db.execute(
        'INSERT INTO user_login_logs (user_id, username, ip_address) VALUES (?, ?, ?)',
        (user['id'], user['username'], ip_address)
    )
    db.commit()

    # 插入登录通知
    user_id = user['id']
    notification_data = json.dumps({'user_id': user_id, 'username': username}, ensure_ascii=False)
    db.execute(
        'INSERT INTO notifications (type, title, message, data) VALUES (?, ?, ?, ?)',
        ('user_login', '用户登录通知', f'{username} 刚刚登录了系统', notification_data)
    )
    db.commit()

    # 简单的认证，返回用户信息
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'hire_date': user['hire_date'],
        'salary_level': user['salary_level'],
        'seniority_bonus': calculate_seniority_bonus(user['hire_date'])
    }), 200

@bp.route('/user', methods=['GET'])
def get_user():
    # 简化实现，实际应该使用JWT认证
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'hire_date': user['hire_date'],
        'salary_level': user['salary_level'],
        'seniority_bonus': calculate_seniority_bonus(user['hire_date'])
    }), 200

@bp.route('/user/salary-level', methods=['PUT'])
def update_salary_level():
    # 简化实现，实际应该使用JWT认证
    data = request.get_json()
    user_id = data.get('user_id')
    salary_level = data.get('salary_level')
    
    if not user_id or not salary_level:
        return jsonify({'error': 'User ID and salary level are required'}), 400
    
    db = get_db()
    
    # 检查用户是否存在
    user = db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 更新用户薪级
    db.execute(
        'UPDATE users SET salary_level = ? WHERE id = ?',
        (salary_level, user_id)
    )
    db.commit()
    
    return jsonify({'message': 'Salary level updated successfully'}), 200

@bp.route('/user/password', methods=['PUT'])
def update_password():
    # 简化实现，实际应该使用JWT认证
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username')
    new_password = data.get('new_password')
    old_password = data.get('old_password')
    privilege_code = data.get('privilege_code')
    
    if not new_password:
        return jsonify({'error': 'New password is required'}), 400
    
    db = get_db()
    
    # 检查用户是否存在
    if user_id:
        user = db.execute('SELECT id, password FROM users WHERE id = ?', (user_id,)).fetchone()
    elif username:
        user = db.execute('SELECT id, password FROM users WHERE username = ?', (username,)).fetchone()
    else:
        return jsonify({'error': 'User ID or username is required'}), 400
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 验证密码修改权限
    is_authorized = False
    
    # 方式1：使用老密码验证
    if old_password:
        if check_password_hash(user['password'], old_password):
            is_authorized = True
    # 方式2：使用特权码验证
    elif privilege_code == '123':
        is_authorized = True
    
    if not is_authorized:
        return jsonify({'error': 'Invalid old password'}), 401
    
    # 更新用户密码
    hashed_password = generate_password_hash(new_password)
    if user_id:
        db.execute(
            'UPDATE users SET password = ? WHERE id = ?',
            (hashed_password, user_id)
        )
    else:
        db.execute(
            'UPDATE users SET password = ? WHERE username = ?',
            (hashed_password, username)
        )
    db.commit()
    
    return jsonify({'message': 'Password updated successfully'}), 200

@bp.route('/user/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id):
    """更新用户账号状态（启用/禁用）"""
    data = request.get_json()
    is_active = data.get('is_active')  # 1 启用, 0 禁用

    if is_active is None:
        return jsonify({'error': 'is_active参数是必需的'}), 400

    if is_active not in [0, 1]:
        return jsonify({'error': 'is_active必须是0或1'}), 400

    db = get_db()

    # 检查用户是否存在
    user = db.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 更新用户状态
    db.execute('UPDATE users SET is_active = ? WHERE id = ?', (is_active, user_id))
    db.commit()

    status_text = '启用' if is_active == 1 else '禁用'
    return jsonify({
        'message': f'用户 {user["username"]} 已{status_text}',
        'user_id': user_id,
        'is_active': is_active
    }), 200

@bp.route('/users/inactive', methods=['GET'])
def get_inactive_users():
    """获取所有被禁用的用户列表"""
    db = get_db()

    users = db.execute("""
        SELECT u.id, u.username, u.is_active, r.name as role_name
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.is_active = 0
        ORDER BY u.username
    """).fetchall()

    # 按用户分组
    result = {}
    for user in users:
        username = user['username']
        if username not in result:
            result[username] = {
                'id': user['id'],
                'username': username,
                'is_active': user['is_active'],
                'roles': []
            }
        if user['role_name']:
            result[username]['roles'].append(user['role_name'])

    return jsonify({'users': list(result.values())}), 200

@bp.route('/users/resigned', methods=['GET'])
def get_resigned_users():
    """获取所有自离人员列表"""
    db = get_db()

    users = db.execute("""
        SELECT DISTINCT u.id, u.username, u.is_active
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = '自离'
        ORDER BY u.username
    """).fetchall()

    return jsonify({
        'users': [{
            'id': user['id'],
            'username': user['username'],
            'is_active': user['is_active'],
            'login_disabled': user['is_active'] == 0
        } for user in users]
    }), 200

@bp.route('/user/<int:user_id>/is-resigned', methods=['GET'])
def check_user_resigned(user_id):
    """检查用户是否标记为自离（同时检查 user_roles 和 time_records.description）"""
    db = get_db()

    user = db.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 方式1: user_roles 有 '自离' 角色
    role_check = db.execute("""
        SELECT 1 FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = ? AND r.name = '自离'
    """, (user_id,)).fetchone()

    # 方式2: 最近的 time_records.description = '自离'
    desc_check = db.execute("""
        SELECT 1 FROM time_records tr
        WHERE tr.user_id = ? AND tr.description = '自离'
        ORDER BY tr.start_time DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    is_resigned = (role_check is not None) or (desc_check is not None)

    return jsonify({
        'user_id': user_id,
        'username': user['username'],
        'is_resigned': is_resigned
    }), 200

@bp.route('/user/<int:user_id>/mark-resigned', methods=['PUT'])
def mark_user_resigned(user_id):
    """标记用户为自离状态
    - 保存原始岗位/工时/班次到 description 字段
    - 删除所有其他角色，只保留'自离'角色
    - 将is_active设为0，禁用登录
    """
    db = get_db()
    data = request.get_json(silent=True) or {}
    date_str = data.get('date')  # 新增：接收日期参数
    remark = data.get('remark', '')

    # 检查用户是否存在
    user = db.execute('SELECT id, username, is_active, shift_type FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 确保'自离'角色存在
    resigned_role = db.execute("SELECT id FROM roles WHERE name = '自离'").fetchone()
    if not resigned_role:
        db.execute("INSERT INTO roles (name) VALUES ('自离')")
        resigned_role_id = db.execute("SELECT last_insert_rowid() as id").fetchone()['id']
    else:
        resigned_role_id = resigned_role['id']

    # 查找当天的工时记录，保存原始信息
    orig_role = ''
    orig_duration = 0
    orig_shift = ''
    orig_desc = ''
    if date_str:
        old_record = db.execute(
            "SELECT tr.description, tr.duration, tr.shift_type FROM time_records tr "
            "WHERE tr.user_id = ? AND DATE(tr.start_time) = ?",
            (user_id, date_str)
        ).fetchone()
        if old_record:
            orig_desc = old_record['description'] or ''
            orig_duration = old_record['duration'] or 0
            orig_shift = old_record['shift_type'] or user['shift_type'] or ''
            # 如果原 description 已经是角色名，取它；否则查 user_roles
            if orig_desc and orig_desc not in ('自离', '', '请假', '调休'):
                orig_role = orig_desc
            if not orig_role:
                roles = db.execute(
                    "SELECT r.name FROM user_roles ur JOIN roles r ON ur.role_id = r.id "
                    "WHERE ur.user_id = ? AND r.name != '自离'",
                    (user_id,)
                ).fetchall()
                if roles:
                    orig_role = roles[0]['name']

    # 删除用户所有现有角色
    db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))

    # 分配'自离'角色
    db.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, resigned_role_id))

    # 禁用登录
    db.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))

    # 构造自离 description：自离|原岗位:X|原工时:Y|原班次:Z|备注:...
    new_desc = f"自离|原岗位:{orig_role}|原工时:{orig_duration}|原班次:{orig_shift}"
    if remark:
        new_desc += f"|备注:{remark}"

    # 更新当天的工时记录
    if date_str:
        existing = db.execute(
            "SELECT id FROM time_records WHERE user_id = ? AND DATE(start_time) = ?",
            (user_id, date_str)
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE time_records SET description = ?, is_leave = 0 WHERE id = ?",
                (new_desc, existing['id'])
            )
        else:
            # 没有当天记录，创建一条
            start_time = f"{date_str} 08:00:00"
            end_time = f"{date_str} 18:00:00"
            db.execute(
                "INSERT INTO time_records (user_id, start_time, end_time, duration, shift_type, description, is_leave) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, start_time, end_time, 0, user['shift_type'] or '白班', new_desc, 0)
            )

    db.commit()

    return jsonify({
        'message': f'用户 {user["username"]} 已标记为自离，原岗位={orig_role}，原工时={orig_duration}分钟',
        'user_id': user_id,
        'username': user['username'],
        'is_resigned': True,
        'is_active': 0,
        'orig_role': orig_role,
        'orig_duration': orig_duration
    }), 200

@bp.route('/user/<int:user_id>/unmark-resigned', methods=['PUT'])
def unmark_user_resigned(user_id):
    """取消用户自离状态
    支持两种自离检测方式：
    1) user_roles 有 '自离' 角色
    2) time_records.description 以 '自离' 开头
    操作：
    - 从 description 解析：原岗位/原工时/原班次
    - 恢复 user_roles 为原岗位
    - 恢复 time_records 的 description、duration、shift_type
    - 将is_active设为1，恢复登录
    """
    db = get_db()
    data = request.get_json(silent=True) or {}
    restore_date = data.get('date')

    # 辅助函数：解析自离 description 格式
    def parse_resigned_desc(desc):
        """解析 '自离|原岗位:X|原工时:Y|原班次:Z|备注:...' 返回 dict"""
        result = {'role': '', 'duration': 0, 'shift': '', 'remark': ''}
        if not desc or not desc.startswith('自离'):
            return result
        if desc == '自离':
            return result
        # 以 '|' 分割，但要注意备注可能也有 '|'
        parts = desc.split('|')
        for part in parts[1:]:  # 跳过第一个 '自离'
            if part.startswith('原岗位:'):
                result['role'] = part[len('原岗位:'):]
            elif part.startswith('原工时:'):
                try:
                    result['duration'] = int(part[len('原工时:'):])
                except:
                    pass
            elif part.startswith('原班次:'):
                result['shift'] = part[len('原班次:'):]
            elif part.startswith('备注:'):
                result['remark'] = part[len('备注:'):]
        return result

    # 检查用户是否存在
    user = db.execute('SELECT id, username, is_active, shift_type FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 两种自离检测方式
    # 方式1: user_roles 有 '自离' 角色
    role_check = db.execute("""
        SELECT 1 FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = ? AND r.name = '自离'
    """, (user_id,)).fetchone()

    # 方式2: 最近的 time_records.description 以 '自离' 开头
    desc_check = db.execute("""
        SELECT 1 FROM time_records tr
        WHERE tr.user_id = ? AND tr.description LIKE '自离%'
        ORDER BY tr.start_time DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    is_resigned = (role_check is not None) or (desc_check is not None)

    if not is_resigned:
        return jsonify({
            'message': f'用户 {user["username"]} 不是自离状态，无需取消',
            'user_id': user_id,
            'username': user['username'],
            'is_resigned': False
        }), 200

    # 1) 解析当天记录的 description，取回原始岗位/工时/班次
    orig_data = {'role': '', 'duration': 0, 'shift': ''}
    if restore_date:
        rec = db.execute(
            "SELECT tr.description, tr.duration, tr.shift_type FROM time_records tr "
            "WHERE tr.user_id = ? AND DATE(tr.start_time) = ? AND tr.description LIKE '自离%'",
            (user_id, restore_date)
        ).fetchone()
        if rec and rec['description'] and rec['description'].startswith('自离'):
            parsed = parse_resigned_desc(rec['description'])
            orig_data['role'] = parsed['role']
            orig_data['duration'] = parsed['duration'] if parsed['duration'] > 0 else rec['duration']
            orig_data['shift'] = parsed['shift'] or rec['shift_type']

    # 如果没有解析到岗位，尝试从历史记录推断
    if not orig_data['role']:
        historical = db.execute(
            "SELECT tr.description FROM time_records tr "
            "WHERE tr.user_id = ? AND tr.description NOT LIKE '自离%' "
            "AND tr.description NOT IN ('', '请假', '调休', '未到岗') "
            "ORDER BY tr.start_time DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        if historical and historical['description']:
            orig_data['role'] = historical['description']

    # 2) 删除 user_roles 中的 '自离' 角色
    db.execute("""
        DELETE FROM user_roles
        WHERE user_id = ? AND role_id IN (
            SELECT id FROM roles WHERE name = '自离'
        )
    """, (user_id,))

    # 3) 恢复原岗位角色（如果解析到了，否则分配默认角色）
    target_role = orig_data['role'] or '涂布'
    if target_role:
        db.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
        role_obj = db.execute("SELECT id FROM roles WHERE name = ?", (target_role,)).fetchone()
        if not role_obj:
            cursor = db.execute("INSERT INTO roles (name) VALUES (?)", (target_role,))
            role_id = cursor.lastrowid
        else:
            role_id = role_obj['id']
        db.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, role_id))

    # 4) 恢复登录权限
    db.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))

    # 5) 恢复当天工时记录（从自离格式恢复到原岗位）
    updated_records = 0
    if restore_date:
        records = db.execute("""
            SELECT id, shift_type FROM time_records
            WHERE user_id = ? AND DATE(start_time) = ?
            AND description LIKE '自离%'
        """, (user_id, restore_date)).fetchall()

        # 决定恢复的工时
        recovery_duration = orig_data['duration'] if orig_data['duration'] > 0 else 690
        recovery_shift = orig_data['shift'] or user['shift_type'] or '白班'

        # 根据班次设置起止时间
        start_time_str = f"{restore_date} 08:00:00"
        end_time_str = f"{restore_date} 19:30:00"
        if '夜班' in recovery_shift:
            start_time_str = f"{restore_date} 19:00:00"
            end_time_str = f"{restore_date} 07:30:00"

        for rec in records:
            db.execute("""
                UPDATE time_records
                SET description = ?, is_leave = 0, duration = ?,
                    start_time = ?, end_time = ?, shift_type = ?
                WHERE id = ?
            """, (target_role, recovery_duration, start_time_str, end_time_str, recovery_shift, rec['id']))
            updated_records += 1

    db.commit()

    # 获取当前角色
    current_roles = db.execute("""
        SELECT r.name FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = ?
    """, (user_id,)).fetchall()

    return jsonify({
        'message': f'用户 {user["username"]} 已取消自离，恢复岗位={target_role}，工时={orig_data["duration"]}分钟',
        'user_id': user_id,
        'username': user['username'],
        'is_resigned': False,
        'is_active': 1,
        'current_roles': [r['name'] for r in current_roles],
        'restored_role': target_role,
        'restored_duration': orig_data['duration'],
        'updated_records': updated_records
    }), 200

@bp.route('/notifications/pull', methods=['GET'])
def pull_notifications():
    """拉取该用户未读的通知列表（last_id之后的通知）"""
    last_id = int(request.args.get('last_id', 0))
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id参数是必需的'}), 400

    db = get_db()

    # 查询last_id之后的通知，LEFT JOIN判断是否已读，只返回未读的
    notifications = db.execute("""
        SELECT n.id, n.type, n.title, n.message, n.data, n.created_at
        FROM notifications n
        LEFT JOIN user_notification_read unr
            ON unr.notification_id = n.id AND unr.user_id = ?
        WHERE n.id > ? AND unr.notification_id IS NULL
        ORDER BY n.id DESC
    """, (user_id, last_id)).fetchall()

    # 查询当前最大的通知ID
    latest_row = db.execute('SELECT COALESCE(MAX(id), 0) as latest_id FROM notifications').fetchone()
    latest_id = latest_row['latest_id'] if latest_row else 0

    return jsonify({
        'notifications': [{
            'id': n['id'],
            'title': n['title'],
            'message': n['message'],
            'type': n['type'],
            'data': n['data'],
            'created_at': n['created_at']
        } for n in notifications],
        'latest_id': latest_id
    }), 200

@bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """将指定通知标记为该用户已读"""
    data = request.get_json()
    user_id = data.get('user_id') if data else None

    if not user_id:
        return jsonify({'error': 'user_id参数是必需的'}), 400

    db = get_db()

    # 检查通知是否存在
    notification = db.execute('SELECT id FROM notifications WHERE id = ?', (notification_id,)).fetchone()
    if not notification:
        return jsonify({'error': '通知不存在'}), 404

    # 插入或忽略已读记录（主键约束避免重复）
    db.execute("""
        INSERT OR IGNORE INTO user_notification_read (user_id, notification_id)
        VALUES (?, ?)
    """, (user_id, notification_id))
    db.commit()

    return jsonify({'success': True}), 200

@bp.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """一键将所有通知标记为该用户已读"""
    data = request.get_json()
    user_id = data.get('user_id') if data else None

    if not user_id:
        return jsonify({'error': 'user_id参数是必需的'}), 400

    db = get_db()

    # 获取所有现有的通知ID
    all_notifications = db.execute('SELECT id FROM notifications').fetchall()
    if not all_notifications:
        return jsonify({'success': True, 'count': 0}), 200

    # 批量插入所有通知为已读
    read_records = [(user_id, n['id']) for n in all_notifications]
    db.executemany("""
        INSERT OR IGNORE INTO user_notification_read (user_id, notification_id)
        VALUES (?, ?)
    """, read_records)
    db.commit()

    # 统计本次新标记为已读的数量
    cursor = db.execute('SELECT changes() as changed_count')
    changed_count = cursor.fetchone()['changed_count']

    return jsonify({'success': True, 'count': changed_count}), 200