#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际的send_table_data_to_dingtalk函数行为
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

# 模拟send_dingtalk_message函数
def mock_send_dingtalk_message(content, message_type, title):
    print(f"\n{'='*60}")
    print(f"模拟发送钉钉消息:")
    print(f"标题: {title}")
    print(f"类型: {message_type}")
    print(f"内容长度: {len(content)}字符")
    print(f"\n消息内容:")
    print(content)
    print(f"{'='*60}")
    return {"errcode": 0, "errmsg": "ok"}

# 导入实际的函数
from dingtalk_robot import send_table_data_to_dingtalk

# 替换全局logger和send_dingtalk_message
import dingtalk_robot
dingtalk_robot.logger = MockLogger()
dingtalk_robot.send_dingtalk_message = mock_send_dingtalk_message

# 测试数据 - 模拟真实的数据结构
test_data = [
    {
        '原车间': '五一车间',
        '接收车间': '三二车间',
        '型号': 'D640',
        '批号': 'D640-240501-A001',
        '重量': '100.5',
        '工序': '正极片'
    },
    {
        '原车间': '五一车间',
        '接收车间': '三二车间',
        '型号': 'D640',
        '批号': 'D640-240501-A002',
        '重量': '98.3',
        '工序': '正极片'
    },
    {
        '原车间': '四一车间',
        '接收车间': '五一车间',
        '型号': 'A732',
        '批号': 'A732-240502-B001',
        '重量': '85.7',
        '工序': '负极片'
    }
]

# 测试函数调用
print("开始测试send_table_data_to_dingtalk函数...")

result = send_table_data_to_dingtalk(
    table_data=test_data,
    title="@小艺 红莲模式明细",
    operation="红莲模式 明细",
    file_name="红莲模式明细",
    operation_time_range="2024-05-01 08:00 - 2024-05-01 20:00",
    data_count=len(test_data)
)

print(f"\n函数返回结果: {result}")
print(f"测试完成！")