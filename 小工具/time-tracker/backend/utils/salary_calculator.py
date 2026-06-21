from datetime import datetime

def get_config_value(configs, key, default):
    """从配置字典中获取值，如果不存在则返回默认值"""
    value = configs.get(key, default)
    # 尝试将字符串转换为数值类型
    if isinstance(value, str):
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except:
            return default
    return value

def calculate_base_salary(salary_level):
    """根据薪资等级计算底薪"""
    # 基准等级：E17 = 5200元
    base_level = 17
    base_salary = 5200
    
    # 提取等级字母和数字
    try:
        level_letter = salary_level[0].upper()
        level_num = int(salary_level[1:])
        
        if level_letter == 'E':
            # E级：每高一级+200元，每低一级-200元
            # 薪级最小E8
            level_num = max(8, level_num)
            return base_salary + (level_num - base_level) * 200
        elif level_letter == 'D':
            # D级：E19之后是D级，D级一级加500元
            # D1比E19多500元，D2比D1多500元，以此类推
            # 计算E19的薪资
            e19_salary = base_salary + (19 - base_level) * 200  # E19 = 5200 + (19-17)*200 = 5600
            # D级薪资计算：D1 = E19 + 500, D2 = D1 + 500, 以此类推
            d_base_salary = e19_salary + level_num * 500
            return d_base_salary
        else:
            return base_salary
    except:
        return base_salary

def calculate_seniority_bonus(hire_date):
    """计算工龄奖"""
    if not hire_date:
        return 0
    
    try:
        # 处理不同格式的日期字符串
        if isinstance(hire_date, str):
            # 如果包含时间部分，只保留日期部分
            if ' ' in hire_date:
                hire_date = hire_date.split(' ')[0]
            hire = datetime.strptime(hire_date, '%Y-%m-%d')
        else:
            hire = hire_date
        
        now = datetime.now()
        
        # 计算工龄，每年7月加一年，第一年不算，满一年后才有
        # 计算实际工作年数
        seniority = now.year - hire.year
        
        # 检查是否已经过了今年的调薪时间（7月）
        if now.month < 7:
            # 今年还没到调薪时间，减去1年
            seniority -= 1
        else:
            # 今年已经过了调薪时间，检查是否满周年
            if hire.month > now.month or (hire.month == now.month and hire.day > now.day):
                # 还没满周年，减去1年
                seniority -= 1
        
        # 直接使用计算出的工龄，不再减去第一年
        # 确保工龄不为负数
        seniority = max(0, seniority)
        
        # 一年80元
        return max(0, seniority * 80)
    except Exception as e:
        print(f"计算工龄奖出错: {e}, hire_date: {hire_date}, 类型: {type(hire_date)}")
        return 0

def calculate_overtime_pay(total_hours, overtime_rate=19.65, standard_hours=167):
    """计算加班费"""
    if total_hours > standard_hours:
        return (total_hours - standard_hours) * overtime_rate
    return 0

def calculate_attendance_bonus(leave_hours, max_leave_hours=8, attendance_bonus_amount=400):
    """计算满勤奖"""
    # 如果请假超过指定小时数，满勤奖为0
    if leave_hours > max_leave_hours:
        return 0
    return attendance_bonus_amount

def calculate_night_shift_allowance(night_shifts, allowance_per_day=10):
    """计算夜班补贴"""
    return night_shifts * allowance_per_day

def calculate_tax(pre_tax_salary, tax_threshold=5000):
    """计算税费"""
    # 简化的个人所得税计算
    if pre_tax_salary <= tax_threshold:
        return 0
    
    taxable = pre_tax_salary - tax_threshold
    if taxable <= 3000:
        return taxable * 0.03
    elif taxable <= 12000:
        return taxable * 0.1 - 210
    elif taxable <= 25000:
        return taxable * 0.2 - 1410
    else:
        return taxable * 0.25 - 2660

def calculate_total_salary(salary_info, total_hours, configs=None):
    """计算总工资"""
    # 如果没有提供配置，使用默认值
    if configs is None:
        configs = {}
    
    # 从配置中获取参数
    overtime_rate = get_config_value(configs, 'overtime_rate', 19.65)
    standard_hours = get_config_value(configs, 'standard_hours', 167)
    attendance_bonus_amount = get_config_value(configs, 'attendance_bonus_amount', 400)
    max_leave_hours = get_config_value(configs, 'max_leave_hours', 8)
    night_shift_allowance = get_config_value(configs, 'night_shift_allowance', 10)
    tax_threshold = get_config_value(configs, 'tax_threshold', 5000)
    
    # 计算各项
    base_salary = salary_info['base_salary']
    attendance_bonus = calculate_attendance_bonus(salary_info['leave_hours'], max_leave_hours, attendance_bonus_amount)
    overtime_pay = calculate_overtime_pay(total_hours, overtime_rate, standard_hours)
    night_shift_allowance = calculate_night_shift_allowance(
        salary_info['total_night_shifts'], 
        night_shift_allowance
    )
    seniority_bonus = salary_info['seniority_bonus'] or 0
    
    # 税前工资
    pre_tax = base_salary + attendance_bonus + overtime_pay + night_shift_allowance + seniority_bonus
    
    # 扣除项
    utility_fee = salary_info['utility_fee'] or 0
    insurance = salary_info['insurance'] or 0
    tax = calculate_tax(pre_tax - insurance, tax_threshold)
    
    # 实发工资
    net_salary = pre_tax - utility_fee - insurance - tax
    
    return {
        'base_salary': base_salary,
        'attendance_bonus': attendance_bonus,
        'overtime_pay': overtime_pay,
        'night_shift_allowance': night_shift_allowance,
        'seniority_bonus': seniority_bonus,
        'pre_tax_salary': pre_tax,
        'utility_fee': utility_fee,
        'insurance': insurance,
        'tax': tax,
        'net_salary': net_salary
    }