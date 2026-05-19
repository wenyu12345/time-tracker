#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卷重量和卷径计算功能
"""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import math

# 创建蓝图
coil_calculator_bp = Blueprint('coil_calculator', __name__)

# 数据文件路径
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'coil_models.json')


def load_coil_models():
    """加载卷型号数据"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'models': []}


def save_coil_models(data):
    """保存卷型号数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def calculate_weight(core_diameter, max_diameter, max_weight, current_diameter):
    """根据卷径计算重量
    
    Args:
        core_diameter: 卷筒直径
        max_diameter: 大卷径
        max_weight: 大卷重量
        current_diameter: 当前卷径
    
    Returns:
        当前重量
    """
    # 计算半径
    core_radius = core_diameter / 2
    max_radius = max_diameter / 2
    current_radius = current_diameter / 2
    
    # 计算圆环面积
    max_area = math.pi * (max_radius ** 2 - core_radius ** 2)
    current_area = math.pi * (current_radius ** 2 - core_radius ** 2)
    
    # 计算重量比例
    weight_ratio = current_area / max_area
    current_weight = max_weight * weight_ratio
    
    return current_weight


def calculate_diameter(core_diameter, max_diameter, max_weight, current_weight):
    """根据重量计算卷径
    
    Args:
        core_diameter: 卷筒直径
        max_diameter: 大卷径
        max_weight: 大卷重量
        current_weight: 当前重量
    
    Returns:
        当前卷径
    """
    # 计算半径
    core_radius = core_diameter / 2
    max_radius = max_diameter / 2
    
    # 计算圆环面积
    max_area = math.pi * (max_radius ** 2 - core_radius ** 2)
    
    # 计算当前面积
    current_area = max_area * (current_weight / max_weight)
    
    # 计算当前半径
    current_radius_squared = (current_area / math.pi) + (core_radius ** 2)
    current_radius = math.sqrt(current_radius_squared)
    
    return current_radius * 2


@coil_calculator_bp.route('/coil_calculator')
def coil_calculator():
    """卷重量卷径计算页面"""
    return render_template('coil_calculator.html')


def save_coil_models(data):
    """保存卷型号数据"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存卷型号数据失败: {str(e)}")
        return False


@coil_calculator_bp.route('/get_coil_models', methods=['GET'])
def get_coil_models():
    """获取所有卷型号"""
    data = load_coil_models()
    return jsonify(data)


@coil_calculator_bp.route('/save_coil_model', methods=['POST'])
def save_coil_model():
    """保存卷型号"""
    try:
        # 检查请求数据
        if not request.is_json:
            return jsonify({'success': False, 'error': '请求数据必须是JSON格式'})
        
        model_data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'core_diameter', 'max_diameter', 'max_weight']
        for field in required_fields:
            if field not in model_data:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        data = load_coil_models()
        
        # 生成唯一ID
        if not model_data.get('id'):
            # 查找最大ID并加1
            max_id = 0
            for model in data['models']:
                if model['id'].startswith('model'):
                    try:
                        model_id = int(model['id'][5:])
                        if model_id > max_id:
                            max_id = model_id
                    except ValueError:
                        pass
            model_data['id'] = f'model{max_id + 1}'
        
        # 检查是否已存在
        existing_index = None
        for i, model in enumerate(data['models']):
            if model['id'] == model_data['id']:
                existing_index = i
                break
        
        # 更新或添加
        if existing_index is not None:
            data['models'][existing_index] = model_data
        else:
            data['models'].append(model_data)
        
        # 保存数据
        if save_coil_models(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '保存数据失败'})
    except Exception as e:
        print(f"保存卷型号失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'服务器内部错误: {str(e)}'})


@coil_calculator_bp.route('/delete_coil_model', methods=['POST'])
def delete_coil_model():
    """删除卷型号"""
    model_id = request.get_json().get('id')
    data = load_coil_models()
    
    # 删除型号
    data['models'] = [model for model in data['models'] if model['id'] != model_id]
    
    save_coil_models(data)
    return jsonify({'success': True})


@coil_calculator_bp.route('/calculate_coil', methods=['POST'])
def calculate_coil():
    """计算卷径或重量"""
    calc_data = request.get_json()
    
    model_id = calc_data.get('model_id')
    input_type = calc_data.get('input_type')  # 'diameter' 或 'weight'
    input_value = calc_data.get('input_value')
    
    # 加载数据
    data = load_coil_models()
    model = next((m for m in data['models'] if m['id'] == model_id), None)
    
    if not model:
        return jsonify({'success': False, 'error': '型号不存在'})
    
    try:
        if input_type == 'diameter':
            # 根据卷径计算重量
            weight = calculate_weight(
                model['core_diameter'],
                model['max_diameter'],
                model['max_weight'],
                input_value
            )
            return jsonify({
                'success': True,
                'result': {
                    'type': 'weight',
                    'value': round(weight, 2),
                    'unit': 'kg'
                }
            })
        elif input_type == 'weight':
            # 根据重量计算卷径
            diameter = calculate_diameter(
                model['core_diameter'],
                model['max_diameter'],
                model['max_weight'],
                input_value
            )
            return jsonify({
                'success': True,
                'result': {
                    'type': 'diameter',
                    'value': round(diameter, 2),
                    'unit': 'mm'
                }
            })
        else:
            return jsonify({'success': False, 'error': '无效的输入类型'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
