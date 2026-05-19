#!/usr/bin/env python3
import sys
sys.path.append('.')
from app.utils.csv_data_processor import CSVDataProcessor

processor = CSVDataProcessor()
result = processor.process_file('test_real_two_row.csv')

print('处理器结果:')
print(f'成功: {result.get("success")}')
print(f'字段映射: {len(result.get("header_info", {}).get("field_mapping", {}))} 个')
print(f'不良项映射: {len(result.get("header_info", {}).get("defect_mapping", {}))} 个')

# 检查序列化
from app.utils.utilities import safe_json_serialize
header_info = result.get("header_info", {})
serialized = safe_json_serialize(header_info)
print(f'序列化后字段映射数量: {len(serialized.get("field_mapping", {}))} 个')

# 打印具体的映射内容
print('字段映射内容:')
field_mapping = serialized.get("field_mapping", {})
for key, value in field_mapping.items():
    print(f'  {key} -> {value}')