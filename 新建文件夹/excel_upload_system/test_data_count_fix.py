#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试data_count参数传递修复
"""

import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试函数
def test_data_count_parameter():
    """测试data_count参数是否能正确传递到钉钉消息"""
    
    # 测试URL
    url = "http://localhost:5000/send_to_dingtalk"
    
    # 测试数据 - 包含表格数据和自定义data_count
    test_data = {
        "file_name": "测试文件.xlsx",
        "operation": "测试操作",
        "data_count": 999,  # 自定义数据总数
        "table_data": [
            # 模拟红莲模式数据格式
            {"原车间": "车间A", "接收车间": "车间B", "产品类型": "类型1", "批次号": "BATCH001", "重量": 100.5},
            {"原车间": "车间A", "接收车间": "车间B", "产品类型": "类型1", "批次号": "BATCH002", "重量": 200.3},
            {"原车间": "车间C", "接收车间": "车间D", "产品类型": "类型2", "批次号": "BATCH003", "重量": 150.7}
        ]
    }
    
    try:
        logger.info(f"发送测试请求，data_count={test_data['data_count']}")
        
        # 发送POST请求
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data, ensure_ascii=False)
        )
        
        # 解析响应
        result = response.json()
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应结果: {result}")
        
        # 检查结果
        if result.get('errcode') == 0:
            logger.info("测试成功！钉钉消息发送成功，请注意查看消息中的数据总数是否为999")
        else:
            logger.error(f"测试失败: {result.get('errmsg', '未知错误')}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"请求异常: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
    except Exception as e:
        logger.error(f"发生未知错误: {str(e)}")

if __name__ == "__main__":
    print("开始测试data_count参数传递修复...")
    test_data_count_parameter()
    print("测试完成，请查看日志输出")
