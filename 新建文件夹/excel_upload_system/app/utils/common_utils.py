import os
import pandas as pd
import re
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def _read_excel_in_chunks(filepath, chunk_size, excel_options):
    """内部函数：分批读取Excel文件"""
    df = pd.read_excel(filepath, **excel_options)
    logger.info(f"Excel文件读取成功，形状: {df.shape}, 列名: {list(df.columns)}")
    
    # 手动分批，优化内存使用
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i+chunk_size].copy()

def _read_csv_in_chunks(filepath, chunk_size, encoding, csv_options):
    """内部函数：分批读取CSV文件"""
    chunks = pd.read_csv(
        filepath, 
        encoding=encoding, 
        engine='python',
        chunksize=chunk_size,
        **csv_options
    )
    logger.info(f"CSV文件分批读取成功({encoding}编码)")
    return chunks

def read_file_with_encoding(filepath, chunk_size=None):
    """
    读取文件并处理编码问题
    
    参数:
        filepath: 文件路径
        chunk_size: 分批读取的大小，如果为None则一次性读取
    
    返回:
        pandas DataFrame 或 生成器（如果指定了chunk_size）
    """
    logger.info(f"开始读取文件: {filepath}, 分批大小: {chunk_size}")
    
    if filepath.endswith(('.xlsx', '.xls')):
        try:
            # 优化Excel读取参数
            excel_options = {
                'engine': 'openpyxl',
                'keep_default_na': False,
                'na_values': ['', 'N/A', 'NULL', 'None']
            }
            
            if chunk_size:
                # 对于Excel文件，使用迭代器方式读取
                logger.info(f"使用分批方式读取Excel文件，分批大小: {chunk_size}")
                # Excel文件不支持chunksize，所以先一次性读取，然后手动分批
                return _read_excel_in_chunks(filepath, chunk_size, excel_options)
            else:
                # 一次性读取时使用更高效的参数
                df = pd.read_excel(filepath, **excel_options)
                logger.info(f"Excel文件读取成功，形状: {df.shape}, 列名: {list(df.columns)}")
                return df
        except Exception as e:
            logger.error(f"Excel文件读取失败: {str(e)}")
            raise e
    else:
        # 尝试检测编码并读取CSV，使用更宽容的参数处理格式不规范的CSV文件
        # 优化CSV读取参数
        csv_options = {
            'on_bad_lines': 'skip',
            'keep_default_na': False,
            'na_values': ['', 'N/A', 'NULL', 'None'],
            'low_memory': False  # 禁用低内存模式，提高读取速度
        }
        
        try:
            if chunk_size:
                logger.info(f"使用分批方式读取CSV文件，分批大小: {chunk_size}")
                # 使用chunksize参数分批读取
                return _read_csv_in_chunks(filepath, chunk_size, 'utf-8', csv_options)
            else:
                df = pd.read_csv(filepath, encoding='utf-8', engine='python', **csv_options)
                logger.info(f"CSV文件读取成功(UTF-8编码)，形状: {df.shape}, 列名: {list(df.columns)}")
                return df
        except UnicodeDecodeError:
            try:
                if chunk_size:
                    logger.info(f"使用分批方式读取CSV文件(GBK编码)，分批大小: {chunk_size}")
                    return _read_csv_in_chunks(filepath, chunk_size, 'gbk', csv_options)
                else:
                    df = pd.read_csv(filepath, encoding='gbk', engine='python', **csv_options)
                    logger.info(f"CSV文件读取成功(GBK编码)，形状: {df.shape}, 列名: {list(df.columns)}")
                    return df
            except UnicodeDecodeError:
                try:
                    if chunk_size:
                        logger.info(f"使用分批方式读取CSV文件(Latin1编码)，分批大小: {chunk_size}")
                        return _read_csv_in_chunks(filepath, chunk_size, 'latin1', csv_options)
                    else:
                        df = pd.read_csv(filepath, encoding='latin1', engine='python', **csv_options)
                        logger.info(f"CSV文件读取成功(Latin1编码)，形状: {df.shape}, 列名: {list(df.columns)}")
                        return df
                except Exception as e:
                    # 如果所有方法都失败，尝试使用更宽松的读取方式
                    logger.warning(f"标准CSV读取失败，尝试使用宽松模式: {str(e)}")
                    try:
                        if chunk_size:
                            logger.info(f"使用分批方式读取CSV文件(宽松模式)，分批大小: {chunk_size}")
                            chunks = pd.read_csv(
                                filepath, 
                                sep=None, 
                                engine='python',
                                chunksize=chunk_size,
                                **csv_options
                            )
                            logger.info(f"CSV文件分批读取成功(宽松模式)")
                            return chunks
                        else:
                            df = pd.read_csv(filepath, sep=None, engine='python', **csv_options)
                            logger.info(f"CSV文件读取成功(宽松模式)，形状: {df.shape}, 列名: {list(df.columns)}")
                            return df
                    except Exception as e2:
                        logger.error(f"所有CSV读取方法都失败: {str(e2)}")
                        raise e2

def format_workshop_name(workshop_name):
    """
    格式化车间名称，移除多余的前缀和后缀
    例如：将'B4_五一车间(正极)'转换为'五一车间'
    """
    if not workshop_name:
        return ''
    
    # 转换为字符串
    name = str(workshop_name)
    
    # 移除常见的前缀格式，如 'B4_', 'C3_', 'A1_'
    import re
    # 匹配字母数字开头，下划线结尾的前缀
    name = re.sub(r'^[A-Za-z0-9]+_', '', name)
    
    # 移除括号及其内容，如 '(正极)', '(负极)', '(正)', '(负)'
    name = re.sub(r'\([^)]*\)', '', name)
    
    # 移除多余的空格
    return name.strip()

def generate_operation_time_range(time_option, df=None, shift_type=None, custom_start=None, custom_end=None):
    """
    根据用户选择生成操作时间范围
    
    参数:
        time_option: 时间选项 (auto_extract/daily/shift/custom)
        df: 数据框，用于自动提取时使用
        shift_type: 班次类型 (day/night)
        custom_start: 自定义开始时间
        custom_end: 自定义结束时间
    
    返回:
        格式化的时间范围字符串
    """
    if time_option == 'auto_extract' and df is not None:
        # 自动从文件提取时间范围
        return extract_operation_time_range(df)
    elif time_option == 'daily':
        # 使用当天时间，从00:00:00到当前时间
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.now()
    elif time_option == 'shift':
        # 根据班次类型设置时间
        now = datetime.now()
        today = now.date()
        
        if shift_type == 'day':
            # 白班: 9:00-21:00
            start_time = datetime.combine(today, datetime.strptime('09:00', '%H:%M').time())
            end_time = datetime.combine(today, datetime.strptime('21:00', '%H:%M').time())
        else:
            # 夜班: 21:00-次日9:00
            start_time = datetime.combine(today, datetime.strptime('21:00', '%H:%M').time())
            end_time = datetime.combine(today + timedelta(days=1), datetime.strptime('09:00', '%H:%M').time())
            
        # 如果当前时间不在选定的班次范围内，调整为上一个班次
        if not (start_time <= now <= end_time):
            if shift_type == 'day':
                start_time = datetime.combine(today - timedelta(days=1), datetime.strptime('09:00', '%H:%M').time())
                end_time = datetime.combine(today - timedelta(days=1), datetime.strptime('21:00', '%H:%M').time())
            else:
                start_time = datetime.combine(today - timedelta(days=1), datetime.strptime('21:00', '%H:%M').time())
                end_time = datetime.combine(today, datetime.strptime('09:00', '%H:%M').time())
    elif time_option == 'custom' and custom_start and custom_end:
        # 使用自定义时间
        try:
            start_time = datetime.strptime(custom_start, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(custom_end, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.error(f"自定义时间格式错误: start={custom_start}, end={custom_end}")
            return "自定义时间格式错误"
    else:
        # 默认使用当天时间
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.now()
    
    # 格式化为要求的字符串格式
    formatted_time_range = f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
    logger.info(f"生成的操作时间范围: {formatted_time_range}")
    return formatted_time_range

def extract_operation_time_range(df):
    """
    从DataFrame中提取操作时间范围
    参数:
        df: pandas DataFrame对象
    返回:
        str: 格式化的时间范围字符串 "YYYY-MM-DD HH:MM:SS - YYYY-MM-DD HH:MM:SS" 或 "无相关时间记录"
    """
    import pandas as pd
    from datetime import datetime
    import re
    
    # 查找包含操作时间关键字的列
    time_columns = []
    time_keywords = ['操作时间', '时间', '日期', 'datetime', 'time', 'date']
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword.lower() in col_lower for keyword in time_keywords):
            time_columns.append(col)
    
    if not time_columns:
        logger.info("未找到时间相关列")
        return "无相关时间记录"
    
    logger.info(f"找到以下时间相关列: {time_columns}")
    
    # 收集所有有效时间
    all_times = []
    
    # 支持的时间格式列表
    time_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y%m%d',
        '%Y%m%d%H%M%S',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M'
    ]
    
    for time_col in time_columns:
        logger.debug(f"处理时间列: {time_col}")
        
        for idx, cell_value in enumerate(df[time_col]):
            if pd.isna(cell_value) or str(cell_value).strip() in ['', 'N/A', 'NULL', 'None']:
                continue
            
            # 尝试多种时间格式解析
            parsed_time = None
            cell_str = str(cell_value).strip()
            
            # 尝试自动解析
            try:
                parsed_time = pd.to_datetime(cell_str, errors='coerce')
                if pd.notna(parsed_time):
                    all_times.append(parsed_time)
                    continue
            except Exception:
                pass
            
            # 尝试特定格式解析
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(cell_str, fmt)
                    all_times.append(parsed_time)
                    break
                except ValueError:
                    continue
            
            # 如果解析失败，记录警告但继续处理
            if parsed_time is None:
                logger.warning(f"无法解析时间值 '{cell_str}' 在列 '{time_col}' 行 {idx}")
    
    if not all_times:
        logger.info("未找到有效时间数据")
        return "无相关时间记录"
    
    # 找到最早和最晚时间
    earliest_time = min(all_times)
    latest_time = max(all_times)
    
    # 格式化为要求的字符串格式
    formatted_time_range = f"{earliest_time.strftime('%Y-%m-%d %H:%M:%S')} - {latest_time.strftime('%Y-%m-%d %H:%M:%S')}"
    logger.info(f"提取的操作时间范围: {formatted_time_range}")
    
    return formatted_time_range

def clean_numeric_value(value):
    """
    清理并标准化数值，处理特殊字符和空值
    
    参数:
        value: 需要清理的值
    
    返回:
        清理后的数值或0（如果无法转换）
    """
    try:
        # 如果已经是数字类型，直接返回
        if isinstance(value, (int, float)):
            return value
        
        # 处理NaN值
        if pd.isna(value):
            return 0
        
        # 转换为字符串并清理
        value_str = str(value).strip()
        
        # 处理空值或特殊字符
        if not value_str or value_str in ['-', 'None', 'null', 'N/A', '，', '—']:
            return 0
        
        # 提取数字部分（包括小数点）
        import re
        number_match = re.search(r'\d+\.?\d*', value_str)
        if number_match:
            return float(number_match.group())
        
        return 0
    except Exception as e:
        logger.debug(f"清理数值时出错: {str(e)}, 值: {value}")
        return 0

def allowed_file(filename):
    """
    检查文件是否为允许的类型
    
    参数:
        filename: 文件名
    
    返回:
        bool: 是否为允许的类型
    """
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
