from flask import Blueprint, request, jsonify
from utils.db import get_db
from utils.salary_calculator import (
    calculate_base_salary,
    calculate_seniority_bonus,
    calculate_total_salary
)

bp = Blueprint('salary', __name__)

@bp.route('/info', methods=['POST'])
def save_salary_info():
    data = request.get_json()
    user_id = data.get('user_id')
    month = data.get('month')
    salary_level = data.get('salary_level')
    utility_fee = data.get('utility_fee', 0)
    insurance = data.get('insurance')
    tax = data.get('tax', 0)
    leave_hours = data.get('leave_hours', 0)
    total_night_shifts = data.get('total_night_shifts', 0)
    simulated_hours = data.get('simulated_hours', 0)
    # 忽略performance_bonus字段，因为数据库表中可能没有这个字段
    # performance_bonus = data.get('performance_bonus', 0)
    
    if not user_id or not month or not salary_level:
        return jsonify({'error': 'User ID, month and salary level are required'}), 400
    
    # 获取用户信息以计算工龄奖
    db = get_db()
    user = db.execute('SELECT hire_date FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 计算各项工资数据
    base_salary = calculate_base_salary(salary_level)
    seniority_bonus = calculate_seniority_bonus(user['hire_date'])
    
    # 保存或更新工资信息
    existing = db.execute(
        'SELECT id FROM salary_info WHERE user_id = ? AND month = ?',
        (user_id, month)
    ).fetchone()
    
    if existing:
        # 更新现有记录
        db.execute(
            '''UPDATE salary_info SET salary_level = ?, base_salary = ?, seniority_bonus = ?, 
            utility_fee = ?, insurance = ?, tax = ?, leave_hours = ?, total_night_shifts = ?, 
            simulated_hours = ? WHERE id = ?''',
            (salary_level, base_salary, seniority_bonus, utility_fee, insurance, tax, leave_hours, total_night_shifts, simulated_hours, existing['id'])
        )
    else:
        # 创建新记录
        db.execute(
            '''INSERT INTO salary_info (user_id, month, salary_level, base_salary, seniority_bonus, 
            utility_fee, insurance, tax, leave_hours, total_night_shifts, simulated_hours) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, month, salary_level, base_salary, seniority_bonus, utility_fee, insurance, tax, leave_hours, total_night_shifts, simulated_hours)
        )
    
    db.commit()
    
    return jsonify({'message': 'Salary information saved successfully'}), 201

@bp.route('/info/<month>', methods=['GET'])
def get_salary_info(month):
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    salary_info = db.execute(
        'SELECT * FROM salary_info WHERE user_id = ? AND month = ?',
        (user_id, month)
    ).fetchone()
    
    if not salary_info:
        return jsonify({'error': 'Salary information not found'}), 404
    
    return jsonify(dict(salary_info)), 200

@bp.route('/calculate', methods=['GET'])
def calculate_salary():
    user_id = request.args.get('user_id')
    month = request.args.get('month')
    simulated_hours = request.args.get('simulated_hours')
    
    if not user_id or not month:
        return jsonify({'error': 'User ID and month are required'}), 400
    
    db = get_db()
    
    # 获取用户信息
    user = db.execute('SELECT hire_date, salary_level FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 调试日志：打印用户信息
    import logging
    # 将sqlite3.Row转换为字典
    user_dict = dict(user)
    logging.info(f"用户信息: {user_dict}")
    logging.info(f"用户薪级: {user_dict.get('salary_level')}")
    
    # 检查是否提供了模拟总工时
    if simulated_hours and float(simulated_hours) > 0:
        # 使用模拟总工时
        total_hours = float(simulated_hours)
    else:
        # 计算当月实际总工时
        start_date = f'{month}-01 00:00:00'
        if month.endswith('12'):
            next_month = f'{int(month[:4])+1}-01'
        else:
            next_month = f'{month[:4]}-{int(month[5:7])+1:02d}'
        end_date = f'{next_month}-01 00:00:00'
        
        total_minutes = db.execute(
            '''SELECT SUM(duration) as total_minutes 
            FROM time_records 
            WHERE user_id = ? AND start_time >= ? AND start_time < ? AND NOT is_leave''',
            (user_id, start_date, end_date)
        ).fetchone()['total_minutes'] or 0
        
        total_hours = total_minutes / 60
    
    # 计算当月夜班天数（大于等于8小时的夜班记录）
    start_date = f'{month}-01 00:00:00'
    if month.endswith('12'):
        next_month = f'{int(month[:4])+1}-01'
    else:
        next_month = f'{month[:4]}-{int(month[5:7])+1:02d}'
    end_date = f'{next_month}-01 00:00:00'
    
    # 查询一个月内大于等于8小时（480分钟）的夜班记录数量
    logging.info(f"查询夜班记录: user_id={user_id}, start_date={start_date}, end_date={end_date}")
    
    # 先查询所有夜班记录，方便调试
    all_night_records = db.execute(
        '''SELECT id, user_id, shift_type, duration, is_leave, start_time 
        FROM time_records 
        WHERE user_id = ? AND start_time >= ? AND start_time < ?''',
        (user_id, start_date, end_date)
    ).fetchall()
    logging.info(f"所有记录: {all_night_records}")
    
    # 查询符合条件的夜班记录，显示详细信息
    night_records = db.execute(
        '''SELECT id, user_id, shift_type, duration, is_leave, start_time 
        FROM time_records 
        WHERE user_id = ? AND start_time >= ? AND start_time < ? 
        AND shift_type = '夜班' AND duration >= 480 AND NOT is_leave''',
        (user_id, start_date, end_date)
    ).fetchall()
    logging.info(f"符合条件的夜班记录: {night_records}")
    night_shifts = len(night_records)
    
    logging.info(f"符合条件的夜班记录数量: {night_shifts}")
    
    # 计算当月请假小时数
    start_date = f'{month}-01 00:00:00'
    if month.endswith('12'):
        next_month = f'{int(month[:4])+1}-01'
    else:
        next_month = f'{month[:4]}-{int(month[5:7])+1:02d}'
    end_date = f'{next_month}-01 00:00:00'
    
    # 计算当月请假小时数
    leave_minutes = db.execute(
        '''SELECT SUM(duration) as leave_minutes 
        FROM time_records 
        WHERE user_id = ? AND start_time >= ? AND start_time < ? AND is_leave''',
        (user_id, start_date, end_date)
    ).fetchone()['leave_minutes'] or 0
    
    leave_hours = leave_minutes / 60
    logging.info(f"当月请假小时数: {leave_hours}")
    
    # 获取或创建工资信息
    salary_info = db.execute(
        'SELECT * FROM salary_info WHERE user_id = ? AND month = ?',
        (user_id, month)
    ).fetchone()
    
    # 计算各项工资数据
    logging.info(f"计算底薪: salary_level={user_dict.get('salary_level') or 'E17'}")
    base_salary = calculate_base_salary(user_dict.get('salary_level') or 'E17')  # 默认薪级E17
    logging.info(f"计算结果: base_salary={base_salary}")
    seniority_bonus = calculate_seniority_bonus(user_dict.get('hire_date'))
    logging.info(f"工龄奖: seniority_bonus={seniority_bonus}")
    
    if salary_info:
        # 更新现有记录，保留原有值
        salary_info_dict = dict(salary_info)
        salary_info_dict['salary_level'] = user_dict.get('salary_level') or 'E17'
        salary_info_dict['base_salary'] = base_salary
        salary_info_dict['seniority_bonus'] = seniority_bonus
        salary_info_dict['total_night_shifts'] = night_shifts
        # 保留原有的值
        salary_info_dict['utility_fee'] = salary_info_dict.get('utility_fee', 0)
        salary_info_dict['insurance'] = salary_info_dict.get('insurance', 0)
        # 更新请假小时数
        salary_info_dict['leave_hours'] = leave_hours
        salary_info_dict['simulated_hours'] = salary_info_dict.get('simulated_hours', 0)
        
        # 更新数据库，包含所有字段
        db.execute(
            '''UPDATE salary_info SET salary_level = ?, base_salary = ?, seniority_bonus = ?, 
            total_night_shifts = ?, utility_fee = ?, insurance = ?, leave_hours = ?, 
            simulated_hours = ? WHERE id = ?''',
            (salary_info_dict['salary_level'], salary_info_dict['base_salary'], 
             salary_info_dict['seniority_bonus'], salary_info_dict['total_night_shifts'],
             salary_info_dict['utility_fee'], salary_info_dict['insurance'], salary_info_dict['leave_hours'],
             salary_info_dict['simulated_hours'], salary_info['id'])
        )
        db.commit()
    else:
        # 创建新记录，使用从工时记录中计算出的请假小时数
        salary_info_dict = {
            'user_id': user_id,
            'month': month,
            'salary_level': user_dict.get('salary_level') or 'E17',
            'base_salary': base_salary,
            'seniority_bonus': seniority_bonus,
            'utility_fee': 0,
            'insurance': 0,
            'tax': 0,
            'leave_hours': leave_hours,
            'total_night_shifts': night_shifts,
            'simulated_hours': 0
        }
        
        # 保存到数据库
        db.execute(
            '''INSERT INTO salary_info (user_id, month, salary_level, base_salary, seniority_bonus, 
            utility_fee, insurance, tax, leave_hours, total_night_shifts, simulated_hours) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (salary_info_dict['user_id'], salary_info_dict['month'], 
             salary_info_dict['salary_level'], salary_info_dict['base_salary'], 
             salary_info_dict['seniority_bonus'], salary_info_dict['utility_fee'], 
             salary_info_dict['insurance'], salary_info_dict['tax'], 
             salary_info_dict['leave_hours'], salary_info_dict['total_night_shifts'],
             salary_info_dict['simulated_hours'])
        )
        db.commit()
    
    # 获取工资算法配置
    configs = {}
    config_rows = db.execute('SELECT config_key, config_value FROM salary_config').fetchall()
    for row in config_rows:
        configs[row['config_key']] = row['config_value']
    
    # 计算工资
    salary_result = calculate_total_salary(salary_info_dict, total_hours, configs)
    
    return jsonify({
        'month': month,
        'total_hours': round(total_hours, 2),
        'night_shifts': night_shifts,
        'salary_details': salary_result
    }), 200

@bp.route('/levels', methods=['GET'])
def get_salary_levels():
    # 生成薪资等级列表
    levels = []
    
    # 生成E级薪级（E8到E19）
    for i in range(8, 20):
        level = f'E{i}'
        base_salary = calculate_base_salary(level)
        levels.append({
            'level': level,
            'base_salary': base_salary
        })
    
    # 生成D级薪级（D1到D10）
    for i in range(1, 11):
        level = f'D{i}'
        base_salary = calculate_base_salary(level)
        levels.append({
            'level': level,
            'base_salary': base_salary
        })
    
    return jsonify(levels), 200

@bp.route('/config', methods=['GET'])
def get_salary_config():
    """获取工资算法配置"""
    db = get_db()
    configs = db.execute('SELECT * FROM salary_config').fetchall()
    return jsonify([dict(config) for config in configs]), 200

@bp.route('/config', methods=['POST'])
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

@bp.route('/config/reset', methods=['POST'])
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