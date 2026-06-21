from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from utils.db import get_db

bp = Blueprint('stats', __name__)

@bp.route('/daily', methods=['GET'])
def get_daily_stats():
    user_id = request.args.get('user_id')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    # 计算当天的开始和结束时间
    start_date = f'{date}T00:00:00'  # 使用ISO格式时间
    end_date = f'{date}T23:59:59'  # 使用ISO格式时间
    
    # 获取当天工时记录
    records = db.execute(
        '''SELECT shift_type, is_leave, SUM(duration) as total_minutes 
        FROM time_records 
        WHERE user_id = ? AND start_time BETWEEN ? AND ? 
        GROUP BY shift_type, is_leave''',
        (user_id, start_date, end_date)
    ).fetchall()
    
    # 计算总工时
    total_hours = 0
    leave_hours = 0
    night_shifts = 0
    
    for record in records:
        minutes = record['total_minutes'] or 0
        hours = minutes / 60
        
        if record['is_leave']:
            leave_hours += hours
        else:
            total_hours += hours
            if record['shift_type'] == '夜班':
                night_shifts += 1
    
    return jsonify({
        'date': date,
        'total_hours': round(total_hours, 2),
        'leave_hours': round(leave_hours, 2),
        'night_shifts': night_shifts
    }), 200

@bp.route('/weekly', methods=['GET'])
def get_weekly_stats():
    user_id = request.args.get('user_id')
    year = request.args.get('year', str(datetime.now().year))
    week = request.args.get('week', str(datetime.now().isocalendar()[1]))
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # 计算周的开始和结束时间
    start_date = datetime.fromisocalendar(int(year), int(week), 1)
    end_date = start_date + timedelta(days=6)
    
    start_str = start_date.strftime('%Y-%m-%dT00:00:00')  # 使用ISO格式时间
    end_str = end_date.strftime('%Y-%m-%dT23:59:59')  # 使用ISO格式时间
    
    db = get_db()
    
    # 获取本周工时记录
    records = db.execute(
        '''SELECT SUM(duration) as total_minutes, SUM(CASE WHEN is_leave THEN duration ELSE 0 END) as leave_minutes,
        COUNT(CASE WHEN shift_type = '夜班' AND NOT is_leave THEN 1 END) as night_shifts
        FROM time_records 
        WHERE user_id = ? AND start_time BETWEEN ? AND ?''',
        (user_id, start_str, end_str)
    ).fetchone()
    
    total_hours = (records['total_minutes'] or 0) / 60
    leave_hours = (records['leave_minutes'] or 0) / 60
    night_shifts = records['night_shifts'] or 0
    
    return jsonify({
        'year': year,
        'week': week,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_hours': round(total_hours, 2),
        'leave_hours': round(leave_hours, 2),
        'night_shifts': night_shifts
    }), 200

@bp.route('/monthly', methods=['GET'])
def get_monthly_stats():
    user_id = request.args.get('user_id')
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # 计算月的开始和结束时间
    start_date = f'{month}-01T00:00:00'  # 使用ISO格式时间
    if month.endswith('12'):
        next_month = f'{int(month[:4])+1}-01'
    else:
        next_month = f'{month[:4]}-{int(month[5:7])+1:02d}'
    end_date = f'{next_month}-01T00:00:00'  # 使用ISO格式时间
    
    db = get_db()
    
    # 获取本月工时记录
    records = db.execute(
        '''SELECT SUM(duration) as total_minutes, SUM(CASE WHEN is_leave THEN duration ELSE 0 END) as leave_minutes,
        COUNT(CASE WHEN shift_type = '夜班' AND NOT is_leave THEN 1 END) as night_shifts
        FROM time_records 
        WHERE user_id = ? AND start_time >= ? AND start_time < ?''',
        (user_id, start_date, end_date)
    ).fetchone()
    
    total_hours = (records['total_minutes'] or 0) / 60
    leave_hours = (records['leave_minutes'] or 0) / 60
    night_shifts = records['night_shifts'] or 0
    
    return jsonify({
        'month': month,
        'total_hours': round(total_hours, 2),
        'leave_hours': round(leave_hours, 2),
        'night_shifts': night_shifts
    }), 200

@bp.route('/project', methods=['GET'])
def get_project_stats():
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    query = '''SELECT p.name, p.color, SUM(tr.duration) as total_minutes 
              FROM time_records tr 
              LEFT JOIN projects p ON tr.project_id = p.id 
              WHERE tr.user_id = ? '''
    params = [user_id]
    
    if start_date:
        # 确保使用ISO格式时间
        if ' ' in start_date:  # 处理YYYY-MM-DD HH:MM:SS格式
            start_date = start_date.replace(' ', 'T')
        query += ' AND tr.start_time >= ?'
        params.append(start_date)
    if end_date:
        # 确保使用ISO格式时间
        if ' ' in end_date:  # 处理YYYY-MM-DD HH:MM:SS格式
            end_date = end_date.replace(' ', 'T')
        query += ' AND tr.start_time <= ?'
        params.append(end_date)
    
    query += ' GROUP BY p.id, p.name, p.color'
    
    records = db.execute(query, params).fetchall()
    
    stats = []
    for record in records:
        stats.append({
            'project_name': record['name'] or '未分配',
            'project_color': record['color'] or '#000000',
            'total_hours': round((record['total_minutes'] or 0) / 60, 2)
        })
    
    return jsonify(stats), 200

@bp.route('/shift', methods=['GET'])
def get_shift_stats():
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    query = '''SELECT shift_type, SUM(duration) as total_minutes 
              FROM time_records 
              WHERE user_id = ? AND is_leave = 0 '''
    params = [user_id]
    
    if start_date:
        # 确保使用ISO格式时间
        if ' ' in start_date:  # 处理YYYY-MM-DD HH:MM:SS格式
            start_date = start_date.replace(' ', 'T')
        query += ' AND start_time >= ?'
        params.append(start_date)
    if end_date:
        # 确保使用ISO格式时间
        if ' ' in end_date:  # 处理YYYY-MM-DD HH:MM:SS格式
            end_date = end_date.replace(' ', 'T')
        query += ' AND start_time <= ?'
        params.append(end_date)
    
    query += ' GROUP BY shift_type'
    
    records = db.execute(query, params).fetchall()
    
    stats = {
        '白班': 0,
        '夜班': 0
    }
    
    for record in records:
        shift_type = record['shift_type'] or '白班'
        hours = round((record['total_minutes'] or 0) / 60, 2)
        stats[shift_type] = hours
    
    return jsonify(stats), 200

@bp.route('/trend', methods=['GET'])
def get_trend_stats():
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    # 确保使用ISO格式时间
    if ' ' in start_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        start_date = start_date.replace(' ', 'T')
    if ' ' in end_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        end_date = end_date.replace(' ', 'T')
    
    db = get_db()
    query = '''SELECT DATE(start_time) as date, SUM(duration) as total_minutes 
              FROM time_records 
              WHERE user_id = ? AND is_leave = 0 AND start_time >= ? AND start_time <= ? 
              GROUP BY DATE(start_time) 
              ORDER BY date ASC'''
    params = [user_id, start_date, end_date]
    
    records = db.execute(query, params).fetchall()
    
    stats = []
    for record in records:
        stats.append({
            'date': record['date'],
            'hours': round((record['total_minutes'] or 0) / 60, 2)
        })
    
    return jsonify(stats), 200

@bp.route('/attendance', methods=['GET'])
def get_attendance_stats():
    """获取出勤率统计"""
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    # 确保使用ISO格式时间
    if ' ' in start_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        start_date = start_date.replace(' ', 'T')
    if ' ' in end_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        end_date = end_date.replace(' ', 'T')
    
    db = get_db()
    
    # 获取总天数（工作日）
    total_days_query = '''SELECT COUNT(DISTINCT DATE(start_time)) as total_days 
                        FROM time_records 
                        WHERE user_id = ? AND start_time >= ? AND start_time <= ?'''
    total_days_result = db.execute(total_days_query, [user_id, start_date, end_date]).fetchone()
    total_days = total_days_result['total_days'] or 0
    
    # 获取出勤天数
    attendance_days_query = '''SELECT COUNT(DISTINCT DATE(start_time)) as attendance_days 
                            FROM time_records 
                            WHERE user_id = ? AND is_leave = 0 AND start_time >= ? AND start_time <= ?'''
    attendance_days_result = db.execute(attendance_days_query, [user_id, start_date, end_date]).fetchone()
    attendance_days = attendance_days_result['attendance_days'] or 0
    
    # 计算出勤率
    attendance_rate = round((attendance_days / total_days) * 100, 2) if total_days > 0 else 0
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'total_days': total_days,
        'attendance_days': attendance_days,
        'attendance_rate': attendance_rate
    }), 200

@bp.route('/overtime', methods=['GET'])
def get_overtime_stats():
    """获取加班情况分析"""
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    standard_hours = float(request.args.get('standard_hours', 8))  # 标准工时，默认8小时/天
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    # 确保使用ISO格式时间
    if ' ' in start_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        start_date = start_date.replace(' ', 'T')
    if ' ' in end_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        end_date = end_date.replace(' ', 'T')
    
    db = get_db()
    
    # 获取每天的工时
    daily_hours_query = '''SELECT DATE(start_time) as date, SUM(duration) as total_minutes 
                        FROM time_records 
                        WHERE user_id = ? AND is_leave = 0 AND start_time >= ? AND start_time <= ? 
                        GROUP BY DATE(start_time)'''
    daily_hours_result = db.execute(daily_hours_query, [user_id, start_date, end_date]).fetchall()
    
    # 计算加班情况
    total_overtime_hours = 0
    overtime_days = 0
    max_overtime_hours = 0
    
    for day in daily_hours_result:
        hours = (day['total_minutes'] or 0) / 60
        if hours > standard_hours:
            overtime = hours - standard_hours
            total_overtime_hours += overtime
            overtime_days += 1
            if overtime > max_overtime_hours:
                max_overtime_hours = overtime
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'standard_hours_per_day': standard_hours,
        'total_overtime_hours': round(total_overtime_hours, 2),
        'overtime_days': overtime_days,
        'max_overtime_hours': round(max_overtime_hours, 2),
        'average_overtime_hours': round(total_overtime_hours / overtime_days, 2) if overtime_days > 0 else 0
    }), 200

@bp.route('/distribution', methods=['GET'])
def get_hours_distribution():
    """获取工时分布分析"""
    user_id = request.args.get('user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    # 确保使用ISO格式时间
    if ' ' in start_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        start_date = start_date.replace(' ', 'T')
    if ' ' in end_date:  # 处理YYYY-MM-DD HH:MM:SS格式
        end_date = end_date.replace(' ', 'T')
    
    db = get_db()
    
    # 获取工时分布（按小时段）
    distribution_query = '''SELECT strftime('%H', start_time) as hour, COUNT(*) as count, SUM(duration) as total_minutes 
                        FROM time_records 
                        WHERE user_id = ? AND is_leave = 0 AND start_time >= ? AND start_time <= ? 
                        GROUP BY strftime('%H', start_time) 
                        ORDER BY hour ASC'''
    distribution_result = db.execute(distribution_query, [user_id, start_date, end_date]).fetchall()
    
    # 准备分布数据
    distribution = []
    for hour in range(24):
        hour_str = f'{hour:02d}'
        hour_data = next((item for item in distribution_result if item['hour'] == hour_str), None)
        if hour_data:
            distribution.append({
                'hour': hour_str,
                'count': hour_data['count'],
                'hours': round((hour_data['total_minutes'] or 0) / 60, 2)
            })
        else:
            distribution.append({
                'hour': hour_str,
                'count': 0,
                'hours': 0
            })
    
    return jsonify({
        'start_date': start_date,
        'end_date': end_date,
        'distribution': distribution
    }), 200

@bp.route('/comparison', methods=['GET'])
def get_comparison_stats():
    """获取对比分析（与上月/上周对比）"""
    user_id = request.args.get('user_id')
    period = request.args.get('period', 'month')  # month 或 week
    current_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    current = datetime.strptime(current_date, '%Y-%m-%d')
    
    if period == 'month':
        # 计算当前月份和上一个月份
        current_month = current.strftime('%Y-%m')
        if current.month == 1:
            previous_month = f'{current.year-1}-12'
        else:
            previous_month = f'{current.year}-{current.month-1:02d}'
        
        # 获取当前月份的统计数据
        current_stats = get_monthly_stats_internal(db, user_id, current_month)
        # 获取上一个月份的统计数据
        previous_stats = get_monthly_stats_internal(db, user_id, previous_month)
        
        return jsonify({
            'period': 'month',
            'current': {
                'period': current_month,
                'stats': current_stats
            },
            'previous': {
                'period': previous_month,
                'stats': previous_stats
            },
            'comparison': {
                'total_hours_change': round(current_stats['total_hours'] - previous_stats['total_hours'], 2),
                'total_hours_change_rate': round(((current_stats['total_hours'] - previous_stats['total_hours']) / previous_stats['total_hours']) * 100, 2) if previous_stats['total_hours'] > 0 else 0,
                'leave_hours_change': round(current_stats['leave_hours'] - previous_stats['leave_hours'], 2),
                'night_shifts_change': current_stats['night_shifts'] - previous_stats['night_shifts']
            }
        }), 200
    else:  # week
        # 计算当前周和上一周
        current_week = current.isocalendar()[1]
        current_year = current.year
        
        if current_week == 1:
            previous_week = 52
            previous_year = current_year - 1
        else:
            previous_week = current_week - 1
            previous_year = current_year
        
        # 获取当前周的统计数据
        current_stats = get_weekly_stats_internal(db, user_id, current_year, current_week)
        # 获取上一周的统计数据
        previous_stats = get_weekly_stats_internal(db, user_id, previous_year, previous_week)
        
        return jsonify({
            'period': 'week',
            'current': {
                'period': f'{current_year}-W{current_week:02d}',
                'stats': current_stats
            },
            'previous': {
                'period': f'{previous_year}-W{previous_week:02d}',
                'stats': previous_stats
            },
            'comparison': {
                'total_hours_change': round(current_stats['total_hours'] - previous_stats['total_hours'], 2),
                'total_hours_change_rate': round(((current_stats['total_hours'] - previous_stats['total_hours']) / previous_stats['total_hours']) * 100, 2) if previous_stats['total_hours'] > 0 else 0,
                'leave_hours_change': round(current_stats['leave_hours'] - previous_stats['leave_hours'], 2),
                'night_shifts_change': current_stats['night_shifts'] - previous_stats['night_shifts']
            }
        }), 200

# 内部辅助函数
def get_monthly_stats_internal(db, user_id, month):
    """获取月份统计数据的内部函数"""
    # 计算月的开始和结束时间
    start_date = f'{month}-01 00:00:00'
    if month.endswith('12'):
        next_month = f'{int(month[:4])+1}-01'
    else:
        next_month = f'{month[:4]}-{int(month[5:7])+1:02d}'
    end_date = f'{next_month}-01 00:00:00'
    
    # 获取本月工时记录
    records = db.execute(
        '''SELECT SUM(duration) as total_minutes, SUM(CASE WHEN is_leave THEN duration ELSE 0 END) as leave_minutes,
        COUNT(CASE WHEN shift_type = '夜班' AND NOT is_leave THEN 1 END) as night_shifts
        FROM time_records 
        WHERE user_id = ? AND start_time >= ? AND start_time < ?''',
        (user_id, start_date, end_date)
    ).fetchone()
    
    total_hours = (records['total_minutes'] or 0) / 60
    leave_hours = (records['leave_minutes'] or 0) / 60
    night_shifts = records['night_shifts'] or 0
    
    return {
        'total_hours': round(total_hours, 2),
        'leave_hours': round(leave_hours, 2),
        'night_shifts': night_shifts
    }

def get_weekly_stats_internal(db, user_id, year, week):
    """获取周统计数据的内部函数"""
    # 计算周的开始和结束时间
    start_date = datetime.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=6)
    
    start_str = start_date.strftime('%Y-%m-%d 00:00:00')
    end_str = end_date.strftime('%Y-%m-%d 23:59:59')
    
    # 获取本周工时记录
    records = db.execute(
        '''SELECT SUM(duration) as total_minutes, SUM(CASE WHEN is_leave THEN duration ELSE 0 END) as leave_minutes,
        COUNT(CASE WHEN shift_type = '夜班' AND NOT is_leave THEN 1 END) as night_shifts
        FROM time_records 
        WHERE user_id = ? AND start_time BETWEEN ? AND ?''',
        (user_id, start_str, end_str)
    ).fetchone()
    
    total_hours = (records['total_minutes'] or 0) / 60
    leave_hours = (records['leave_minutes'] or 0) / 60
    night_shifts = records['night_shifts'] or 0
    
    return {
        'total_hours': round(total_hours, 2),
        'leave_hours': round(leave_hours, 2),
        'night_shifts': night_shifts
    }