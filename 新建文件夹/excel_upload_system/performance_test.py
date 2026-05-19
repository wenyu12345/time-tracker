import time
import requests
import threading
import os
import pandas as pd
from datetime import datetime

# 测试配置
TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), 'test_large_file.xlsx')
TEST_URL = 'http://127.0.0.1:2006/process'
CONCURRENT_REQUESTS = 5

# 创建测试文件
def create_test_file():
    """创建测试文件"""
    print("创建测试文件...")
    # 创建一个大型测试文件
    data = {
        '日期': pd.date_range('2025-01-01', periods=10000),
        '班次': ['白班', '夜班'] * 5000,
        '产品型号': ['A732正极片', 'A730负极片', 'D640负极片', 'D652正极片'] * 2500,
        '工序名称': ['涂布', '辊压', '分切', '叠片'] * 2500,
        '良品数(kg)': range(10000),
        '报废数(kg)': range(10000)[:10000]
    }
    df = pd.DataFrame(data)
    df.to_excel(TEST_FILE_PATH, index=False)
    print(f"测试文件创建完成: {TEST_FILE_PATH}")
    print(f"文件大小: {os.path.getsize(TEST_FILE_PATH) / 1024 / 1024:.2f} MB")
    print(f"数据行数: {len(df)}")

# 测试文件处理速度
def test_file_processing_speed():
    """测试文件处理速度"""
    print("\n测试文件处理速度...")
    start_time = time.time()
    
    # 发送文件上传请求
    with open(TEST_FILE_PATH, 'rb') as f:
        files = {'file': f}
        data = {'mode': 'normal'}
        response = requests.post(TEST_URL, files=files, data=data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"文件处理时间: {processing_time:.2f} 秒")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容长度: {len(response.text)} 字节")
    
    return processing_time

# 测试并发处理能力
def test_concurrent_processing():
    """测试并发处理能力"""
    print(f"\n测试并发处理能力 ({CONCURRENT_REQUESTS} 个并发请求)...")
    start_time = time.time()
    
    def send_request():
        """发送单个请求"""
        try:
            with open(TEST_FILE_PATH, 'rb') as f:
                files = {'file': f}
                data = {'mode': 'normal'}
                response = requests.post(TEST_URL, files=files, data=data, timeout=60)
            return response.status_code
        except Exception as e:
            print(f"请求失败: {str(e)}")
            return 500
    
    # 创建并发请求
    threads = []
    results = []
    
    for i in range(CONCURRENT_REQUESTS):
        thread = threading.Thread(target=lambda i: results.append(send_request()), args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有请求完成
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"并发处理时间: {total_time:.2f} 秒")
    print(f"平均处理时间: {total_time / CONCURRENT_REQUESTS:.2f} 秒/请求")
    print(f"成功请求数: {results.count(200)}")
    print(f"失败请求数: {len(results) - results.count(200)}")
    
    return total_time

# 主测试函数
def main():
    """主测试函数"""
    print("=== Excel数据上传系统性能测试 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建测试文件
    create_test_file()
    
    # 测试文件处理速度
    processing_time = test_file_processing_speed()
    
    # 测试并发处理能力
    concurrent_time = test_concurrent_processing()
    
    # 清理测试文件
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)
        print(f"\n测试文件已清理: {TEST_FILE_PATH}")
    
    print("\n=== 性能测试结果 ===")
    print(f"文件处理速度: {processing_time:.2f} 秒")
    print(f"并发处理时间: {concurrent_time:.2f} 秒")
    print(f"平均并发处理时间: {concurrent_time / CONCURRENT_REQUESTS:.2f} 秒/请求")
    print("=== 测试完成 ===")

if __name__ == '__main__':
    main()
