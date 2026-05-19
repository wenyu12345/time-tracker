# CSV新模式识别表头识别算法文档

## 1. 算法概述

本文档详细描述了CSV新模式识别系统中的表头识别算法，该算法能够自动识别并映射CSV文件中的表头字段到系统标准字段，实现数据的标准化处理。

## 2. 核心功能

- 自动识别CSV文件中的表头字段
- 根据预定义映射规则将表头映射到标准字段
- 清理表头名称，去除多余字符和空格
- 处理未映射的字段
- 提供数据预览功能

## 3. 完整代码

### 3.1 导入模块

```python
from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import io
import json
from datetime import datetime
import re
import os
from werkzeug.utils import secure_filename
from collections import defaultdict

csv_new_pattern_bp = Blueprint('csv_new_pattern', __name__)

# 文件上传相关配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 缓存已上传的数据
uploaded_data_cache = {}
```

### 3.2 表头映射规则

```python
# 定义标准字段与可能的表头名称映射
HEADER_MAPPING = {
    '日期': ['日期', 'Date', '日期时间', '时间', 'datetime', '生产日期', 'product_date', '日期时间'],
    '班次': ['班次', 'Shift', '班', '班别', '早班', '中班', '晚班', '早', '中', '晚', 'day', 'middle', 'night'],
    '产品型号': ['产品型号', '产品', '型号', 'Product', 'Model', '物料号', 'material_id', '物料编码', 'material_code', '料号'],
    '工序名称': ['工序名称', '工序', 'Process', '工序名', '工步', 'step', '操作', 'operation', '工序号', 'process_id'],
    '良品数(kg)': ['良品数(kg)', '良品数', '良品', 'Good', 'Yield', '合格数', 'qualified', '合格量', '产量', 'output'],
    '报废数(kg)': ['报废数(kg)', '报废数', '报废', 'Waste', 'Scrap', '废品数', '不良数', 'defective', '不良量', 'reject']
}

# 定义需要进行数值处理的字段
NUMERIC_FIELDS = ['良品数(kg)', '报废数(kg)']
```

### 3.3 表头清理函数

```python
def clean_header_name(header):
    """
    清理表头名称，去除多余字符和空格
    
    Args:
        header: 原始表头名称
    
    Returns:
        清理后的表头名称
    """
    if not isinstance(header, str):
        header = str(header)
    
    # 去除首尾空格
    header = header.strip()
    
    # 去除特殊字符，只保留字母、数字、中文和常见符号
    header = re.sub(r'[\s\u3000]+', ' ', header)  # 替换所有空白字符为单个空格
    header = re.sub(r'[\u00A0\t\n\r]+', ' ', header)  # 替换不间断空格和制表符
    
    # 清理一些常见的特殊字符
    header = re.sub(r'[\(\)\[\]{}]+', '', header)  # 去除括号
    
    # 转换为小写进行匹配（仅对英文部分）
    header_lower = header.lower()
    
    return header, header_lower
```

### 3.4 表头识别和映射函数

```python
def identify_and_map_headers(df):
    """
    识别并映射表头字段
    
    Args:
        df: 包含原始数据的DataFrame
    
    Returns:
        tuple: (field_mapping, unmapped_headers)
            field_mapping: 字段映射字典 {原始表头: 标准字段}
            unmapped_headers: 未映射的表头列表
    """
    # 获取原始表头
    original_headers = df.columns.tolist()
    field_mapping = {}
    used_standard_fields = set()
    unmapped_headers = []
    
    # 首先进行精确匹配
    for header in original_headers:
        clean_head, clean_head_lower = clean_header_name(header)
        
        # 检查精确匹配
        for standard_field, possible_names in HEADER_MAPPING.items():
            if standard_field == clean_head or clean_head_lower == standard_field.lower():
                field_mapping[header] = standard_field
                used_standard_fields.add(standard_field)
                break
            
            # 检查可能的名称列表中的精确匹配
            for possible_name in possible_names:
                if possible_name == clean_head or clean_head_lower == possible_name.lower():
                    field_mapping[header] = standard_field
                    used_standard_fields.add(standard_field)
                    break
            else:
                continue  # 内循环未break，继续检查下一个标准字段
            break  # 找到匹配，跳出外循环
    
    # 然后进行模糊匹配（仅对未匹配的表头）
    for header in original_headers:
        if header in field_mapping:
            continue  # 已经匹配过的跳过
        
        clean_head, clean_head_lower = clean_header_name(header)
        
        # 模糊匹配：检查是否包含关键词
        matched = False
        for standard_field, possible_names in HEADER_MAPPING.items():
            if standard_field in used_standard_fields:
                continue  # 已经被使用的标准字段跳过
            
            # 检查标准字段名是否在清理后的表头中
            if standard_field.lower() in clean_head_lower:
                field_mapping[header] = standard_field
                used_standard_fields.add(standard_field)
                matched = True
                break
            
            # 检查可能的名称是否在清理后的表头中
            for possible_name in possible_names:
                if possible_name.lower() in clean_head_lower:
                    field_mapping[header] = standard_field
                    used_standard_fields.add(standard_field)
                    matched = True
                    break
            if matched:
                break
        
        if not matched:
            unmapped_headers.append(header)
    
    return field_mapping, unmapped_headers
```

### 3.5 数据转换函数

```python
def transform_dataframe(df, field_mapping):
    """
    根据字段映射转换DataFrame
    
    Args:
        df: 原始DataFrame
        field_mapping: 字段映射字典
    
    Returns:
        tuple: (transformed_df, conversion_errors)
            transformed_df: 转换后的DataFrame
            conversion_errors: 转换过程中的错误信息
    """
    # 创建映射后的DataFrame
    transformed_df = pd.DataFrame()
    conversion_errors = []
    
    # 重命名列
    renamed_df = df.rename(columns=field_mapping)
    
    # 处理每个标准字段
    for standard_field in HEADER_MAPPING.keys():
        if standard_field in renamed_df.columns:
            # 日期字段处理
            if standard_field == '日期':
                try:
                    # 尝试多种日期格式转换
                    date_series = renamed_df[standard_field].apply(format_date)
                    transformed_df[standard_field] = date_series
                    
                    # 记录转换错误
                    error_count = date_series.isna().sum()
                    if error_count > 0:
                        conversion_errors.append({
                            'field': standard_field,
                            'error_type': 'date_conversion',
                            'count': error_count,
                            'message': f'无法转换 {error_count} 个日期值'
                        })
                except Exception as e:
                    conversion_errors.append({
                        'field': standard_field,
                        'error_type': 'date_processing',
                        'message': f'日期处理错误: {str(e)}'
                    })
                    transformed_df[standard_field] = renamed_df[standard_field]
            
            # 数值字段处理
            elif standard_field in NUMERIC_FIELDS:
                try:
                    # 尝试转换为数值类型
                    num_series = pd.to_numeric(renamed_df[standard_field], errors='coerce')
                    transformed_df[standard_field] = num_series
                    
                    # 记录转换错误
                    error_count = num_series.isna().sum()
                    if error_count > 0:
                        conversion_errors.append({
                            'field': standard_field,
                            'error_type': 'numeric_conversion',
                            'count': error_count,
                            'message': f'无法转换 {error_count} 个数值'
                        })
                except Exception as e:
                    conversion_errors.append({
                        'field': standard_field,
                        'error_type': 'numeric_processing',
                        'message': f'数值处理错误: {str(e)}'
                    })
                    transformed_df[standard_field] = renamed_df[standard_field]
            
            # 其他字段直接复制
            else:
                transformed_df[standard_field] = renamed_df[standard_field]
    
    # 添加未映射的列
    for header in df.columns:
        if header not in field_mapping:
            transformed_df[header] = df[header]
    
    return transformed_df, conversion_errors

def format_date(date_value):
    """
    格式化日期值，支持多种日期格式
    
    Args:
        date_value: 需要格式化的日期值
    
    Returns:
        格式化后的日期字符串，无法转换则返回None
    """
    if pd.isna(date_value):
        return None
    
    # 如果已经是日期时间对象
    if isinstance(date_value, (datetime, pd.Timestamp)):
        return date_value.strftime('%Y-%m-%d %H:%M:%S')
    
    # 转换为字符串
    date_str = str(date_value)
    date_str = date_str.strip()
    
    # 尝试多种常见的日期格式
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d',
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M',
        '%d-%m-%Y',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
        '%m-%d-%Y %H:%M:%S',
        '%m-%d-%Y %H:%M',
        '%m-%d-%Y',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',
        '%Y年%m月%d日 %H:%M:%S',
        '%Y年%m月%d日 %H:%M',
        '%Y年%m月%d日',
    ]
    
    # 尝试去除时间部分的特殊字符
    if 'T' in date_str:
        date_str = date_str.replace('T', ' ')
    
    # 尝试解析日期
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    
    # 尝试处理Excel日期序列号
    try:
        num_date = float(date_str)
        if 10000 <= num_date <= 50000:  # 典型的Excel日期范围
            dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(num_date) - 2)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        pass
    
    # 尝试只提取年月日数字
    digits = re.findall(r'\d+', date_str)
    if len(digits) >= 3:
        # 尝试组合年月日
        try:
            # 常见的数字组合模式
            if len(digits[0]) == 4:  # 年开头
                year = int(digits[0])
                month = int(digits[1])
                day = int(digits[2])
            else:
                # 尝试日开头
                day = int(digits[0])
                month = int(digits[1])
                year = int(digits[2])
                # 处理年份为两位数的情况
                if year < 100:
                    year += 2000
            
            # 验证日期有效性
            if 1 <= month <= 12 and 1 <= day <= 31:
                dt = datetime(year, month, day)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, IndexError):
            pass
    
    return None  # 无法识别的日期格式
```

### 3.6 文件上传和处理路由

```python
@csv_new_pattern_bp.route('/upload', methods=['POST'])
def upload_csv():
    """
    上传CSV文件并进行表头识别
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件上传'}), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        # 检查文件类型
        if not file.filename.endswith(('.csv', '.txt')):
            return jsonify({'success': False, 'error': '不支持的文件类型，请上传CSV或TXT文件'}), 400
        
        # 生成唯一的文件ID
        file_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
        
        # 读取CSV文件
        file_content = file.read()
        
        # 尝试不同的编码格式
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
        df = None
        encoding_used = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            return jsonify({'success': False, 'error': '无法解析文件，请检查文件编码'}), 400
        
        # 检查DataFrame是否为空
        if df.empty:
            return jsonify({'success': False, 'error': '文件内容为空或无法识别'}), 400
        
        # 识别和映射表头
        field_mapping, unmapped_headers = identify_and_map_headers(df)
        
        # 转换数据
        transformed_df, conversion_errors = transform_dataframe(df, field_mapping)
        
        # 准备数据预览（限制前10行）
        preview_data = transformed_df.head(10).to_dict(orient='records')
        
        # 将处理后的数据存入缓存
        uploaded_data_cache[file_id] = {
            'original_df': df,
            'transformed_df': transformed_df,
            'field_mapping': field_mapping,
            'upload_time': datetime.now()
        }
        
        # 清理缓存
        cleanup_cache()
        
        # 准备返回数据
        result = {
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'encoding': encoding_used,
            'total_rows': len(df),
            'field_mapping': field_mapping,
            'unmapped_headers': unmapped_headers,
            'preview_data': preview_data,
            'conversion_errors': conversion_errors
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

## 4. 算法工作流程

### 4.1 表头识别流程

1. **原始表头获取**：从上传的CSV文件中读取原始表头
2. **表头清理**：对每个表头进行清理，去除多余字符和空格
3. **精确匹配**：首先尝试标准字段名和可能名称的精确匹配
4. **模糊匹配**：对未匹配的表头，尝试关键词模糊匹配
5. **未映射处理**：记录无法映射的表头

### 4.2 数据转换流程

1. **列重命名**：根据字段映射重命名DataFrame的列
2. **日期字段处理**：尝试多种日期格式解析日期字段
3. **数值字段处理**：将数值相关字段转换为数值类型
4. **错误记录**：记录转换过程中的错误信息
5. **数据预览**：生成数据预览用于前端展示

## 5. 技术要点

1. **多编码支持**：自动尝试多种常见编码格式解析CSV文件
2. **智能日期解析**：支持多种日期格式和Excel日期序列号
3. **多级匹配策略**：采用精确匹配和模糊匹配相结合的策略提高识别准确率
4. **错误处理**：完善的错误捕获和记录机制
5. **内存缓存**：使用内存缓存提高处理效率

## 6. 性能优化

1. **缓存管理**：自动清理过期缓存，避免内存溢出
2. **多级匹配**：先进行精确匹配，再进行模糊匹配，提高效率
3. **数据预览限制**：只返回前10行数据用于预览
4. **错误统计**：提供详细的转换错误统计，便于问题排查

## 7. 使用说明

1. 调用`/upload`接口上传CSV文件
2. 系统自动进行表头识别和数据转换
3. 返回识别结果，包括字段映射、未映射字段和数据预览
4. 可根据返回的`file_id`进行后续操作

## 8. 扩展建议

1. 增加自定义映射规则功能，允许用户手动调整映射关系
2. 实现表头模板保存和加载功能
3. 优化大数据量CSV文件的处理性能
4. 支持更多的日期格式和特殊数据格式处理
5. 添加机器学习模型提高表头识别的准确率