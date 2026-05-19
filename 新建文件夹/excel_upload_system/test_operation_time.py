#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试操作时间段提取功能
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from app.routes.main import extract_operation_time_range

# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_operation_time')

def test_operation_time_extraction():
    """测试操作时间提取功能"""
    logger.info("开始测试操作时间提取功能...")
    
    # 测试用例1: 有操作时间列，包含有效时间数据
    logger.info("\n测试用例1: 有操作时间列，包含有效时间数据")
    data1 = {
        '操作时间': [
            '2025-11-01 08:30:00',
            '2025-11-06 10:29:09',
            '2025-11-03 15:45:30'
        ],
        '产品型号': ['D640正极片', 'D640正极片', 'D640正极片'],
        '重量': [388.0, 234.5, 211.0]
    }
    df1 = pd.DataFrame(data1)
    result1 = extract_operation_time_range(df1)
    logger.info(f"测试用例1结果: {result1}")
    assert result1 == '2025-11-01 08:30:00 - 2025-11-06 10:29:09', f"测试用例1失败: {result1}"
    
    # 测试用例2: 有多个时间相关列
    logger.info("\n测试用例2: 有多个时间相关列")
    data2 = {
        '操作时间': [
            '2025-11-01 08:30:00',
            '2025-11-02 10:29:09'
        ],
        '完成时间': [
            '2025-11-03 15:45:30',
            '2025-11-06 18:00:00'
        ],
        '产品型号': ['D640正极片', 'D640正极片']
    }
    df2 = pd.DataFrame(data2)
    result2 = extract_operation_time_range(df2)
    logger.info(f"测试用例2结果: {result2}")
    assert result2 == '2025-11-01 08:30:00 - 2025-11-06 18:00:00', f"测试用例2失败: {result2}"
    
    # 测试用例3: 无时间相关列
    logger.info("\n测试用例3: 无时间相关列")
    data3 = {
        '产品型号': ['D640正极片', 'D640正极片'],
        '重量': [388.0, 234.5]
    }
    df3 = pd.DataFrame(data3)
    result3 = extract_operation_time_range(df3)
    logger.info(f"测试用例3结果: {result3}")
    assert result3 == '无相关时间记录', f"测试用例3失败: {result3}"
    
    # 测试用例4: 有时间列但无有效数据
    logger.info("\n测试用例4: 有时间列但无有效数据")
    data4 = {
        '操作时间': [None, '', 'N/A'],
        '产品型号': ['D640正极片', 'D640正极片', 'D640正极片']
    }
    df4 = pd.DataFrame(data4)
    result4 = extract_operation_time_range(df4)
    logger.info(f"测试用例4结果: {result4}")
    assert result4 == '无相关时间记录', f"测试用例4失败: {result4}"
    
    # 测试用例5: 混合格式的时间数据
    logger.info("\n测试用例5: 混合格式的时间数据")
    data5 = {
        '时间': [
            '2025-11-01',
            '2025/11/06 10:29:09',
            '20251103'
        ],
        '产品型号': ['D640正极片', 'D640正极片', 'D640正极片']
    }
    df5 = pd.DataFrame(data5)
    result5 = extract_operation_time_range(df5)
    logger.info(f"测试用例5结果: {result5}")
    # 这里只检查是否包含正确的日期部分，因为时间格式转换可能会有细微差异
    assert '2025-11-01' in result5 and '2025-11-06' in result5, f"测试用例5失败: {result5}"
    
    logger.info("\n所有测试用例通过！")
    return True

def test_dingtalk_message_format():
    """测试钉钉消息格式（模拟）"""
    logger.info("\n开始测试钉钉消息格式...")
    
    # 模拟操作时间范围
    operation_time_range = '2025-11-01 08:30:00 - 2025-11-06 10:29:09'
    
    # 模拟消息格式
    from dingtalk_robot import send_honglian_notification
    
    # 这里我们不实际发送消息，只检查函数签名是否正确
    import inspect
    sig = inspect.signature(send_honglian_notification)
    assert 'operation_time_range' in sig.parameters, "send_honglian_notification 函数缺少 operation_time_range 参数"
    
    from dingtalk_robot import send_table_data_to_dingtalk
    sig = inspect.signature(send_table_data_to_dingtalk)
    assert 'operation_time_range' in sig.parameters, "send_table_data_to_dingtalk 函数缺少 operation_time_range 参数"
    
    logger.info("钉钉消息格式测试通过！")
    return True

if __name__ == '__main__':
    try:
        # 运行测试
        test_operation_time_extraction()
        test_dingtalk_message_format()
        
        logger.info("\n所有测试都已成功完成！")
        logger.info("\n功能验证总结:")
        logger.info("1. 操作时间提取功能正常工作")
        logger.info("2. 钉钉通知函数已正确更新")
        logger.info("3. 异常处理逻辑完整")
        logger.info("4. 支持多种时间格式和多时间列")
        
    except AssertionError as e:
        logger.error(f"测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
