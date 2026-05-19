#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际的send_table_data_to_dingtalk函数行为 - 记录内容长度
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟日志记录器
class MockLogger:
    def debug(self, msg):
        print(f"[DEBUG] {msg}")
    
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")

# 记录内容长度的模拟函数
content_lengths = []

def mock_send_dingtalk_message(content, message_type, title):
    length = len(content)
    content_lengths.append(length)
    print(f"内容长度: {length}字符")
    return {"errcode": 0, "errmsg": "ok"}

# 导入实际的函数
from dingtalk_robot import send_table_data_to_dingtalk

# 替换全局logger和send_dingtalk_message
import dingtalk_robot
dingtalk_robot.logger = MockLogger()
dingtalk_robot.send_dingtalk_message = mock_send_dingtalk_message

# 生成大量测试数据来模拟真实场景
def generate_test_data(count=50):
    """生成指定数量的测试数据"""
    test_data = []
    workshops = [
        ('五一车间', '三二车间'),
        ('四一车间', '五一车间'),
        ('三二车间', '四二车间'),
        ('二一车间', '三二车间')
    ]
    product_types = ['D640', 'A732', 'B855', 'C923', 'E567']
    processes = ['正极片', '负极片', '隔膜', '电解液', '壳体']
    
    for i in range(count):
        original, receive = workshops[i % len(workshops)]
        product_type = product_types[i % len(product_types)]
        process = processes[i % len(processes)]
        
        test_data.append({
            '原车间': original,
            '接收车间': receive,
            '型号': product_type,
            '批号': f"{product_type}-240501-{chr(65 + i % 26)}{i:03d}",
            '重量': str(round(80 + (i % 30) * 1.5, 1)),
            '工序': process
        })
    
    return test_data

# 测试不同数据量的情况
test_cases = [50, 100, 147, 200]

for data_count in test_cases:
    print(f"\n测试数据量: {data_count} 条")
    
    test_data = generate_test_data(data_count)
    
    result = send_table_data_to_dingtalk(
        table_data=test_data,
        title="@小艺 红莲模式明细",
        operation="红莲模式 明细",
        file_name="红莲模式明细",
        operation_time_range="2024-05-01 08:00 - 2024-05-01 20:00",
        data_count=len(test_data)
    )
    
    print(f"返回结果: {result}")

# 总结内容长度
print(f"\n{'='*50}")
print("内容长度统计:")
for i, length in enumerate(content_lengths):
    print(f"数据量 {test_cases[i]}: {length} 字符")
print(f"{'='*50}")