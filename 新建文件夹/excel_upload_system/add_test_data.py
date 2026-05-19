#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
员工工装系统测试数据生成脚本
用于添加演示数据来测试系统功能
"""

import json
import os
import sys
from datetime import datetime, timedelta
import random

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def add_test_data():
    """添加测试数据到员工工装系统"""
    
    # 数据文件路径
    data_file = os.path.join(project_root, 'data', 'employee_uniforms.json')
    
    # 确保数据文件存在
    if not os.path.exists(data_file):
        print("错误：数据文件不存在")
        return False
    
    try:
        # 读取现有数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否有足够的员工和工装类型
        if len(data['employees']) < 3 or len(data['uniform_types']) < 2:
            print("错误：需要至少3个员工和2个工装类型才能添加测试数据")
            return False
        
        # 获取员工和工装类型
        employees = data['employees']
        uniform_types = data['uniform_types']
        
        # 添加测试领取记录
        test_records = []
        
        # 为每个员工添加一些领取记录
        for employee in employees:
            employee_id = employee['employee_id']
            employee_name = employee['name']
            
            # 随机选择1-3种工装类型
            selected_types = random.sample(uniform_types, min(len(uniform_types), random.randint(1, 3)))
            
            for uniform_type in selected_types:
                # 生成随机日期（过去6个月内）
                days_ago = random.randint(0, 180)
                issue_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                
                record = {
                    'id': f"test_{employee_id}_{uniform_type['id']}_{days_ago}",
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'uniform_type_id': uniform_type['id'],
                    'uniform_type_name': uniform_type['name'],
                    'issue_date': issue_date,
                    'recorded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                test_records.append(record)
        
        # 添加测试记录到数据
        data['uniform_records'] = test_records
        
        # 保存数据
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功添加 {len(test_records)} 条测试领取记录")
        print("📊 数据统计：")
        print(f"   员工数量：{len(employees)}")
        print(f"   工装类型：{len(uniform_types)}")
        print(f"   领取记录：{len(test_records)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 添加测试数据失败：{str(e)}")
        return False

def remove_test_data():
    """移除测试数据"""
    
    data_file = os.path.join(project_root, 'data', 'employee_uniforms.json')
    
    if not os.path.exists(data_file):
        print("数据文件不存在")
        return False
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 移除所有测试记录（以test_开头的记录）
        original_count = len(data['uniform_records'])
        data['uniform_records'] = [r for r in data['uniform_records'] if not r['id'].startswith('test_')]
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        removed_count = original_count - len(data['uniform_records'])
        print(f"✅ 成功移除 {removed_count} 条测试记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 移除测试数据失败：{str(e)}")
        return False

def show_data_stats():
    """显示数据统计信息"""
    
    data_file = os.path.join(project_root, 'data', 'employee_uniforms.json')
    
    if not os.path.exists(data_file):
        print("数据文件不存在")
        return
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📊 当前数据统计：")
        print(f"   员工数量：{len(data['employees'])}")
        print(f"   工装类型：{len(data['uniform_types'])}")
        print(f"   领取记录：{len(data['uniform_records'])}")
        
        # 显示员工列表
        print("\n👥 员工列表：")
        for emp in data['employees']:
            print(f"   {emp['employee_id']} - {emp['name']}")
        
        # 显示工装类型
        print("\n👕 工装类型：")
        for ut in data['uniform_types']:
            print(f"   {ut['name']} - {ut.get('description', '无描述')}")
        
        # 显示最近的领取记录
        if data['uniform_records']:
            print("\n📋 最近的领取记录：")
            recent_records = sorted(data['uniform_records'], key=lambda x: x['issue_date'], reverse=True)[:5]
            for record in recent_records:
                print(f"   {record['employee_name']} - {record['uniform_type_name']} ({record['issue_date']})")
        
    except Exception as e:
        print(f"❌ 读取数据失败：{str(e)}")

if __name__ == "__main__":
    print("员工工装系统测试数据管理工具")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "add":
            add_test_data()
        elif command == "remove":
            remove_test_data()
        elif command == "stats":
            show_data_stats()
        else:
            print("用法：")
            print("  python add_test_data.py add     - 添加测试数据")
            print("  python add_test_data.py remove  - 移除测试数据")
            print("  python add_test_data.py stats   - 显示数据统计")
    else:
        print("请指定操作：")
        print("  add    - 添加测试数据")
        print("  remove - 移除测试数据")
        print("  stats  - 显示数据统计")
        print("\n例如：python add_test_data.py stats")