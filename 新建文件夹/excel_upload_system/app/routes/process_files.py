"""工艺文件管理API路由 - Version 4.0"""
from flask import Blueprint, request, jsonify, render_template, send_file
from app.models.process_files import ProcessFileManager
import io
import pandas as pd
import os
import sys
from datetime import datetime

# 创建蓝图
process_files_bp = Blueprint('process_files', __name__)
__all__ = ['process_files_bp']

process_manager = ProcessFileManager()


# 页面路由
@process_files_bp.route('/', methods=['GET'])
def process_files_page():
    """工艺文件管理页面"""
    return render_template('process_files.html')


# 字段配置API
@process_files_bp.route('/api/fields', methods=['GET'])
def get_fields():
    """获取字段配置"""
    try:
        fields = process_manager.get_fields()
        visible_fields = process_manager.get_visible_fields()
        ui_settings = process_manager.get_ui_settings()
        return jsonify({
            'success': True,
            'data': {
                'all_fields': fields,
                'visible_fields': visible_fields,
                'ui_settings': ui_settings
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/fields/order', methods=['POST'])
def update_field_order():
    """更新字段排序"""
    try:
        data = request.get_json()
        field_keys = data.get('field_keys', [])
        
        result = process_manager.update_field_order(field_keys)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/fields/visibility', methods=['POST'])
def update_field_visibility():
    """更新字段可见性"""
    try:
        data = request.get_json()
        field_key = data.get('field_key')
        visible = data.get('visible', True)
        
        result = process_manager.update_field_visibility(field_key, visible)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/fields', methods=['POST'])
def add_custom_field():
    """添加自定义字段"""
    try:
        data = request.get_json()
        key = data.get('key', '').strip()
        label = data.get('label', '').strip()
        field_type = data.get('type', 'text')
        required = data.get('required', False)
        
        if not key or not label:
            return jsonify({
                'success': False,
                'error': '字段key和标签不能为空'
            }), 400
        
        result = process_manager.add_custom_field(key, label, field_type, required)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/fields/<field_key>', methods=['DELETE'])
def delete_field(field_key):
    """删除字段"""
    try:
        result = process_manager.delete_field(field_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# UI配置API
@process_files_bp.route('/api/ui_settings', methods=['GET'])
def get_ui_settings():
    """获取UI配置"""
    try:
        settings = process_manager.get_ui_settings()
        return jsonify({'success': True, 'data': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@process_files_bp.route('/api/ui_settings', methods=['POST'])
def save_ui_settings():
    """保存UI配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400
        result = process_manager.save_ui_settings(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# 记录管理API
@process_files_bp.route('/api/records', methods=['GET'])
def get_records():
    """获取工艺文件记录"""
    try:
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        filters_json = request.args.get('filters', '{}')
        
        # 解析筛选参数
        filters = {}
        if filters_json:
            try:
                import json
                filters = json.loads(filters_json)
            except:
                pass
        
        records = process_manager.get_records(search, sort_by, sort_order, filters)
        return jsonify({
            'success': True,
            'data': records,
            'total': len(records)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/records/<record_id>', methods=['GET'])
def get_record(record_id):
    """获取单条记录"""
    try:
        record = process_manager.get_record_by_id(record_id)
        if record:
            return jsonify({
                'success': True,
                'data': record
            })
        return jsonify({
            'success': False,
            'error': '记录不存在'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/records', methods=['POST'])
def add_record():
    """添加记录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        result = process_manager.add_record(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/records/<record_id>', methods=['PUT'])
def update_record(record_id):
    """更新记录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        result = process_manager.update_record(record_id, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@process_files_bp.route('/api/records/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除记录"""
    try:
        result = process_manager.delete_record(record_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 导出API
@process_files_bp.route('/api/export', methods=['POST'])
def export_records():
    """导出记录为Excel"""
    try:
        data = request.get_json() or {}
        record_ids = data.get('record_ids', None)
        
        export_data = process_manager.export_records(record_ids)
        
        if not export_data:
            return jsonify({
                'success': False,
                'error': '没有数据可导出'
            }), 400
        
        # 创建DataFrame
        df = pd.DataFrame(export_data)
        
        # 生成Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='工艺文件', index=False)
        
        output.seek(0)
        
        filename = f'工艺文件_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 批量操作API
@process_files_bp.route('/api/records/batch', methods=['DELETE'])
def batch_delete():
    """批量删除记录"""
    try:
        data = request.get_json()
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return jsonify({
                'success': False,
                'error': '请选择要删除的记录'
            }), 400
        
        success_count = 0
        failed_ids = []
        
        for record_id in record_ids:
            result = process_manager.delete_record(record_id)
            if result['success']:
                success_count += 1
            else:
                failed_ids.append(record_id)
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {success_count} 条记录' + (f'，{len(failed_ids)} 条失败' if failed_ids else ''),
            'success_count': success_count,
            'failed_ids': failed_ids
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 分享到钉钉API
@process_files_bp.route('/api/share_to_dingtalk', methods=['POST'])
def share_to_dingtalk():
    """分享工艺文件数据到钉钉"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'errcode': 400, 'errmsg': '请求体为空'})
        
        operation = data.get('operation', '工艺文件分享')
        table_data = data.get('table_data', None)
        
        # 如果前端没有传来数据，则按ID获取
        if not table_data:
            record_ids = data.get('record_ids', None)
            if record_ids:
                records = []
                for record_id in record_ids:
                    record = process_manager.get_record_by_id(record_id)
                    if record:
                        records.append(record)
                table_data = records
            else:
                table_data = process_manager.get_records()
        
        if not table_data:
            return jsonify({'errcode': 400, 'errmsg': '没有数据可分享'})
        
        # 导入钉钉机器人发送函数
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from dingtalk_robot import send_process_files_to_dingtalk
        
        # 获取字段配置
        fields = process_manager.get_fields()
        
        # 使用专门的工艺文件发送函数
        result = send_process_files_to_dingtalk(
            table_data=table_data,
            fields=fields,
            operation=operation,
            file_name="工艺文件数据",
            operation_time_range=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data_count=len(table_data)
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'errcode': 500, 'errmsg': str(e)})
