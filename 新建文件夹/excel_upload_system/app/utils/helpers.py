import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_unique_filename(original_filename):
    """生成唯一的文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name, extension = os.path.splitext(original_filename)
    return f"{base_name}_{timestamp}{extension}"

def detect_file_encoding(file_path, sample_size=10000):
    """检测文件编码"""
    encodings_to_try = ['utf-8', 'gbk', 'latin1', 'utf-16']
    
    with open(file_path, 'rb') as f:
        sample = f.read(sample_size)
    
    for encoding in encodings_to_try:
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    
    # 如果都失败，返回默认编码
    return 'utf-8'

def clean_dataframe(df):
    """清理数据框"""
    # 移除完全为空的行和列
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # 清理列名
    df.columns = [str(col).strip() for col in df.columns]
    
    # 移除重复的列名
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    
    # 转换数据类型
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            try:
                # 尝试转换为日期时间
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except:
                pass
            
            try:
                # 尝试转换为数值
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
    
    return df

def get_memory_usage(df):
    """获取数据框的内存使用情况"""
    return df.memory_usage(deep=True).sum() / 1024**2  # 返回MB

def optimize_dataframe_memory(df):
    """优化数据框的内存使用"""
    original_memory = get_memory_usage(df)
    
    # 优化数值类型
    for col in df.select_dtypes(include=['int', 'float']).columns:
        col_min = df[col].min()
        col_max = df[col].max()
        
        # 尝试转换整数类型
        if pd.api.types.is_integer_dtype(df[col]):
            if col_min >= 0:
                if col_max < 2**8:
                    df[col] = df[col].astype('uint8')
                elif col_max < 2**16:
                    df[col] = df[col].astype('uint16')
                elif col_max < 2**32:
                    df[col] = df[col].astype('uint32')
            else:
                if col_min >= -2**7 and col_max < 2**7:
                    df[col] = df[col].astype('int8')
                elif col_min >= -2**15 and col_max < 2**15:
                    df[col] = df[col].astype('int16')
                elif col_min >= -2**31 and col_max < 2**31:
                    df[col] = df[col].astype('int32')
        # 优化浮点类型
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype('float32')
    
    # 优化对象类型
    for col in df.select_dtypes(include=['object']).columns:
        # 如果唯一值少于50%，转换为分类类型
        if df[col].nunique() / len(df) < 0.5:
            df[col] = df[col].astype('category')
    
    optimized_memory = get_memory_usage(df)
    logger.info(f"数据框内存优化: {original_memory:.2f}MB → {optimized_memory:.2f}MB (减少{((original_memory - optimized_memory) / original_memory * 100):.2f}%)")
    
    return df

def generate_data_quality_report(df):
    """生成数据质量报告"""
    report = []
    
    for col in df.columns:
        col_data = df[col]
        
        # 基本信息
        dtype = str(col_data.dtype)
        missing_count = col_data.isnull().sum()
        missing_percent = (missing_count / len(df) * 100) if len(df) > 0 else 0
        unique_count = col_data.nunique()
        
        # 数值列的额外信息
        if pd.api.types.is_numeric_dtype(col_data):
            mean_val = col_data.mean() if not col_data.isnull().all() else None
            std_val = col_data.std() if not col_data.isnull().all() else None
            min_val = col_data.min() if not col_data.isnull().all() else None
            max_val = col_data.max() if not col_data.isnull().all() else None
        else:
            mean_val = std_val = min_val = max_val = None
        
        report.append({
            '列名': col,
            '数据类型': dtype,
            '缺失值数量': missing_count,
            '缺失值百分比': round(missing_percent, 2),
            '唯一值数量': unique_count,
            '均值': round(mean_val, 2) if mean_val is not None else None,
            '标准差': round(std_val, 2) if std_val is not None else None,
            '最小值': min_val,
            '最大值': max_val
        })
    
    return pd.DataFrame(report)
