import os
import magic
import pandas as pd
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
ALLOWED_MIMETYPES = {
    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'xls': ['application/vnd.ms-excel'],
    'csv': ['text/csv', 'text/plain']
}

def validate_file_extension(filename):
    """验证文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_mimetype(file_path):
    """验证文件MIME类型"""
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        
        # 根据文件扩展名检查MIME类型
        extension = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
        
        if extension in ALLOWED_MIMETYPES:
            return mime_type in ALLOWED_MIMETYPES[extension]
        
        return False
    except Exception as e:
        logger.error(f"验证MIME类型时出错: {str(e)}")
        # 如果无法验证MIME类型，返回True以避免阻断流程
        return True

def validate_file_size(file_path, max_size_mb=50):
    """验证文件大小"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return os.path.getsize(file_path) <= max_size_bytes

def validate_dataframe(df, min_rows=1, max_rows=100000, max_columns=100):
    """验证数据框的有效性"""
    if df is None or df.empty:
        return False, "数据框为空"
    
    if len(df) < min_rows:
        return False, f"数据行太少，需要至少{min_rows}行"
    
    if len(df) > max_rows:
        return False, f"数据行太多，最多支持{max_rows}行"
    
    if len(df.columns) > max_columns:
        return False, f"数据列太多，最多支持{max_columns}列"
    
    # 检查是否所有列都为空
    if df.isnull().all().all():
        return False, "所有数据都是空值"
    
    return True, "验证通过"

def validate_column_selection(selected_columns, all_columns):
    """验证列选择是否有效"""
    if not selected_columns:
        return False, "请至少选择一列"
    
    invalid_columns = set(selected_columns) - set(all_columns)
    if invalid_columns:
        return False, f"无效的列名: {', '.join(invalid_columns)}"
    
    return True, "验证通过"

def detect_data_issues(df):
    """检测数据中的问题"""
    issues = []
    
    # 检查重复行
    duplicated_rows = df.duplicated().sum()
    if duplicated_rows > 0:
        issues.append(f"发现{duplicated_rows}行重复数据")
    
    # 检查每列的缺失值
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        missing_percent = (missing_count / len(df) * 100) if len(df) > 0 else 0
        
        if missing_percent > 50:
            issues.append(f"列'{col}'缺失值过多: {missing_percent:.1f}%")
    
    # 检查异常值（仅对数值列）
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if len(df[col].dropna()) > 0:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            
            if len(outliers) > 0:
                outlier_percent = (len(outliers) / len(df) * 100)
                if outlier_percent > 10:  # 超过10%的异常值才报告
                    issues.append(f"列'{col}'可能存在异常值: {len(outliers)}个 ({outlier_percent:.1f}%)")
    
    return issues
