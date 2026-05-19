#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel上传分析系统 - 部署测试与验证脚本

用途：在腾讯云服务器部署完成后，验证系统的可访问性、功能完整性和性能
使用方法：python DEPLOYMENT_TESTS.py [--host HOST] [--port PORT] [--timeout TIMEOUT]

测试内容包括：
1. 服务健康检查 - 验证服务是否正常运行
2. 功能测试 - 测试核心功能是否正常工作
3. 性能测试 - 测量系统响应时间和吞吐量
4. 错误处理测试 - 验证系统对异常情况的处理
"""

import os
import sys
import json
import time
import argparse
import requests
import logging
import threading
import queue
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deployment_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('deployment_tests')

class ExcelUploadTestSuite:
    """Excel上传系统测试套件"""
    
    def __init__(self, host='localhost', port=5000, timeout=30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.test_results = {
            'start_time': datetime.now(),
            'end_time': None,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }
        self.test_excel_file = self._create_test_excel()
    
    def _create_test_excel(self):
        """创建测试用Excel文件"""
        try:
            # 创建临时目录
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_test')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 创建测试数据
            data = {
                '型号': ['A732正极片', 'A730负极片', None, 'D640正极片'],
                '工序': ['涂布', '辊压', '分切', '模切'],
                '批号': ['466123', '505456', '467789', 'A44001'],
                '重量': [10.5, 8.3, 12.7, 9.1],
                '原车间': ['B4_五一车间(正极)', 'C3_三车间(负极)', 'A1_二车间(正极)', 'D2_四车间(正极)'],
                '接收车间': ['E5_六车间(装配)', 'F6_七车间(包装)', 'G7_八车间(测试)', 'H8_九车间(入库)']
            }
            
            df = pd.DataFrame(data)
            
            # 保存为Excel文件
            file_path = os.path.join(temp_dir, 'test_excel_file.xlsx')
            df.to_excel(file_path, index=False)
            
            logger.info(f"已创建测试Excel文件: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"创建测试Excel文件失败: {str(e)}")
            return None
    
    def run_test(self, test_name, test_func, *args, **kwargs):
        """运行单个测试并记录结果"""
        self.test_results['tests_run'] += 1
        test_start = time.time()
        
        try:
            logger.info(f"开始测试: {test_name}")
            result = test_func(*args, **kwargs)
            
            test_duration = time.time() - test_start
            
            if result:
                self.test_results['tests_passed'] += 1
                status = "通过"
                error_msg = None
                logger.info(f"测试通过: {test_name} (耗时: {test_duration:.2f}s)")
            else:
                self.test_results['tests_failed'] += 1
                status = "失败"
                error_msg = "测试未返回预期结果"
                logger.error(f"测试失败: {test_name} (耗时: {test_duration:.2f}s)")
                
        except Exception as e:
            self.test_results['tests_failed'] += 1
            test_duration = time.time() - test_start
            status = "异常"
            error_msg = str(e)
            logger.error(f"测试异常: {test_name} - {str(e)} (耗时: {test_duration:.2f}s)")
        
        # 记录测试详情
        self.test_results['test_details'].append({
            'name': test_name,
            'status': status,
            'duration': test_duration,
            'error': error_msg
        })
        
        return status == "通过"
    
    def test_health_check(self):
        """测试1: 服务健康检查"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False
    
    def test_model_mapping_page(self):
        """测试2: 型号映射页面访问"""
        try:
            response = requests.get(f"{self.base_url}/manage_model_mapping", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"型号映射页面访问失败: {str(e)}")
            return False
    
    def test_file_upload(self):
        """测试3: 文件上传功能"""
        if not self.test_excel_file:
            logger.error("测试文件不存在，跳过文件上传测试")
            return False
        
        try:
            # 测试普通模式上传
            with open(self.test_excel_file, 'rb') as f:
                files = {'file': ('test_file.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data={'mode': 'normal'},
                    timeout=self.timeout
                )
            
            return response.status_code in [200, 302]  # 200成功，302重定向
        except Exception as e:
            logger.error(f"文件上传测试失败: {str(e)}")
            return False
    
    def test_honglian_mode(self):
        """测试4: 开红莲模式"""
        if not self.test_excel_file:
            logger.error("测试文件不存在，跳开过红莲模式测试")
            return False
        
        try:
            # 测试开红莲模式上传
            with open(self.test_excel_file, 'rb') as f:
                files = {'file': ('test_file.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data={'mode': 'honglian'},
                    timeout=self.timeout
                )
            
            return response.status_code in [200, 302]
        except Exception as e:
            logger.error(f"开红莲模式测试失败: {str(e)}")
            return False
    
    def test_json_api(self):
        """测试5: JSON API响应"""
        try:
            # 测试切换自定义映射API
            response = requests.post(
                f"{self.base_url}/toggle_custom_mapping",
                json={'enabled': True},
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return False
                
            try:
                data = response.json()
                return isinstance(data, dict) and 'success' in data
            except:
                return False
                
        except Exception as e:
            logger.error(f"JSON API测试失败: {str(e)}")
            return False
    
    def test_error_handling(self):
        """测试6: 错误处理"""
        try:
            # 测试上传不支持的文件类型
            with open(__file__, 'rb') as f:
                files = {'file': ('test.py', f, 'text/x-python')}
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data={'mode': 'normal'},
                    timeout=self.timeout
                )
            
            # 应该返回错误，但不能崩溃
            return response.status_code in [200, 400]  # 200可能是显示错误页面，400是直接返回错误
        except Exception as e:
            logger.error(f"错误处理测试失败: {str(e)}")
            return False
    
    def test_performance(self, num_requests=10, concurrency=3):
        """测试7: 性能测试"""
        try:
            response_times = []
            success_count = 0
            
            def make_request():
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}/", timeout=self.timeout)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        nonlocal success_count
                        success_count += 1
                        return end_time - start_time
                    return None
                except Exception:
                    return None
            
            # 并发请求
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                results = list(executor.map(lambda _: make_request(), range(num_requests)))
            
            # 收集成功的响应时间
            response_times = [t for t in results if t is not None]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                logger.info(f"性能测试结果:")
                logger.info(f"  请求总数: {num_requests}")
                logger.info(f"  成功请求: {success_count}")
                logger.info(f"  平均响应时间: {avg_response_time:.4f}s")
                logger.info(f"  最大响应时间: {max_response_time:.4f}s")
                logger.info(f"  最小响应时间: {min_response_time:.4f}s")
                
                # 成功率90%以上且平均响应时间小于1秒为通过
                success_rate = success_count / num_requests
                return success_rate >= 0.9 and avg_response_time < 1.0
            else:
                logger.error("性能测试无成功响应")
                return False
                
        except Exception as e:
            logger.error(f"性能测试失败: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info(f"开始运行测试套件，目标服务: {self.base_url}")
        
        # 运行测试
        self.run_test("服务健康检查", self.test_health_check)
        self.run_test("型号映射页面访问", self.test_model_mapping_page)
        self.run_test("文件上传功能", self.test_file_upload)
        self.run_test("开红莲模式", self.test_honglian_mode)
        self.run_test("JSON API响应", self.test_json_api)
        self.run_test("错误处理", self.test_error_handling)
        self.run_test("性能测试", self.test_performance)
        
        # 完成测试
        self.test_results['end_time'] = datetime.now()
        self._generate_report()
        
        # 清理测试文件
        if self.test_excel_file and os.path.exists(self.test_excel_file):
            try:
                os.remove(self.test_excel_file)
                os.rmdir(os.path.dirname(self.test_excel_file))
                logger.info(f"已清理测试文件")
            except:
                pass
        
        # 返回是否所有测试都通过
        return self.test_results['tests_failed'] == 0
    
    def _generate_report(self):
        """生成测试报告"""
        total_duration = (self.test_results['end_time'] - self.test_results['start_time']).total_seconds()
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100 if self.test_results['tests_run'] > 0 else 0
        
        logger.info("=" * 60)
        logger.info(f"测试报告 - Excel上传分析系统部署验证")
        logger.info("=" * 60)
        logger.info(f"开始时间: {self.test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"结束时间: {self.test_results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"总耗时: {total_duration:.2f}秒")
        logger.info(f"测试总数: {self.test_results['tests_run']}")
        logger.info(f"通过测试: {self.test_results['tests_passed']}")
        logger.info(f"失败测试: {self.test_results['tests_failed']}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info("-" * 60)
        
        # 详细测试结果
        logger.info("详细测试结果:")
        for test in self.test_results['test_details']:
            status_color = "✓ 通过" if test['status'] == "通过" else "✗ 失败"
            if test['status'] == "异常":
                status_color = "! 异常"
            
            logger.info(f"[{test['name']}] - {status_color} - {test['duration']:.2f}秒")
            if test['error']:
                logger.info(f"  错误信息: {test['error']}")
        
        logger.info("=" * 60)
        
        # 生成HTML报告
        self._generate_html_report()
        
        # 返回总体结果
        if success_rate == 100:
            logger.info("🎉 所有测试通过！系统部署成功！")
        elif success_rate >= 80:
            logger.warning("⚠️  大部分测试通过，但有个别测试失败。请检查系统配置。")
        else:
            logger.error("❌ 多个测试失败！系统部署可能存在严重问题，请检查。")
    
    def _generate_html_report(self):
        """生成HTML测试报告"""
        try:
            report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
            os.makedirs(report_dir, exist_ok=True)
            
            report_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = os.path.join(report_dir, f"test_report_{report_time}.html")
            
            # HTML模板
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excel上传分析系统 - 部署测试报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .summary-item {{
            display: inline-block;
            margin-right: 30px;
            margin-bottom: 10px;
        }}
        .summary-label {{
            font-weight: bold;
            color: #666;
        }}
        .summary-value {{
            font-size: 18px;
            font-weight: bold;
            margin-left: 5px;
        }}
        .success {{
            color: #27ae60;
        }}
        .warning {{
            color: #f39c12;
        }}
        .danger {{
            color: #e74c3c;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-passed {{
            background-color: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .status-failed {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .status-error {{
            background-color: #fff3cd;
            color: #856404;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .error-message {{
            color: #e74c3c;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Excel上传分析系统 - 部署测试报告</h1>
        
        <div class="summary">
            <div class="summary-item">
                <span class="summary-label">测试时间:</span>
                <span class="summary-value">{self.test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">服务地址:</span>
                <span class="summary-value">{self.base_url}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">测试总数:</span>
                <span class="summary-value">{self.test_results['tests_run']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">通过:</span>
                <span class="summary-value success">{self.test_results['tests_passed']}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">失败:</span>
                <span class="summary-value {"danger" if self.test_results['tests_failed'] > 0 else "success"}">{
                    self.test_results['tests_failed']
                }</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">成功率:</span>
                <span class="summary-value {"success" if success_rate == 100 else "warning" if success_rate >= 80 else "danger"}">{
                    f"{success_rate:.1f}%"
                }</span>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>测试项目</th>
                    <th>状态</th>
                    <th>耗时 (秒)</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
        """
            
            # 添加测试结果行
            for test in self.test_results['test_details']:
                status_class = "status-passed" if test['status'] == "通过" else "status-failed" if test['status'] == "失败" else "status-error"
                status_text = "通过" if test['status'] == "通过" else "失败" if test['status'] == "失败" else "异常"
                error_message = test['error'] if test['error'] else "-"
                
                html_content += f"""
                <tr>
                    <td>{test['name']}</td>
                    <td><span class="{status_class}">{status_text}</span></td>
                    <td>{test['duration']:.2f}</td>
                    <td class="error-message">{error_message}</td>
                </tr>
                """
            
            # 结束HTML
            html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
        """
            
            # 写入HTML文件
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"已生成HTML测试报告: {report_file}")
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {str(e)}")

# 主函数
def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Excel上传分析系统部署测试脚本')
    parser.add_argument('--host', default='localhost', help='服务主机地址')
    parser.add_argument('--port', type=int, default=5000, help='服务端口')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时时间(秒)')
    args = parser.parse_args()
    
    # 创建测试套件并运行测试
    test_suite = ExcelUploadTestSuite(
        host=args.host,
        port=args.port,
        timeout=args.timeout
    )
    
    # 运行所有测试
    success = test_suite.run_all_tests()
    
    # 根据测试结果设置退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
