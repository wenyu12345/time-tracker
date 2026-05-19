from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.utils import secure_filename
import os
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta
from app.utils.utilities import convert_numpy_types, safe_json_serialize
from app.utils.csv_double_header_processor import CSVDoubleHeaderProcessor
from app.utils.temp_file_manager import temp_file_manager
from app.utils.async_task_manager import async_task_manager
from app.utils.common_utils import (
    read_file_with_encoding,
    format_workshop_name,
    generate_operation_time_range,
    extract_operation_time_range,
    clean_numeric_value,
    allowed_file
)
# 设置matplotlib使用非交互式后端，避免在服务器环境中崩溃
import matplotlib
matplotlib.use('Agg')  # 使用Agg后端，适合服务器环境
import matplotlib.pyplot as plt
import seaborn as sns
# 配置中文字体，确保正确显示中文
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
from io import BytesIO
import base64
import logging
import json
import shutil

from app import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('excel_upload')
logger.setLevel(logging.INFO)  # 设置为INFO以减少日志输出，提高性能

# 默认的型号映射规则
DEFAULT_MAPPINGS = {
    "466": "A732正极片",
    "505": "A730负极片",
    "467": "A730正极片",
    "Y46": "D640负极片",
    "A47": "D652正极片",
    "A44": "D640正极片",
    "Y49": "D652正极片",
    "477": "A732负极片"
}

# 映射规则文件路径
MAPPINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'model_mappings.json')

# 确保数据目录存在
def ensure_data_dir():
    data_dir = os.path.dirname(MAPPINGS_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

# 加载映射规则
def load_mappings():
    ensure_data_dir()
    if not os.path.exists(MAPPINGS_FILE):
        # 如果文件不存在，创建默认映射文件
        with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_MAPPINGS, f, ensure_ascii=False, indent=2)
        return DEFAULT_MAPPINGS
    
    try:
        with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载映射规则失败: {str(e)}")
        return DEFAULT_MAPPINGS

# 保存映射规则
def save_mappings(mappings):
    ensure_data_dir()
    try:
        with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存映射规则失败: {str(e)}")
        return False



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/csv_double_header')
def csv_double_header():
    """CSV双层表头处理页面"""
    return render_template('csv_double_header.html')

@app.route('/process_csv_double_header', methods=['POST'])
def process_csv_double_header():
    """处理CSV双层表头文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未找到文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '不支持的文件格式，请上传CSV文件'})
        
        # 读取文件内容
        file_content = file.read()
        
        # 处理文件
        processor = CSVDoubleHeaderProcessor()
        result = processor.process_file(file_content)
        
        if result['success']:
            # 保存处理后的数据到会话中
            session['processed_data'] = json.dumps(result['data'].to_dict('records'), ensure_ascii=False)
            session['filter_options'] = json.dumps(result['filter_options'], ensure_ascii=False)
            session['columns'] = json.dumps(result['columns'], ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'columns': result['columns'],
                'preview': result['preview'],
                'filter_options': result['filter_options'],
                'field_mapping': result['field_mapping'],
                'message': '文件处理成功'
            })
        else:
            return jsonify(result)
    
    except Exception as e:
        logger.error(f"处理CSV双层表头文件失败: {str(e)}")
        return jsonify({'success': False, 'error': f'处理失败: {str(e)}'})

@app.route('/filter_and_sum', methods=['POST'])
def filter_and_sum():
    """多条件筛选和求和"""
    try:
        # 获取筛选条件
        data = request.json
        filters = data.get('filters', {})
        sum_fields = data.get('sum_fields', ['良品数(kg)', '报废数(kg)'])
        
        # 从会话中获取处理后的数据
        if 'processed_data' not in session:
            return jsonify({'success': False, 'error': '没有已处理的数据，请先上传文件'})
        
        # 还原数据
        processed_data = json.loads(session['processed_data'])
        df = pd.DataFrame(processed_data)
        
        # 执行筛选和求和
        processor = CSVDoubleHeaderProcessor()
        result = processor.filter_and_sum(df, filters, sum_fields)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"筛选求和失败: {str(e)}")
        return jsonify({'success': False, 'error': f'筛选求和失败: {str(e)}'})



@app.route('/summary_table')
def summary_table():
    """分类汇总表格页面"""
    return render_template('summary_table.html')

@app.route('/summary_table_v2')
def summary_table_v2():
    """表2格式汇总页面"""
    return render_template('summary_table_v2.html')

@app.route('/manage_model_mapping')
def manage_model_mapping():
    mappings = load_mappings()
    return render_template('manage_model_mapping.html', mappings=mappings)



@app.route('/save_model_mapping', methods=['POST'])
def save_model_mapping():
    mappings = load_mappings()
    
    # 处理删除操作
    deleted_prefixes = request.form.get('deletedPrefixes', '').split(',')
    for prefix in deleted_prefixes:
        if prefix and prefix in mappings:
            del mappings[prefix]
    
    # 处理添加操作
    new_prefix = request.form.get('newPrefix', '').strip()
    new_model = request.form.get('newModel', '').strip()
    
    if new_prefix and new_model:
        mappings[new_prefix] = new_model
    
    # 保存更新后的映射规则
    if save_mappings(mappings):
        flash('映射规则已成功保存', 'success')
    else:
        flash('保存映射规则失败，请稍后重试', 'danger')
    
    return redirect(url_for('manage_model_mapping'))

@app.route('/toggle_custom_mapping', methods=['POST'])
def toggle_custom_mapping():
    """切换自定义映射功能的启用状态"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        # 保存状态到session
        session['custom_mapping_enabled'] = enabled
        
        return jsonify({'success': True, 'enabled': enabled})
    except Exception as e:
        logger.error(f"切换自定义映射状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 文件管理路由 - 查看上传的文件列表
@app.route('/file_manager')
def file_manager():
    """文件管理页面 - 显示所有上传的文件"""
    try:
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uploads')
        files = []
        
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                if filename.endswith(('.xlsx', '.xls', '.csv')):
                    file_path = os.path.join(uploads_dir, filename)
                    stat = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'display_name': filename  # 用于重命名的显示名称
                    })
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return render_template('file_manager.html', files=files)
    except Exception as e:
        logger.error(f"文件管理页面加载失败: {str(e)}")
        flash(f'文件管理页面加载失败: {str(e)}', 'danger')
        return redirect(url_for('index'))

# 文件重命名路由
@app.route('/rename_file', methods=['POST'])
def rename_file():
    """重命名上传的文件"""
    try:
        old_name = request.form.get('old_name', '').strip()
        new_name = request.form.get('new_name', '').strip()
        
        if not old_name or not new_name:
            return jsonify({'success': False, 'error': '文件名不能为空'})
        
        # 验证新文件名
        if not new_name.endswith(('.xlsx', '.xls', '.csv')):
            return jsonify({'success': False, 'error': '文件扩展名必须是 .xlsx, .xls 或 .csv'})
        
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uploads')
        old_path = os.path.join(uploads_dir, old_name)
        new_path = os.path.join(uploads_dir, new_name)
        
        if not os.path.exists(old_path):
            return jsonify({'success': False, 'error': '原文件不存在'})
        
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': '新文件名已存在'})
        
        # 执行重命名
        os.rename(old_path, new_path)
        logger.info(f"文件重命名成功: {old_name} -> {new_name}")
        
        return jsonify({'success': True, 'message': '文件重命名成功'})
        
    except Exception as e:
        logger.error(f"文件重命名失败: {str(e)}")
        return jsonify({'success': False, 'error': f'文件重命名失败: {str(e)}'})

# 文件删除路由
@app.route('/delete_file/<filename>', methods=['DELETE'])
def delete_file(filename):
    """删除上传的文件"""
    try:
        # 安全验证文件名
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': '无效的文件名'})
        
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uploads')
        file_path = os.path.join(uploads_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'})
        
        # 删除文件
        os.remove(file_path)
        logger.info(f"文件删除成功: {filename}")
        
        return jsonify({'success': True, 'message': '文件删除成功'})
        
    except Exception as e:
        logger.error(f"文件删除失败: {str(e)}")
        return jsonify({'success': False, 'error': f'文件删除失败: {str(e)}'})

# 文件下载路由
@app.route('/download_upload/<path:filename>')
def download_upload(filename):
    """下载上传的文件"""
    try:
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uploads')
        file_path = os.path.join(uploads_dir, filename)
        
        if not os.path.exists(file_path):
            flash('文件不存在', 'danger')
            return redirect(url_for('file_manager'))
        
        # 安全验证文件名
        if '..' in filename or '/' in filename or '\\' in filename:
            flash('无效的文件名', 'danger')
            return redirect(url_for('file_manager'))
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        flash(f'文件下载失败: {str(e)}', 'danger')
        return redirect(url_for('file_manager'))

# 钉钉机器人通知接口
@app.route('/send_to_dingtalk', methods=['POST'])
def send_to_dingtalk():
    """发送通知到钉钉群，支持发送图片和表格数据"""
    logger.info("收到钉钉通知接口请求")
    
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            error_msg = "请求体为空，无法获取通知数据"
            logger.error(error_msg)
            return jsonify({"errcode": 400, "errmsg": error_msg})
        
        file_name = data.get('file_name', '未知文件名')
        operation = data.get('operation', '下载操作')
        data_count = data.get('data_count', 0)
        page_count = data.get('page_count', 0)
        image_data = data.get('image_data', None)  # 获取图片base64数据
        image_name = data.get('image_name', None)  # 获取图片名称
        table_data = data.get('table_data', None)  # 获取表格数据
        
        # 从session中获取操作时间范围
        operation_time_range = session.get('honglian_data', {}).get('operation_time_range', '无相关时间记录')
        
        logger.info(f"钉钉通知请求详情 - 文件: {file_name}, 操作: {operation}, 数据量: {data_count}, 页码: {page_count}")
        logger.debug(f"是否包含图片数据: {image_data is not None}, 是否包含表格数据: {table_data is not None}")
        
        # 导入钉钉机器人发送函数（从根目录导入）
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # 如果有表格数据，直接发送表格格式
        if table_data:
            # 确保标题包含@小艺关键词
            safe_title = f"@小艺 {file_name} - {operation}"
            logger.info(f"处理表格数据，使用安全标题: {safe_title}")
            
            try:
                from dingtalk_robot import send_table_data_to_dingtalk
                result = send_table_data_to_dingtalk(
                    table_data=table_data,
                    title=safe_title,
                    operation=operation,
                    file_name=file_name,
                    operation_time_range=operation_time_range,
                    data_count=data_count
                )
                # 详细记录结果，使用DEBUG级别
                logger.debug(f"钉钉表格数据发送结果: {result}")
                return jsonify(result)
            except ImportError as e:
                error_msg = f"导入send_table_data_to_dingtalk失败: {str(e)}"
                logger.error(error_msg)
                return jsonify({"errcode": 500, "errmsg": error_msg})
        
        # 否则发送图片或文本通知
        try:
            from dingtalk_robot import send_honglian_notification
            logger.debug("调用send_honglian_notification函数发送红莲模式通知")
            result = send_honglian_notification(
                file_name=file_name,
                operation=operation,
                data_count=data_count,
                page_count=page_count,
                image_data=image_data,
                image_name=image_name,
                operation_time_range=operation_time_range
            )
            
            logger.info(f"钉钉消息发送结果: {result}")
            return jsonify(result)
        except ImportError as e:
            error_msg = f"导入send_honglian_notification失败: {str(e)}"
            logger.error(error_msg)
            return jsonify({"errcode": 500, "errmsg": error_msg})
    except json.JSONDecodeError as e:
        error_msg = f"请求数据格式错误，无法解析JSON: {str(e)}"
        logger.error(error_msg)
        return jsonify({"errcode": 400, "errmsg": error_msg})
    except Exception as e:
        error_msg = f"发送钉钉通知失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({"errcode": 500, "errmsg": error_msg})

# 产能汇总分析钉钉发送路由













def honglian_mode_handler(file):
    """处理开红莲专用模式的文件上传"""
    try:
        # 保存上传的文件
        original_filename = file.filename
        filename = secure_filename(original_filename)
        logger.info(f"原始文件名: {original_filename}, 安全处理后: {filename}")
        
        # 检查文件名是否有效
        if not filename or filename == '':
            logger.error(f"文件名无效: 原始文件名='{original_filename}', 安全处理后='{filename}'")
            flash('文件名无效，请检查文件名是否包含特殊字符', 'error')
            return redirect('/')
        
        # 添加时间戳避免文件名冲突
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        name_without_ext, ext = os.path.splitext(filename)
        
        # 如果扩展名丢失，尝试从原始文件名获取
        if not ext and original_filename:
            original_name, original_ext = os.path.splitext(original_filename)
            if original_ext:
                ext = original_ext
                logger.info(f"从原始文件名恢复扩展名: {ext}")
        
        unique_filename = f"{name_without_ext}_{timestamp}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # 确保上传目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存文件时捕获权限错误
        try:
            file.save(filepath)
            logger.info(f"已保存上传文件: {unique_filename}, 文件大小: {os.path.getsize(filepath)} bytes")
            
            # 检查文件是否为空
            if os.path.getsize(filepath) == 0:
                logger.error(f"文件为空: {unique_filename}")
                flash('上传的文件为空，请检查文件内容', 'error')
                return redirect('/')
                
        except PermissionError:
            # 如果有权限错误，尝试使用不同的文件名
            unique_filename = f"upload_{timestamp}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            logger.warning(f"权限问题，使用备用文件名: {unique_filename}")
        except Exception as e:
            logger.error(f"保存文件时出错: {str(e)}")
            flash(f"文件保存失败: {str(e)}", 'error')
            return redirect('/')
        
        # 读取和处理文件
        try:
            df = read_file_with_encoding(filepath)
            logger.info(f"文件读取成功，形状: {df.shape}, 列名: {list(df.columns)}")
            
            # 检查数据框是否有效
            if df.empty:
                logger.warning(f"文件读取结果为空: {unique_filename}")
                flash('文件内容为空或无法读取有效数据', 'warning')
                return redirect('/')
                
            # 检查列名是否异常（可能是二进制文件被错误读取）
            if len(df.columns) == 1 and any(ord(char) < 32 or ord(char) > 126 for char in str(df.columns[0])):
                logger.error(f"文件可能被错误读取为二进制: {unique_filename}, 列名: {df.columns[0]}")
                flash('文件格式错误，请确保上传的是有效的Excel或CSV文件', 'error')
                return redirect('/')
                
        except Exception as e:
            logger.error(f"文件读取失败: {str(e)}, 文件: {unique_filename}")
            flash(f"文件读取失败，请检查文件格式: {str(e)}", 'error')
            return redirect('/')
        
        # 获取时间设置参数
        time_option = request.form.get('time_option', 'auto_extract')
        shift_type = request.form.get('shift_type', 'day')
        custom_start = request.form.get('custom_start', '')
        custom_end = request.form.get('custom_end', '')
        
        logger.info(f"时间选项: {time_option}, 班次类型: {shift_type}, 自定义开始: {custom_start}, 自定义结束: {custom_end}")
        
        # 根据用户选择生成操作时间范围
        operation_time_range = generate_operation_time_range(
            time_option=time_option,
            df=df,
            shift_type=shift_type,
            custom_start=custom_start,
            custom_end=custom_end
        )
        
        # 用于存储结果数据
        result_data = []
        
        # 查找包含关键字的列
        columns_to_extract = {
            '汇总型号': ['型号', '汇总型号', '产品型号', '极片型号'],
            '工序': ['工序', '工序名称', '工位'],
            '批号': ['批号', '批次', '批次号', '批次条码'],
            '重量': ['重量', '净重', '质量', 'kg', 'KG'],
            '原车间': ['原车间', '来源车间', '生产车间'],
            '接收车间': ['接收车间', '目标车间', '去向车间']
        }
        
        # 性能优化：预编译列名映射，避免重复计算
        column_mappings = {}
        for target_col, possible_names in columns_to_extract.items():
            for col in df.columns:
                col_lower = str(col).lower()
                for possible_name in possible_names:
                    if possible_name.lower() in col_lower:
                        column_mappings[target_col] = col
                        break
                if target_col in column_mappings:
                    break
        
        # 性能优化：只加载一次映射规则
        mappings = load_mappings()
        logger.info(f"已加载映射规则: {mappings}")
        
        # 检查是否启用自定义映射
        custom_mapping_enabled = session.get('custom_mapping_enabled', True)
        
        # 为每一行数据提取信息（使用向量化操作，减少循环开销）
        # 先提取所有需要的列
        extracted_data = {}
        for target_col, source_col in column_mappings.items():
            if source_col in df.columns:
                extracted_data[target_col] = df[source_col]
        
        # 处理每一行数据
        for idx, row in df.iterrows():
            row_data = {}
            
            # 快速提取数据
            for target_col, source_col in column_mappings.items():
                if source_col in df.columns:
                    value = row[source_col]
                    if pd.notna(value):
                        row_data[target_col] = value
            
            # 只添加至少有一个字段的数据行
            if any(row_data.values()):
                # 格式化车间名称，移除多余的前缀和后缀
                if '原车间' in row_data and row_data['原车间']:
                    row_data['原车间'] = format_workshop_name(row_data['原车间'])
                
                if '接收车间' in row_data and row_data['接收车间']:
                    row_data['接收车间'] = format_workshop_name(row_data['接收车间'])
                
                # 添加映射逻辑：如果型号为空，根据批号前缀确定极片型号
                if custom_mapping_enabled and ('汇总型号' not in row_data or not row_data['汇总型号'] or str(row_data['汇总型号']) == '0'):
                    if '批号' in row_data and row_data['批号']:
                        batch_str = str(row_data['批号']).strip()
                        if len(batch_str) >= 3:
                            prefix = batch_str[:3]
                            if prefix in mappings:
                                row_data['汇总型号'] = mappings[prefix]
                
                result_data.append(row_data)
        
        logger.info(f"数据处理完成，共提取{len(result_data)}条有效记录")
        # 按批号升序排列
        result_data.sort(key=lambda x: str(x.get('批号', '')), reverse=False)
        
        # 记录部分数据用于调试
        if result_data:
            logger.info(f"前5条处理后的数据: {result_data[:5]}")
            # 统计各字段的非空值数量
            for col in columns_to_extract.keys():
                non_null_count = sum(1 for row in result_data if col in row and row[col])
                logger.info(f"字段'{col}'非空值数量: {non_null_count}/{len(result_data)}")
        
        # 清除session中的旧数据，确保数据完全刷新
        if 'honglian_original_data' in session:
            del session['honglian_original_data']
            logger.info("已清除旧的原始数据，准备存储新文件的数据")
        
        # 使用固定的列顺序，确保按照用户要求的顺序显示
        columns = ['汇总型号', '工序', '批号', '重量', '原车间', '接收车间']
        
        # 检查数据大小，如果超过阈值，使用临时文件存储
        data_size = len(str(result_data))
        if data_size > 100000:  # 100KB阈值
            # 使用临时文件存储大型数据
            temp_file_path = temp_file_manager.save_data(result_data, prefix='honglian_')
            session['honglian_data'] = {
                'filename': filename,
                'columns': columns,  # 使用目标列名作为表头
                'data_file': temp_file_path,  # 存储临时文件路径
                'operation_time_range': operation_time_range  # 新增操作时间范围
            }
            logger.info(f"新文件'{filename}'数据已成功存储到临时文件: {temp_file_path}")
        else:
            # 直接存储到session
            session['honglian_data'] = {
                'filename': filename,
                'columns': columns,  # 使用目标列名作为表头
                'data': result_data,
                'operation_time_range': operation_time_range  # 新增操作时间范围
            }
            logger.info(f"新文件'{filename}'数据已成功存储到session")
        
        # 重定向到开红莲结果页面
        return redirect(url_for('honglian_result'))
    except Exception as e:
        app.logger.error(f"开红莲模式处理文件时出错: {str(e)}")
        flash(f"开红莲模式处理文件时出错: {str(e)}", 'error')
        return redirect('/')



        selected_columns = list(column_mapping.values())
        required_columns = list(columns_to_extract.keys())
        
        # 添加光箔*和去光箔后报废到必需列
        if '光箔*' not in required_columns:
            required_columns.append('光箔*')
        if '去光箔后报废' not in required_columns:
            required_columns.append('去光箔后报废')
        
        # 数据处理 - 使用统一的清理函数
        result_data = []
        for idx, row in df.iterrows():
            row_data = {}
            
            # 映射列名并提取数据
            for target_col, source_col in column_mapping.items():
                if source_col in df.columns:
                    value = row[source_col]
                    
                    # 对数值字段使用统一的清理函数
                    if target_col in ['良品数(kg)', '报废数(kg)', '光箔*']:
                        cleaned_value = clean_numeric_value(value)
                        row_data[target_col] = cleaned_value
                        # 记录良品数的处理情况
                        if target_col == '良品数(kg)' and idx < 5:  # 只记录前5行用于调试
                            logger.debug(f"原始良品数 - 索引{idx}: 原始值={value}, 清理后={cleaned_value}")
                    else:
                        # 非数值字段的处理
                        if pd.isna(value):
                            row_data[target_col] = ''
                        else:
                            row_data[target_col] = str(value).strip()
            
            # 只添加非空数据行
            if any(str(v).strip() for v in row_data.values()) or any(isinstance(v, (int, float)) and v != 0 for v in row_data.values()):
                result_data.append(row_data)
        
        logger.info(f"数据处理完成，共提取{len(result_data)}条有效记录")
        
        # 分类汇总：按产品型号和工序名称分组，对数值字段求和
        # 1. 将列表转换为DataFrame便于聚合
        if result_data:
            summary_df = pd.DataFrame(result_data)
            
            # 记录良品数字段的统计信息
            if '良品数(kg)' in summary_df.columns:
                logger.info(f"良品数字段统计信息 - 数据类型: {summary_df['良品数(kg)'].dtype}")
                logger.info(f"良品数字段统计信息 - 非零值数量: {summary_df['良品数(kg)'].count()}")
                logger.info(f"良品数字段统计信息 - 总和: {summary_df['良品数(kg)'].sum()}")
            
            # 2. 定义分组键和数值字段 - 优化分组顺序，使班次成为主要维度
            group_keys = ['班次', '日期', '产品型号', '工序名称']
            numeric_fields = ['良品数(kg)', '报废数(kg)', '光箔*', '投入数']
            
            # 确保分组键存在
            group_keys = [key for key in group_keys if key in summary_df.columns]
            numeric_fields = [field for field in numeric_fields if field in summary_df.columns]
            
            # 对所有数值字段进行统一的预处理，确保都是数值类型
            for field in numeric_fields:
                if field in summary_df.columns:
                    logger.info(f"统一预处理数值字段: {field}")
                    # 确保是数值类型
                    summary_df[field] = pd.to_numeric(summary_df[field], errors='coerce').fillna(0)
                    logger.info(f"字段 {field} 预处理后 - 非零值: {(summary_df[field] > 0).sum()}, 平均值: {summary_df[field].mean():.2f}")
            
            # 如果投入数字段不存在，尝试从良品数和报废数推导
            if '投入数' not in summary_df.columns:
                logger.warning("投入数字段不存在，尝试从良品数和报废数推导")
                if '良品数(kg)' in summary_df.columns and '报废数(kg)' in summary_df.columns:
                    summary_df['投入数'] = summary_df['良品数(kg)'] + summary_df['报废数(kg)']
                    logger.info("已从良品数和报废数推导投入数")
            
            if group_keys:
                # 3. 对数值字段进行求和汇总
                agg_dict = {field: 'sum' for field in numeric_fields}
                
                # 4. 执行分组汇总
                try:
                    # 确保所有分组键都不为空
                    for key in group_keys:
                        summary_df = summary_df[summary_df[key].notna() & (summary_df[key] != '')]
                    
                    summary_result = summary_df.groupby(group_keys, as_index=False).agg(agg_dict)
                    
                    # 5. 处理汇总结果，保留原始格式
                    summary_data = []
                    for _, row in summary_result.iterrows():
                        row_dict = {}
                        for key in group_keys:
                            row_dict[key] = row[key]
                        for field in numeric_fields:
                            if pd.notna(row[field]):
                                # 统一使用浮点数计算并保留1位小数
                                try:
                                    row_dict[field] = round(float(row[field]), 1)
                                except:
                                    row_dict[field] = 0.0
                            else:
                                row_dict[field] = 0.0
                        
                        # 计算去光箔后报废 = 报废数(kg) - 光箔*
                        try:
                            # 确保光箔*字段存在，如果不存在则默认为0
                            if '光箔*' not in row_dict:
                                row_dict['光箔*'] = 0.0
                                logger.debug("光箔*字段不存在，使用默认值0")
                            
                            scrap_value = float(row_dict.get('报废数(kg)', 0))
                            foil_value = float(row_dict['光箔*'])
                            net_scrap = scrap_value - foil_value
                            row_dict['去光箔后报废'] = round(net_scrap, 1)
                            
                            logger.debug(f"计算去光箔后报废: {scrap_value} - {foil_value} = {row_dict['去光箔后报废']}")
                        except Exception as e:
                            logger.warning(f"计算去光箔后报废时出错: {str(e)}")
                            row_dict['去光箔后报废'] = 0.0
                        
                        # 计算产出数 = 投入数 - 报废数(kg)
                        try:
                            input_value = float(row_dict.get('投入数', 0))
                            scrap_value = float(row_dict.get('报废数(kg)', 0))
                            output_value = input_value - scrap_value
                            row_dict['产出数'] = round(output_value, 1)
                            
                            logger.debug(f"计算产出数: {input_value} - {scrap_value} = {row_dict['产出数']}")
                        except Exception as e:
                            logger.warning(f"计算产出数时出错: {str(e)}")
                            row_dict['产出数'] = 0.0
                        
                        # 数据一致性校验
                        try:
                            input_value = float(row_dict.get('投入数', 0))
                            good_value = float(row_dict.get('良品数(kg)', 0))
                            scrap_value = float(row_dict.get('报废数(kg)', 0))
                            
                            # 检查投入数是否等于良品数加报废数（允许0.001的误差）
                            if abs(input_value - (good_value + scrap_value)) > 0.001:
                                logger.warning(f"数据一致性校验失败: 投入数{input_value} != 良品数{good_value} + 报废数{scrap_value}")
                                # 添加标记，但不阻止数据显示
                                row_dict['数据状态'] = '不一致'
                            else:
                                row_dict['数据状态'] = '一致'
                        except Exception as e:
                            logger.warning(f"数据一致性校验时出错: {str(e)}")
                            row_dict['数据状态'] = '校验失败'
                        
                        summary_data.append(row_dict)
                    
                    logger.info(f"数据汇总完成，共{len(summary_data)}条汇总记录")
                    # 保存原始明细数据到session，用于后续验证
                    # 使用汇总数据替换原始明细数据
                    result_data = summary_data
                except Exception as e:
                    logger.warning(f"数据汇总失败，使用原始数据: {str(e)}")
        
        # 按日期、班次、产品型号和工序名称排序
        if result_data:
            sort_keys = ['日期', '班次', '产品型号', '工序名称']
            sort_keys = [key for key in sort_keys if any(key in row for row in result_data)]
            
            def sort_key(row):
                return tuple(str(row.get(key, '')) for key in sort_keys)
            
            result_data.sort(key=sort_key)
        
        # 再次清除session中的旧数据，但保留原始明细数据
        for key in []:
            if key in session:
                del session[key]
                logger.info(f"在存储新数据前再次清除session[{key}]")
        
        # 注意：保留数据用于后续获取明细数据
        
        # 设置上传时间戳，用于验证是否真的是新上传
        session['last_upload_time'] = datetime.now().isoformat()
        logger.info(f"设置上传时间戳: {session['last_upload_time']}")
        
        # 确保required_columns包含光箔*字段
        if '光箔*' not in required_columns:
            # 找到报废数(kg)的位置，将光箔*插入在其后
            if '报废数(kg)' in required_columns:
                idx = required_columns.index('报废数(kg)')
                required_columns.insert(idx + 1, '光箔*')
            else:
                required_columns.append('光箔*')
        
        # 确保required_columns包含去光箔后报废字段
        if '去光箔后报废' not in required_columns:
            # 找到光箔*的位置，将去光箔后报废插入在其后
            if '光箔*' in required_columns:
                idx = required_columns.index('光箔*')
                required_columns.insert(idx + 1, '去光箔后报废')
            elif '报废数(kg)' in required_columns:
                idx = required_columns.index('报废数(kg)')
                required_columns.insert(idx + 1, '去光箔后报废')
            else:
                required_columns.append('去光箔后报废')
        
        # 添加产出数字段到必需列
        if '产出数' not in required_columns:
            # 找到报废数(kg)的位置，将产出数插入在其后
            if '报废数(kg)' in required_columns:
                idx = required_columns.index('报废数(kg)')
                # 如果去光箔后报废在报废数后面，则插入到去光箔后报废后面
                if '去光箔后报废' in required_columns and required_columns.index('去光箔后报废') == idx + 1:
                    required_columns.insert(idx + 2, '产出数')
                else:
                    required_columns.insert(idx + 1, '产出数')
            else:
                required_columns.append('产出数')
        
        # 存储结果到session
        session['data'] = {
            'filename': unique_filename,  # 使用带时间戳的唯一文件名
            'columns': required_columns,
            'data': result_data,
            'operation_time_range': operation_time_range,
            'timestamp': timestamp  # 添加时间戳便于调试
        }
        logger.info(f"已存储新的处理结果到session，包含{len(result_data)}条记录")
        logger.info(f"处理结果示例: {result_data[0] if result_data else '无数据'}")
        
        # 重定向到结果页面
        return redirect(url_for('result'))
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        flash(f"处理文件时出错: {str(e)}", 'error')
        return redirect('/')

def normal_mode_handler(file):
    """处理普通模式的文件上传"""
    try:
        # 保存上传的文件
        original_filename = file.filename
        filename = secure_filename(original_filename)
        logger.info(f"原始文件名: {original_filename}, 安全处理后: {filename}")
        
        # 检查文件名是否有效
        if not filename or filename == '':
            logger.error(f"文件名无效: 原始文件名='{original_filename}', 安全处理后='{filename}'")
            flash('文件名无效，请检查文件名是否包含特殊字符', 'error')
            return redirect('/')
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 确保上传目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        file.save(filepath)
        logger.info(f"已保存上传文件: {filename}, 文件大小: {os.path.getsize(filepath)} bytes")
        
        # 检查文件是否为空
        if os.path.getsize(filepath) == 0:
            logger.error(f"文件为空: {filename}")
            flash('上传的文件为空，请检查文件内容', 'error')
            return redirect('/')
        
        # 读取和处理文件
        try:
            df = read_file_with_encoding(filepath)
            logger.info(f"文件读取成功，形状: {df.shape}, 列名: {list(df.columns)}")
            
            # 检查数据框是否有效
            if df.empty:
                logger.warning(f"文件读取结果为空: {filename}")
                flash('文件内容为空或无法读取有效数据', 'warning')
                return redirect('/')
                
            # 检查列名是否异常（可能是二进制文件被错误读取）
            if len(df.columns) == 1 and any(ord(char) < 32 or ord(char) > 126 for char in str(df.columns[0])):
                logger.error(f"文件可能被错误读取为二进制: {filename}, 列名: {df.columns[0]}")
                flash('文件格式错误，请确保上传的是有效的Excel或CSV文件', 'error')
                return redirect('/')
                
        except Exception as e:
            logger.error(f"文件读取失败: {str(e)}, 文件: {filename}")
            flash(f"文件读取失败，请检查文件格式: {str(e)}", 'error')
            return redirect('/')
        
        # 检查是否有极片批号或批次条码列，如果有则添加极片型号列作为第一列
        # 优先使用批次条码列
        batch_number_col = None
        for col in df.columns:
            if '批次条码' in col:
                batch_number_col = col
                break
        # 如果没有批次条码列，则查找极片批号或批号列
        if batch_number_col is None:
            for col in df.columns:
                if '极片批号' in col or '批号' in col:
                    batch_number_col = col
                    break
        
        if batch_number_col:
            # 性能优化：只加载一次映射规则，避免重复IO操作
            mappings = load_mappings()
            
            # 创建极片型号列的函数
            def determine_model(batch_number):
                if pd.isna(batch_number):
                    return ''
                batch_str = str(batch_number)
                # 检查是否有型号列，如果有且不为0则使用型号列的值
                if '型号' in df.columns:
                    model_idx = df.columns.get_loc('型号')
                    row_idx = df[df[batch_number_col] == batch_number].index
                    if len(row_idx) > 0 and not pd.isna(df.iloc[row_idx[0], model_idx]) and df.iloc[row_idx[0], model_idx] != 0:
                        return str(df.iloc[row_idx[0], model_idx])
                # 基于批号/批次条码前缀确定极片型号
                if len(batch_str) >= 3:
                    prefix = batch_str[:3]
                    # 性能优化：使用预加载的映射规则，避免重复读取文件
                    if prefix in mappings:
                        return mappings[prefix]
                return ''
            
            # 应用函数创建极片型号列
            df['极片型号'] = df[batch_number_col].apply(determine_model)
            # 将极片型号列移动到第一列
            cols = df.columns.tolist()
            cols.insert(0, cols.pop(cols.index('极片型号')))
            df = df[cols]
            app.logger.info(f"已添加极片型号列，基于{batch_number_col}列生成")
            
            # 保存修改后的数据框回文件，确保后续分析也能使用
            if filename.endswith(('.xlsx', '.xls')):
                df.to_excel(filepath, engine='openpyxl', index=False)
            else:
                # 根据原始编码保存
                try:
                    df.to_csv(filepath, encoding='utf-8', index=False)
                except UnicodeEncodeError:
                    df.to_csv(filepath, encoding='gbk', index=False)
        
        # 存储到session (但大数据集可能有问题)
        # 更好的方法是存储文件路径和基本信息
        session_data = {
            'filepath': filepath,
            'filename': filename,
            'columns': df.columns.tolist(),
            'shape': {'rows': len(df), 'columns': len(df.columns)}
        }
        
        # 保存到临时存储
        # 性能优化：使用已导入的json模块
        with open(os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}_meta.json'), 'w') as f:
            json.dump(session_data, f)
        
        return render_template('setup_columns.html', 
                             filename=filename,
                             columns=df.columns.tolist(),
                             shape=session_data['shape'])
    except Exception as e:
        app.logger.error(f"处理文件时出错: {str(e)}")
        flash(f"处理文件时出错: {str(e)}", 'error')
        return redirect('/')


@app.route('/process', methods=['POST'])
def process_file():
    """通用处理路由，根据表单提交的mode参数来决定调用普通模式还是开红莲模式"""
    try:
        # 获取模式参数
        mode = request.form.get('mode', 'normal')
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            flash('没有文件上传', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
        # 检查文件类型
        if not allowed_file(file.filename):
            flash('不支持的文件类型，请上传Excel或CSV文件', 'error')
            return redirect(request.url)
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        logger.info(f"处理文件上传，模式: {mode}, 文件名: {file.filename}, 文件大小: {file_size} bytes")
        
        # 如果文件大小超过阈值，使用异步处理
        if file_size > 5 * 1024 * 1024:  # 5MB阈值
            logger.info(f"文件大小超过阈值，使用异步处理")
            
            # 保存文件到临时位置
            temp_filename = secure_filename(file.filename)
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{temp_filename}")
            file.save(temp_filepath)
            
            # 定义异步处理函数
            def async_process(temp_filepath, mode, filename):
                """异步处理文件"""
                try:
                    # 重新打开文件
                    with open(temp_filepath, 'rb') as f:
                        # 创建一个模拟的FileStorage对象
                        from werkzeug.datastructures import FileStorage
                        mock_file = FileStorage(stream=f, filename=filename)
                        
                        # 根据模式调用不同的处理函数
                        if mode == 'honglian':
                            return honglian_mode_handler(mock_file)
                        else:  # normal mode
                            return normal_mode_handler(mock_file)
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_filepath):
                        try:
                            os.remove(temp_filepath)
                            logger.info(f"临时文件已清理: {temp_filepath}")
                        except Exception as e:
                            logger.error(f"清理临时文件失败: {str(e)}")
            
            # 提交异步任务
            future = async_task_manager.submit_task(
                async_process, 
                temp_filepath, 
                mode, 
                file.filename
            )
            
            # 等待任务完成（这里我们仍然需要等待，因为Flask需要返回响应）
            # 但是使用线程池可以避免阻塞主线程
            try:
                result = async_task_manager.get_task_result(future, timeout=300)  # 5分钟超时
                return result
            except concurrent.futures.TimeoutError:
                flash('文件处理超时，请尝试上传 smaller 文件', 'error')
                return redirect('/')
        else:
            # 文件大小在阈值以下，使用同步处理
            logger.info(f"文件大小在阈值以下，使用同步处理")
            if mode == 'honglian':
                return honglian_mode_handler(file)
            else:  # normal mode
                return normal_mode_handler(file)
    
    except Exception as e:
        app.logger.error(f"处理文件时出错: {str(e)}")
        flash(f"处理文件时出错: {str(e)}", 'error')
        return redirect('/')


@app.route('/honglian_mode', methods=['POST'])
def honglian_mode():
    """开红莲专用模式，直接汇总型号、工序、批号、重量、原车间、接收车间"""
    # 兼容性路由，重定向到通用处理路由
    return process_file()



@app.route('/honglian_result', methods=['GET'])
def honglian_result():
    """显示开红莲专用模式处理结果，支持多条件筛选和分页"""
    if 'honglian_data' not in session:
        flash('没有处理结果，请先上传文件', 'danger')
        return redirect(url_for('index'))
    
    # 保存原始数据到session中，以便多次筛选
    if 'honglian_original_data' not in session:
        data = session['honglian_data']
        if 'data_file' in data:
            # 从临时文件加载数据
            result_data = temp_file_manager.load_data(data['data_file'])
            if result_data is None:
                flash('数据加载失败，请重新上传文件', 'danger')
                return redirect(url_for('index'))
            session['honglian_original_data'] = result_data
            logger.info(f"从临时文件初始化原始数据，共{len(session['honglian_original_data'])}条记录")
        else:
            # 直接从session加载数据
            session['honglian_original_data'] = data['data']
            logger.info(f"初始化原始数据，共{len(session['honglian_original_data'])}条记录")
    
    data = session['honglian_data']
    logger.info(f"进入honglian_result，原始数据总数: {len(session['honglian_original_data'])}")
    
    # 获取筛选参数
    filters = {}
    for col in data['columns']:
        filter_value = request.args.get(col, '').strip()
        if filter_value:
            filters[col] = filter_value
    
    logger.info(f"应用筛选条件: {filters}")
    
    # 应用筛选 - 支持空格分隔的多条件筛选（OR逻辑）
    filtered_data = session['honglian_original_data']
    
    # 处理不显示指定车间数据的逻辑
    exclude_workshop = request.args.get('exclude_workshop', '')
    
    # 获取手动输入的屏蔽车间列表
    manual_exclude = request.args.get('manual_exclude', '').strip()
    
    # 合并所有需要屏蔽的车间
    workshops_to_exclude = []
    
    # 如果选择了排除四二车间，添加到列表
    if exclude_workshop == '四二车间':
        workshops_to_exclude.append('四二车间')
    
    # 处理手动输入的车间列表（支持逗号、空格或换行分隔）
    if manual_exclude:
        # 使用正则表达式分割，支持多种分隔符
        import re
        manual_workshops = re.split(r'[\s,，;；\n\r]+', manual_exclude)
        # 过滤掉空字符串
        manual_workshops = [ws.strip() for ws in manual_workshops if ws.strip()]
        workshops_to_exclude.extend(manual_workshops)
    
    # 如果有需要屏蔽的车间，执行过滤
    if workshops_to_exclude:
        before_count = len(filtered_data)
        filtered_data = [row for row in filtered_data if 
                        not any(workshop in [row.get('原车间', ''), row.get('接收车间', '')] 
                                for workshop in workshops_to_exclude)]
        after_count = len(filtered_data)
        logger.info(f"排除车间数据 - 车间列表: {workshops_to_exclude}, 记录数从{before_count}减少到{after_count}")
    
    # 然后应用其他筛选条件
    for col, value in filters.items():
        # 使用空格分割多个筛选条件
        filter_conditions = value.strip().split()
        before_count = len(filtered_data)
        
        # 实现多条件OR筛选逻辑
        filtered_data = [row for row in filtered_data if 
                        col in row and 
                        any(str(row[col]).strip().lower().find(cond.lower()) != -1 
                            for cond in filter_conditions)]
        
        after_count = len(filtered_data)
        logger.info(f"应用多条件筛选 '{col}': '{value}' - 记录数从{before_count}减少到{after_count}")
        
        # 调试：显示筛选过程中的一些样本
        if after_count > 0 and after_count <= 5:
            logger.info(f"筛选后的数据样本: {filtered_data}")
        elif after_count > 5:
            logger.info(f"筛选后的数据样本(前3条): {filtered_data[:3]}")
            # 检查是否有匹配但被错误过滤的数据
            for row in session['honglian_original_data'][:10]:  # 检查前10条原始数据
                if col in row:
                    row_value = str(row[col]).strip().lower()
                    # 检查row_value是否包含任何筛选条件
                    if any(cond.lower() in row_value for cond in filter_conditions) and row not in filtered_data:
                        logger.warning(f"数据行应该被匹配但被过滤: {row}")
    
    # 分页处理 - 支持自定义每页显示数量和全部显示
    page_size_param = request.args.get('page_size', 'all')
    
    # 处理'all'选项和数字选项
    if page_size_param == 'all':
        page_size = 'all'
        page = 1
        total_pages = 1
        paginated_data = filtered_data
    else:
        # 对于数字选项，转换为整数
        try:
            page_size = int(page_size_param)
        except ValueError:
            page_size = 8
        # 获取当前页码，默认为1
        page = request.args.get('page', 1, type=int)
        # 计算总页数
        total_pages = (len(filtered_data) + page_size - 1) // page_size
        # 计算当前页数据的起始和结束索引
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        # 获取当前页的数据
        paginated_data = filtered_data[start_idx:end_idx]
    
    # 更新当前显示的数据
    data['data'] = paginated_data
    
    # 计算总计值 - 为重量字段添加汇总功能
    total_values = {}
    numeric_fields = ['重量']  # 红莲模式主要是重量字段的汇总
    
    # 初始化所有数值字段的总计值为0
    for field in numeric_fields:
        total_values[field] = 0
    
    # 遍历数据计算各个字段的总和
    for row in filtered_data:
        for field in numeric_fields:
            try:
                val = row.get(field, '')
                # 处理不同类型的值
                if val is None or val == '':
                    continue
                
                # 尝试清理和转换重量值
                if isinstance(val, (int, float)):
                    total_values[field] += val
                else:
                    val_str = str(val).strip()
                    # 提取数字部分
                    import re
                    number_match = re.search(r'\d+\.?\d*', val_str)
                    if number_match:
                        total_values[field] += float(number_match.group())
                    elif val_str == '0' or val == 0:
                        total_values[field] += 0.0
            except (ValueError, TypeError):
                # 如果转换失败，跳过该值
                continue
    
    # 格式化数值，保留两位小数或转换为整数
    for field in numeric_fields:
        try:
            if total_values[field] == int(total_values[field]):
                total_values[field] = int(total_values[field])
            else:
                total_values[field] = round(total_values[field], 2)
        except (ValueError, TypeError):
            total_values[field] = ''
    
    # 更新日志信息，突出显示这是汇总数据
    logger.info(f"显示汇总数据，共{len(filtered_data)}条汇总记录")
    if total_values:
        logger.info(f"数值字段总计: {total_values}")
    
    return render_template('honglian_result.html', 
                         filename=data['filename'],
                         columns=data['columns'],
                         data=paginated_data,
                         filters=filters,
                         page=page,
                         total_pages=total_pages,
                         page_size=page_size,
                         total_items=len(filtered_data),
                         total_values=total_values)

@app.route('/upload', methods=['POST'])
def upload_file():
    """兼容旧的上传路由，重定向到通用处理路由"""
    return process_file()

@app.route('/analyze', methods=['POST'])
def analyze_data():
    # POST请求处理逻辑
    filename = request.form['filename']
    meta_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}_meta.json')
    
    try:
        import json
        with open(meta_file, 'r') as f:
            session_data = json.load(f)
        
        filepath = session_data['filepath']
        
        # 获取用户选择的列
        selected_columns = request.form.getlist('columns')
        
        # 如果用户没有选择任何列，显示错误信息
        if not selected_columns:
            flash('请至少选择一列进行分析', 'danger')
            return render_template('setup_columns.html',
                                 filename=filename,
                                 columns=session_data['columns'],
                                 shape=session_data['shape'])
        
        # 读取文件
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='gbk')
        
        # 只保留用户选择的列
        df = df[selected_columns]
        
        # 改进的数据类型转换，使用coerce而非ignore以确保数值列被正确识别
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                # 先尝试移除可能的千位分隔符和货币符号
                try:
                    # 复制一列进行尝试转换
                    test_series = df[col].copy()
                    # 尝试移除常见的千位分隔符
                    test_series = test_series.str.replace(',', '', regex=False)
                    # 尝试移除货币符号
                    test_series = test_series.str.replace('￥', '', regex=False)
                    test_series = test_series.str.replace('$', '', regex=False)
                    # 尝试转换为数值，使用coerce以便将非数值转换为NaN
                    numeric_series = pd.to_numeric(test_series, errors='coerce')
                    # 检查是否有超过50%的值成功转换为数值
                    if numeric_series.notna().mean() > 0.5:
                        df[col] = numeric_series
                        app.logger.info(f"列 {col} 已成功转换为数值类型")
                except Exception as e:
                    app.logger.warning(f"转换列 {col} 时出错: {str(e)}")
                    # 如果前面的处理失败，回退到简单转换
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
        
        # 生成统计信息
        stats = df.describe().to_html(classes='table table-striped', justify='center')
        
        # 生成数据预览
        preview = df.head(10).to_html(classes='table table-striped', justify='center')
        
        # 生成图表
        charts = []
        # 限制最大图表数量，避免内存占用过高
        max_charts = 5
        
        # 统计柱状图 - 数值列
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:3]:  # 限制为前3列以避免过多图表
                plt.figure(figsize=(8, 5))  # 减小图表尺寸，降低内存占用
                # 对于数值列，我们可以创建分组统计柱状图
                # 首先将数值分组
                try:
                    # 对于连续性数值，我们可以使用分箱后的数据
                    bins = min(10, len(df[col].unique()))  # 最多10个箱子
                    if bins > 1:
                        # 创建分箱
                        df['temp_bin'] = pd.cut(df[col].dropna(), bins=bins)
                        # 计算每个分箱的计数
                        bin_counts = df['temp_bin'].value_counts().sort_index()
                        # 绘制柱状图
                        ax = bin_counts.plot(kind='bar')
                        plt.title(f'{col} 统计柱状图')
                        plt.xlabel('数值区间')
                        plt.ylabel('计数')
                        # 调整x轴标签角度
                        plt.xticks(rotation=45, ha='right')
                        # 删除临时列
                        df.drop('temp_bin', axis=1, inplace=True)
                    else:
                        # 如果唯一值太少，直接使用原始值统计
                        value_counts = df[col].value_counts().head(10)  # 最多显示10个类别
                        ax = value_counts.plot(kind='bar')
                        plt.title(f'{col} 统计柱状图')
                        plt.xlabel('数值')
                        plt.ylabel('计数')
                        plt.xticks(rotation=45, ha='right')
                except Exception as e:
                    # 如果分箱失败，回退到简单的柱状图
                    app.logger.warning(f"创建柱状图出错: {str(e)}")
                    plt.title(f'{col} 统计柱状图')
                    sns.countplot(data=df, x=col)
                    plt.xticks(rotation=45, ha='right')
                
                plt.tight_layout()
                
                img = BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                
                chart_base64 = base64.b64encode(img.read()).decode('utf-8')
                if len(charts) < max_charts:
                    charts.append({
                        'title': f'{col} 统计柱状图',
                        'data': chart_base64
                    })
                plt.close()
        
        # 相关性热图
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            plt.figure(figsize=(8, 6))  # 减小图表尺寸，降低内存占用
            sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
            plt.title('相关性热图')
            plt.tight_layout()
            
            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            
            chart_base64 = base64.b64encode(img.read()).decode('utf-8')
            if len(charts) < max_charts:
                charts.append({
                    'title': '相关性热图',
                    'data': chart_base64
                })
            plt.close()
        
        # 箱线图
        if len(numeric_cols) > 0:
            plt.figure(figsize=(8, 5))  # 减小图表尺寸，降低内存占用
            sns.boxplot(data=df[numeric_cols])
            plt.xticks(rotation=45)
            plt.title('数值列箱线图')
            plt.tight_layout()
            
            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            
            chart_base64 = base64.b64encode(img.read()).decode('utf-8')
            if len(charts) < max_charts:
                charts.append({
                    'title': '数值列箱线图',
                    'data': chart_base64
                })
            plt.close()
        
        # 显式删除临时变量，释放内存
        del img
        # 生成汇总数据
        # 保存汇总结果
        aggregated_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{os.path.splitext(filename)[0]}_aggregated.xlsx')
        
        with pd.ExcelWriter(aggregated_file, engine='openpyxl') as writer:
            # 原始数据预览
            df.head(50).to_excel(writer, sheet_name='数据预览', index=False)
            
            # 统计摘要
            df.describe().to_excel(writer, sheet_name='统计摘要')
            
            # 数据质量报告
            quality_report = pd.DataFrame({
                '列名': df.columns,
                '数据类型': df.dtypes.astype(str),
                '缺失值数量': df.isnull().sum(),
                '缺失值百分比': (df.isnull().sum() / len(df) * 100).round(2),
                '唯一值数量': df.nunique()
            })
            quality_report.to_excel(writer, sheet_name='数据质量报告', index=False)
        
        return render_template('results.html',
                             filename=filename,
                             stats=stats,
                             preview=preview,
                             charts=charts,
                             aggregated_file=os.path.basename(aggregated_file),
                             columns=df.columns.tolist())
        
    except Exception as e:
        logger.error(f"图表生成失败: {str(e)}")
        flash(f'图表生成失败: {str(e)}', 'error')
        try:
            # 尝试最小化的数据读取
            meta_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}_meta.json')
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    session_data = json.load(f)
                filepath = session_data['filepath']
                
                if os.path.exists(filepath):
                    # 读取文件用于预览
                    if filename.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(filepath, engine='openpyxl')
                    else:
                        try:
                            df = pd.read_csv(filepath, encoding='utf-8')
                        except UnicodeDecodeError:
                            df = pd.read_csv(filepath, encoding='gbk')
                    # 返回基本的数据预览，不生成图表
                    preview = df.head(10).to_html(classes='table table-striped', justify='center')
                    columns = df.columns.tolist()
                    return render_template('results.html',
                                         filename=filename,
                                         stats='',
                                         preview=preview,
                                         charts=[],
                                         aggregated_file='',
                                         columns=columns,
                                         error_message=f"图表生成遇到问题，请尝试重新上传文件")
        except Exception as inner_e:
            logger.error(f"异常处理时出错: {str(inner_e)}")
        return render_template('results.html',
                             filename=filename,
                             stats='',
                             preview='',
                             charts=[],
                             aggregated_file='',
                             columns=[],
                             error_message="数据处理失败，请尝试重新上传文件")

# 处理GET请求的结果展示路由
@app.route('/show_results/<filename>', methods=['GET'])
def show_results(filename):
    """从URL直接访问结果页面"""
    meta_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}_meta.json')
    
    if not os.path.exists(meta_file):
        flash('文件不存在或已过期', 'error')
        return redirect(url_for('index'))
    
    try:
        # 重新执行数据分析逻辑，但使用已保存的元数据
        import json
        with open(meta_file, 'r') as f:
            session_data = json.load(f)
        
        filepath = session_data['filepath']
        
        # 读取文件
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='gbk')
        
        # 使用所有列进行分析
        selected_columns = session_data['columns']
        
        # 应用列选择
        if selected_columns:
            df = df[selected_columns]
        
        # 生成统计信息
        stats = df.describe().to_html(classes='table table-striped', justify='center')
        
        # 生成数据预览
        preview = df.head(10).to_html(classes='table table-striped', justify='center')
        
        # 初始化图表列表
        charts = []
        
        # 检查是否有数值列
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        # 如果有数值列，尝试生成一些基本图表（简化版，降低内存消耗）
        if len(numeric_cols) > 0:
            # 只生成一个简单的柱状图
            col = numeric_cols[0]
            try:
                plt.figure(figsize=(8, 5))
                if len(df[col].unique()) <= 20:  # 避免类别太多
                    df[col].value_counts().head(10).plot(kind='bar')
                else:
                    # 对于连续性数据，使用直方图
                    df[col].hist(bins=20)
                plt.title(f'{col} 分布图')
                plt.tight_layout()
                
                # 将图表转换为base64
                img = BytesIO()
                plt.savefig(img, format='png', dpi=96)  # 降低dpi，减小文件大小
                img.seek(0)
                chart_base64 = base64.b64encode(img.read()).decode('utf-8')
                charts.append({
                    'title': f'{col} 分布图',
                    'data': chart_base64
                })
                plt.close()
                del img
            except:
                pass
        
        # 检查是否已有汇总文件
        aggregated_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{os.path.splitext(filename)[0]}_aggregated.xlsx')
        aggregated_filename = os.path.basename(aggregated_file) if os.path.exists(aggregated_file) else ''
        
        return render_template('results.html',
                             filename=filename,
                             stats=stats,
                             preview=preview,
                             charts=charts,
                             aggregated_file=aggregated_filename,
                             columns=df.columns.tolist())
        
    except Exception as e:
        logger.error(f"展示结果失败: {str(e)}")
        flash(f'展示结果失败: {str(e)}', 'error')
        return render_template('results.html',
                             filename=filename,
                             stats='',
                             preview='',
                             charts=[],
                             aggregated_file='',
                             columns=[],
                             error_message="数据处理失败，请尝试重新上传文件")
  
@app.route('/download_file/<path:filename>')
def download_file(filename):
    from flask import send_from_directory
    import os
    
    # 记录详细信息用于调试
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    app.logger.info(f"尝试下载文件: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        app.logger.error(f"文件不存在: {file_path}")
        return f"文件不存在: {filename}", 404
    
    try:
        app.logger.info(f"发送文件: {filename}")
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        app.logger.error(f"下载文件时出错: {str(e)}")
        return f"下载文件时出错: {str(e)}", 500

@app.errorhandler(413)
def too_large(e):
    flash('文件过大，最大允许50MB。手机用户建议使用WiFi网络上传大文件', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(e):
    """处理文件过大错误"""
    return render_template('error.html', 
                         error_message='文件过大，最大允许50MB',
                         error_details='上传的文件大小超过了系统限制（50MB）。手机用户建议使用WiFi网络上传大文件，或压缩文件后重新上传。'), 413

@app.route('/aggregate', methods=['POST'])
def aggregate_data():
    """按表头汇总求和功能"""
    filename = request.form['filename']
    meta_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}_meta.json')
    
    try:
        import json
        with open(meta_file, 'r') as f:
            session_data = json.load(f)
        
        filepath = session_data['filepath']
        
        # 获取用户选择的分组列和数值列
        group_columns = request.form.getlist('group_columns')
        value_columns = request.form.getlist('value_columns')
        
        # 验证输入
        if not group_columns:
            flash('请至少选择一个分组列', 'danger')
            return render_template('results.html',
                                 filename=filename,
                                 stats='',
                                 preview='',
                                 charts=[],
                                 aggregated_file='',
                                 columns=session_data['columns'])
        
        if not value_columns:
            flash('请至少选择一个数值列', 'danger')
            return render_template('results.html',
                                 filename=filename,
                                 stats='',
                                 preview='',
                                 charts=[],
                                 aggregated_file='',
                                 columns=session_data['columns'])
        
        # 读取文件
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='gbk')
        
        # 确保列存在
        for col in group_columns + value_columns:
            if col not in df.columns:
                flash(f'列 "{col}" 不存在于数据中', 'danger')
                return render_template('results.html',
                                     filename=filename,
                                     stats='',
                                     preview='',
                                     charts=[],
                                     aggregated_file='',
                                     columns=session_data['columns'])
        
        # 改进的数值列转换，使用与analyze_data函数中相同的逻辑
        for col in value_columns:
            if pd.api.types.is_object_dtype(df[col]):
                # 先尝试移除可能的千位分隔符和货币符号
                try:
                    # 复制一列进行尝试转换
                    test_series = df[col].copy()
                    # 尝试移除常见的千位分隔符
                    test_series = test_series.str.replace(',', '', regex=False)
                    # 尝试移除货币符号
                    test_series = test_series.str.replace('￥', '', regex=False)
                    test_series = test_series.str.replace('$', '', regex=False)
                    # 尝试转换为数值，使用coerce以便将非数值转换为NaN
                    numeric_series = pd.to_numeric(test_series, errors='coerce')
                    # 检查是否有超过50%的值成功转换为数值
                    if numeric_series.notna().mean() > 0.5:
                        df[col] = numeric_series
                        app.logger.info(f"汇总列 {col} 已成功转换为数值类型")
                except Exception as e:
                    app.logger.warning(f"转换汇总列 {col} 时出错: {str(e)}")
                    # 如果前面的处理失败，回退到简单转换
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
        
        # 执行汇总计算
        agg_dict = {col: 'sum' for col in value_columns}
        summary_df = df.groupby(group_columns, as_index=False).agg(agg_dict)
        
        # 格式化汇总结果，添加查看明细按钮
        html_result = '<table class="table table-striped">'
        
        # 添加表头
        html_result += '<thead><tr>'
        for col in summary_df.columns:
            html_result += f'<th>{col}</th>'
        html_result += '<th>操作</th>'
        html_result += '</tr></thead><tbody>'
        
        # 添加数据行
        for _, row in summary_df.iterrows():
            html_result += '<tr>'
            group_values = []
            
            # 添加分组列值
            for col in group_columns:
                value = str(row[col]) if pd.notna(row[col]) else 'NaN'
                html_result += f'<td>{value}</td>'
                group_values.append(f'{col}:{value}')
            
            # 添加数值列值
            for col in value_columns:
                value = row[col]
                if pd.notna(value):
                    # 格式化数值，保留2位小数
                    try:
                        formatted_value = f"{float(value):,.2f}"
                    except:
                        formatted_value = str(value)
                else:
                    formatted_value = 'NaN'
                html_result += f'<td>{formatted_value}</td>'
            
            # 添加查看明细按钮
            group_identifier = '|'.join(group_values)
            html_result += f'<td><button class="detail-btn" data-group="{group_identifier}">查看明细</button></td>'
            html_result += '</tr>'
        
        html_result += '</tbody></table>'
        
        # 保存汇总结果用于后续查询
        session_data['last_aggregation'] = {
            'group_columns': group_columns,
            'value_columns': value_columns
        }
        with open(meta_file, 'w') as f:
            json.dump(session_data, f)
        
        # 重新生成原始的统计信息和预览
        stats = df.describe().to_html(classes='table table-striped', justify='center')
        preview = df.head(10).to_html(classes='table table-striped', justify='center')
        
        # 重新生成图表
        charts = []
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:3]:
                plt.figure(figsize=(10, 6))
                sns.histplot(df[col].dropna(), kde=True)
                plt.title(f'{col} 分布')
                plt.tight_layout()
                
                img = BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                
                chart_base64 = base64.b64encode(img.read()).decode('utf-8')
                charts.append({
                    'title': f'{col} 分布直方图',
                    'data': chart_base64
                })
                plt.close()
        
        # 生成汇总Excel文件，包含汇总结果和明细数据
        aggregated_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{os.path.splitext(filename)[0]}_aggregated.xlsx')
        
        # 创建Excel写入器
        with pd.ExcelWriter(aggregated_file_path, engine='openpyxl') as writer:
            # Sheet1: 汇总结果
            summary_df.to_excel(writer, sheet_name='汇总结果', index=False)
            
            # 自动调整列宽
            worksheet = writer.sheets['汇总结果']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # 为每个分组生成明细数据Sheet
            # 限制最大Sheet数量，避免文件过大
            max_sheets = 50
            sheet_count = 1  # 已经有了汇总结果Sheet
            
            # 遍历每个分组
            for _, row in summary_df.iterrows():
                if sheet_count >= max_sheets:
                    # 如果超过最大Sheet数，创建一个汇总明细Sheet
                    if sheet_count == max_sheets:
                        all_details = []
                    # 过滤出该分组的明细数据
                    filter_condition = True
                    for col in group_columns:
                        value = row[col]
                        if pd.notna(value):
                            if pd.api.types.is_numeric_dtype(df[col]):
                                # 数值类型，处理浮点数精度
                                filter_condition &= (abs(df[col] - value) < 0.0001)
                            else:
                                # 字符串类型
                                filter_condition &= (df[col].astype(str) == str(value))
                        else:
                            filter_condition &= df[col].isna()
                    
                    # 获取明细数据
                    detail_df = df[filter_condition].copy()
                    
                    if sheet_count == max_sheets:
                        # 添加分组标识列
                        group_info = '_'.join([f'{col}={row[col]}' for col in group_columns])
                        detail_df['分组标识'] = group_info
                        all_details.append(detail_df)
                    else:
                        # 创建单独的Sheet
                        sheet_name = '明细_' + '_'.join([str(row[col])[:10] for col in group_columns])
                        # 处理Sheet名称长度限制
                        sheet_name = sheet_name[:31]  # Excel Sheet名称最大31个字符
                        
                        # 写入明细数据
                        detail_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # 自动调整列宽
                        detail_worksheet = writer.sheets[sheet_name]
                        for column in detail_worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)
                            detail_worksheet.column_dimensions[column_letter].width = adjusted_width
                    
                    sheet_count += 1
            
            # 如果有多个分组被合并到一个Sheet
            if sheet_count > max_sheets:
                combined_df = pd.concat(all_details, ignore_index=True)
                combined_df.to_excel(writer, sheet_name='其他分组明细汇总', index=False)
                
                # 自动调整列宽
                combined_worksheet = writer.sheets['其他分组明细汇总']
                for column in combined_worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    combined_worksheet.column_dimensions[column_letter].width = adjusted_width
        
        aggregated_file = os.path.basename(aggregated_file_path)
        
        return render_template('results.html',
                             filename=filename,
                             stats=stats,
                             preview=preview,
                             charts=charts,
                             aggregated_file=aggregated_file,
                             columns=session_data['columns'],
                             summary_result=html_result)
        
    except Exception as e:
        logger.error(f"汇总数据时出错: {str(e)}")
        flash(f'汇总数据时出错: {str(e)}')
        return redirect(url_for('index'))

@app.route('/development_docs')
def development_docs():
    """开发文档页面"""
    return render_template('development_docs.html')

@app.route('/technical_docs')
def technical_docs():
    """技术协议页面"""
    return render_template('technical_docs.html')

@app.route('/changelog_docs')
def changelog_docs():
    """版本更新公告页面"""
    return render_template('changelog_docs.html')

@app.route('/version_management_docs')
def version_management_docs():
    """版本管理页面"""
    return render_template('version_management_docs.html')

@app.route('/get_details', methods=['POST'])
def get_details():
    """获取汇总分组的明细数据，支持多条件排序功能"""
    filename = request.form['filename']
    group_values_str = request.form['group_values']
    # 获取用户选择的明细列
    detail_columns = request.form.getlist('detail_columns')
    # 获取排序参数，现在支持多条件排序
    sort_columns_str = request.form.get('sort_columns', '')
    sort_directions_str = request.form.get('sort_directions', '')
    meta_file = os.path.join(app.config['UPLOAD_FOLDER'], f'{filename}_meta.json')
    
    try:
        import json
        with open(meta_file, 'r') as f:
            session_data = json.load(f)
        
        filepath = session_data['filepath']
        
        # 获取上次汇总的配置
        if 'last_aggregation' not in session_data:
            return '<p>没有找到汇总配置信息</p>'
        
        group_columns = session_data['last_aggregation']['group_columns']
        
        # 解析分组值
        group_filters = {}
        for group_item in group_values_str.split('|'):
            if ':' in group_item:
                col, value = group_item.split(':', 1)
                # 特殊处理NaN值
                if value != 'NaN':
                    group_filters[col] = value
        
        # 读取文件
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='gbk')
        
        # 应用过滤条件
        filtered_df = df.copy()
        for col, value in group_filters.items():
            if col in filtered_df.columns:
                # 尝试匹配数值类型
                if pd.api.types.is_numeric_dtype(filtered_df[col]):
                    try:
                        value = float(value)
                        filtered_df = filtered_df[filtered_df[col] == value]
                    except:
                        filtered_df = filtered_df[filtered_df[col].astype(str) == value]
                else:
                    # 字符串类型匹配
                    filtered_df = filtered_df[filtered_df[col].astype(str) == value]
        
        # 应用用户选择的列
        if detail_columns:
            # 确保所有选择的列都存在于DataFrame中
            valid_columns = [col for col in detail_columns if col in filtered_df.columns]
            if valid_columns:
                filtered_df = filtered_df[valid_columns]
        
        # 应用多条件排序
        if sort_columns_str:
            try:
                # 解析多条件排序参数
                sort_columns = sort_columns_str.split(',')
                sort_directions = sort_directions_str.split(',') if sort_directions_str else ['asc'] * len(sort_columns)
                
                # 确保排序方向与排序列数量一致
                if len(sort_directions) < len(sort_columns):
                    sort_directions += ['asc'] * (len(sort_columns) - len(sort_directions))
                
                # 构建排序键列表
                sort_keys = []
                for col, direction in zip(sort_columns, sort_directions):
                    if col in filtered_df.columns:
                        ascending = direction.lower() == 'asc'
                        
                        # 尝试处理可能是数值的字符串列
                        if pd.api.types.is_object_dtype(filtered_df[col]):
                            # 尝试转换为数值
                            numeric_series = pd.to_numeric(filtered_df[col], errors='coerce')
                            # 检查是否大部分都能转换为数值
                            if numeric_series.notna().mean() > 0.8:  # 80%以上能转换
                                filtered_df = filtered_df.copy()  # 创建副本避免SettingWithCopyWarning
                                # 排序时使用临时列
                                temp_col_name = f'_temp_sort_{col}'
                                filtered_df[temp_col_name] = numeric_series
                                sort_keys.append((temp_col_name, ascending))
                                # 注意：临时列将在排序后删除
                            else:
                                # 否则按字符串排序
                                sort_keys.append((col, ascending))
                        else:
                            # 已经是数值类型
                            sort_keys.append((col, ascending))
                
                # 执行多条件排序
                if sort_keys:
                    temp_cols_to_drop = [key[0] for key in sort_keys if key[0].startswith('_temp_sort_')]
                    filtered_df = filtered_df.sort_values(by=[key[0] for key in sort_keys], 
                                                         ascending=[key[1] for key in sort_keys])
                    
                    # 删除临时排序列
                    for temp_col in temp_cols_to_drop:
                        if temp_col in filtered_df.columns:
                            filtered_df = filtered_df.drop(temp_col, axis=1)
            except Exception as e:
                logger.warning(f"多条件排序失败: {str(e)}")
                # 排序失败时不影响数据显示，继续执行
        
        # 格式化明细数据为HTML表格
        if len(filtered_df) > 0:
            # 限制显示的行数，避免数据过多
            warning_html = ''
            if len(filtered_df) > 1000:
                warning_html = '<p class="text-warning">数据过多，仅显示前1000行</p>'
                filtered_df = filtered_df.head(1000)
            
            html_table = warning_html + filtered_df.to_html(classes='table table-striped', justify='center', index=False)
            html_table += f'<p>共 {len(filtered_df)} 条明细记录</p>'
            
            # 添加多条件排序信息
            if sort_columns_str:
                sort_info = []
                for col, direction in zip(sort_columns_str.split(','), (sort_directions_str.split(',') if sort_directions_str else ['asc'] * len(sort_columns_str.split(',')))):
                    if col in filtered_df.columns:
                        sort_info.append(f"{col} {"升序" if direction.lower() == "asc" else "降序"}")
                if sort_info:
                    html_table += f'<p>当前排序: {', '.join(sort_info)}</p>'
        else:
            html_table = '<p>没有找到匹配的明细数据</p>'
        
        return html_table
        
    except Exception as e:
        logger.error(f"获取明细数据时出错: {str(e)}")
        return f'<p>加载明细数据时出错: {str(e)}</p>'

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    """清理服务器缓存和临时文件"""
    try:
        logger.info("开始清理服务器缓存")
        
        # 清理上传文件目录
        upload_dir = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'))
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
            logger.info(f'找到 {len(files)} 个文件在上传目录')
            
            # 创建备份目录
            backup_dir = f'uploads_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.makedirs(backup_dir, exist_ok=True)
            
            # 备份并清理文件
            backup_count = 0
            for file in files:
                src = os.path.join(upload_dir, file)
                dst = os.path.join(backup_dir, file)
                if os.path.isfile(src):
                    try:
                        shutil.copy2(src, dst)
                        os.remove(src)
                        backup_count += 1
                        logger.debug(f'已备份并删除: {file}')
                    except Exception as e:
                        logger.warning(f'处理文件 {file} 时出错: {str(e)}')
            
            logger.info(f'已备份并清理 {backup_count} 个上传文件到: {backup_dir}')
        else:
            logger.info('上传目录不存在，跳过清理')
        
        # 清理session缓存目录（如果存在）
        session_dir = 'sessions'
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                os.makedirs(session_dir)
                logger.info('Session缓存已清空')
            except Exception as e:
                logger.warning(f'清理session缓存时出错: {str(e)}')
        
        # 清理临时元数据文件
        meta_files = [f for f in os.listdir('.') if f.endswith('_meta.json')]
        for meta_file in meta_files:
            try:
                os.remove(meta_file)
                logger.debug(f'已删除元数据文件: {meta_file}')
            except Exception as e:
                logger.warning(f'删除元数据文件 {meta_file} 时出错: {str(e)}')
        
        # 清理matplotlib缓存（如果存在）
        try:
            import matplotlib as mpl
            cache_dir = mpl.get_cachedir()
            if cache_dir and os.path.exists(cache_dir):
                # 只清理旧的缓存文件，保留最近1小时的
                current_time = datetime.now()
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    if os.path.isfile(item_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(item_path))
                        if (current_time - file_time).total_seconds() > 3600:  # 1小时前的文件
                            try:
                                os.remove(item_path)
                                logger.debug(f'已清理matplotlib缓存: {item}')
                            except Exception as e:
                                logger.warning(f'清理matplotlib缓存时出错: {str(e)}')
        except Exception as e:
            logger.warning(f'清理matplotlib缓存时出错: {str(e)}')
        
        logger.info('服务器缓存清理完成！')
        
        return jsonify({
            'success': True,
            'message': f'缓存清理成功！已备份并清理 {backup_count if "backup_count" in locals() else 0} 个文件。'
        })
        
    except Exception as e:
        logger.error(f'清理服务器缓存时出错: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'清理缓存失败: {str(e)}'
        })

@app.route('/save_honglian_changes', methods=['POST'])
def save_honglian_changes():
    """保存红莲模式的数据修改"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'modified_data' not in data:
            return jsonify({
                'success': False,
                'message': '未提供修改数据'
            })
        
        modified_data = data['modified_data']
        total_changes = data.get('total_changes', 0)
        new_rows = data.get('new_rows', [])
        total_new_rows = data.get('total_new_rows', 0)
        
        if not modified_data and not new_rows:
            return jsonify({
                'success': False,
                'message': '没有检测到任何修改或新数据'
            })
        
        logger.info(f"开始保存红莲模式数据修改，共 {total_changes} 处修改，{total_new_rows} 条新数据")
        
        # 获取当前的红莲模式数据
        if 'data' not in session:
            return jsonify({
                'success': False,
                'message': '会话中未找到原始数据，请重新上传文件'
            })
        
        # 从session获取原始数据
        original_data = session['data']
        
        # 创建数据副本进行修改
        updated_data = []
        modification_log = []
        
        # 遍历原始数据并应用修改
        for row_idx, row in enumerate(original_data):
            row_str = str(row_idx)
            
            if row_str in modified_data:
                # 这一行有修改，创建副本
                updated_row = row.copy()
                
                # 应用这一行的所有修改
                for column, change_info in modified_data[row_str].items():
                    old_value = change_info['oldValue']
                    new_value = change_info['newValue']
                    
                    # 记录修改日志
                    modification_log.append({
                        'row_index': row_idx,
                        'column': column,
                        'old_value': old_value,
                        'new_value': new_value,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    # 应用修改到数据行
                    if column in updated_row:
                        updated_row[column] = new_value
                        logger.debug(f"修改行 {row_idx} 的 {column}: {old_value} -> {new_value}")
                
                updated_data.append(updated_row)
            else:
                # 这一行没有修改，保持原样
                updated_data.append(row)
        
        # 添加新行数据
        if new_rows:
            for new_row_data in new_rows:
                # 验证新行数据
                if not new_row_data or not isinstance(new_row_data, dict):
                    logger.warning(f"跳过无效的新行数据: {new_row_data}")
                    continue
                
                # 添加新行到数据末尾
                updated_data.append(new_row_data)
                
                # 记录新行添加日志
                modification_log.append({
                    'row_index': len(updated_data) - 1,
                    'column': 'NEW_ROW',
                    'old_value': '',
                    'new_value': str(new_row_data),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                logger.info(f"添加新行数据: {new_row_data}")
        
        # 保存修改后的数据到session
        session['data'] = updated_data
        
        # 记录修改历史（可选）
        if 'modification_history' not in session:
            session['modification_history'] = []
        
        session['modification_history'].append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_changes': total_changes,
            'total_new_rows': total_new_rows,
            'modifications': modification_log
        })
        
        logger.info(f"红莲模式数据修改保存成功，共修改了 {total_changes} 处数据，添加了 {total_new_rows} 条新数据")
        
        return jsonify({
            'success': True,
            'message': f'成功保存 {total_changes} 处修改，添加 {total_new_rows} 条新数据',
            'modification_count': total_changes,
            'new_rows_count': total_new_rows
        })
        
    except Exception as e:
        logger.error(f"保存红莲模式数据修改时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存修改失败: {str(e)}'
        })


@app.route('/employee_management_system')
def employee_management_system():
    """工时管理系统Web界面入口"""
    return redirect('/employee_management')
