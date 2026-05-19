# 测试send_table_data_to_dingtalk函数行为
import json
import re
from datetime import datetime

# 模拟日志记录器
class Logger:
    def info(self, msg): print(f'[INFO] {msg}')
    def debug(self, msg): print(f'[DEBUG] {msg}')
    def error(self, msg): print(f'[ERROR] {msg}')
    def warning(self, msg): print(f'[WARNING] {msg}')

logger = Logger()

def send_table_data_to_dingtalk(table_data, title='表格数据通知', operation='数据处理', file_name=None, operation_time_range='无相关时间记录', data_count=None):
    print(f'\n=== 开始处理表格数据 ===')
    print(f'数据条数: {len(table_data) if table_data else 0}')
    print(f'标题: {title}')
    print(f'操作: {operation}')
    print(f'文件名: {file_name}')
    
    # 固定标题格式
    title = '@小艺 红莲模式明细'
    
    # 构建消息头部
    markdown_content = f'### {title}\n\n'
    
    # 添加文件名和操作信息
    if file_name:
        markdown_content += f'**文件名:** 红莲模式明细\n'
    markdown_content += f'**操作:** 红莲模式 明细\n'
    markdown_content += f'**处理时间:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
    markdown_content += f'**操作时间段:** {operation_time_range}\n\n'
    
    # 添加二级标题
    markdown_content += '#### 红莲模式明细数据\n\n'
    
    # 按原车间、接收车间和产品类型分组数据
    grouped_data = {}
    
    # 处理表格数据，进行分组
    filtered_count = 0
    for row in table_data:
        if not isinstance(row, dict):
            continue
        
        # 提取必要字段
        original_workshop = None
        receive_workshop = None
        product_type = None
        batch_no = None
        weight = None
        
        for key, value in row.items():
            key_lower = str(key).strip().lower()
            
            if any(keyword in key_lower for keyword in ['原车间', '源车间', 'from']):
                original_workshop = str(value).strip()
                workshop_match = re.search(r'[一二三四五六七八九十百]+车间', original_workshop)
                if workshop_match:
                    original_workshop = workshop_match.group()
            
            elif any(keyword in key_lower for keyword in ['接收车间', '接收', 'receive']):
                receive_workshop = str(value).strip()
                workshop_match = re.search(r'[一二三四五六七八九十百]+车间', receive_workshop)
                if workshop_match:
                    receive_workshop = workshop_match.group()
            
            elif any(keyword in key_lower for keyword in ['型号', 'model', 'type']):
                product_type = str(value).strip()
            
            elif any(keyword in key_lower for keyword in ['批号', '批次号', 'batch', 'lot']):
                batch_no = str(value).strip()
            
            elif any(keyword in key_lower for keyword in ['重量', 'weight', 'kg']):
                weight = str(value).strip()
        
        # 检查是否有批次号（关键字段）
        if batch_no:
            workshop_key = f'{original_workshop or "未知"}-{receive_workshop or "未知"}'
            if workshop_key not in grouped_data:
                grouped_data[workshop_key] = {
                    'original_workshop': original_workshop or '未知',
                    'receive_workshop': receive_workshop or '未知',
                    'products': {}
                }
            
            product_type_key = product_type or '未知型号'
            if product_type_key not in grouped_data[workshop_key]['products']:
                grouped_data[workshop_key]['products'][product_type_key] = []
            
            weight_str = f'{weight}kg' if weight else ''
            grouped_data[workshop_key]['products'][product_type_key].append((batch_no, weight_str))
        else:
            filtered_count += 1
            print(f'[DEBUG] 数据行缺少批次号，被过滤: {row}')
    
    print(f'分组后数据: {len(grouped_data)} 个分组')
    print(f'被过滤数据: {filtered_count} 条')
    
    # 构建内容
    for workshop_key, workshop_data in grouped_data.items():
        original_workshop = workshop_data['original_workshop']
        receive_workshop = workshop_data['receive_workshop']
        products = workshop_data['products']
        
        markdown_content += f'**原车间：{original_workshop}      接收: {receive_workshop}**\n\n'
        
        for product_type, batches in products.items():
            batch_count = len(batches)
            markdown_content += f'\n{"="*50}\n'
            markdown_content += f'**{product_type} 【{batch_count}批】**\n\n'
            
            for i, (batch_no, weight_str) in enumerate(batches, 1):
                markdown_content += f'- 【{i}】{batch_no}, {weight_str}\n'
            
            markdown_content += f'{"="*50}\n'
    
    # 如果没有数据，添加提示信息
    if not grouped_data:
        markdown_content += '暂无符合条件的数据\n'
    
    # 数据总数
    if data_count is None:
        data_count = sum(len(batches) for products in grouped_data.values() for batches in products.values())
    
    markdown_content += f'\n**数据总数**: {data_count} 条\n'
    markdown_content += '\n此消息由系统自动发送'
    
    print(f'\n=== 最终内容长度: {len(markdown_content)} 字符 ===')
    print(f'=== 内容预览 ===')
    print(markdown_content[:500] + '...' if len(markdown_content) > 500 else markdown_content)
    
    return markdown_content

# 测试数据
test_data = [
    {'原车间': '五一车间', '接收车间': '三二车间', '汇总型号': 'D640正极片', '批号': 'A44TCMK12F04_1_2', '重量': 261.0},
    {'原车间': '五一车间', '接收车间': '三二车间', '汇总型号': 'D640正极片', '批号': 'A44TCMK12F05_1_1', '重量': 300.0},
    {'原车间': '四一车间', '接收车间': '五一车间', '汇总型号': 'A732负极片', '批号': '477TAMK11J14_1', '重量': 625.0}
]

result = send_table_data_to_dingtalk(test_data, file_name='红莲模式明细', operation_time_range='2025-11-14 00:00:00 至 2025-11-14 23:59:59')

print(f'\n=== 完整结果 ===')
print(result)