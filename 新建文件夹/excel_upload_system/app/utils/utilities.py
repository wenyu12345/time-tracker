import pandas as pd
import numpy as np
import json

def convert_numpy_types(obj):
    """
    递归转换numpy类型为Python基本类型，确保对象可以被JSON序列化
    
    参数:
        obj: 需要转换的对象
        
    返回:
        转换后的可JSON序列化对象
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, (pd.Int64Dtype, pd.Float64Dtype)):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif pd.isna(obj):
        return None
    return obj

def safe_json_serialize(obj):
    """
    安全地序列化对象，处理pandas和numpy类型
    
    参数:
        obj: 需要序列化的对象
        
    返回:
        可JSON序列化的对象
    """
    # 首先转换numpy类型
    converted_obj = convert_numpy_types(obj)
    
    # 确保所有值都可以被JSON序列化
    try:
        # 尝试直接序列化为JSON字符串，验证结果
        json.dumps(converted_obj)
        return converted_obj
    except (TypeError, OverflowError) as e:
        # 如果仍然有问题，进行更深度的处理
        if isinstance(converted_obj, dict):
            for key, value in converted_obj.items():
                try:
                    json.dumps(value)
                except (TypeError, OverflowError):
                    converted_obj[key] = str(value)
        elif isinstance(converted_obj, list):
            for i in range(len(converted_obj)):
                try:
                    json.dumps(converted_obj[i])
                except (TypeError, OverflowError):
                    converted_obj[i] = str(converted_obj[i])
        return converted_obj
