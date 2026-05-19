import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import re
from collections import OrderedDict

class CSVHeaderDetector:
    """CSV文件表头识别器 - 新版本
    专门处理两行固定表头格式：
    第一行：固定的标准表头（日期,班次,产品型号,工序名称,投入数(kg),良品数(kg),报废数(kg)）
    第二行：不良项字段，光箔位置不固定
    """
    
    def __init__(self):
        # 标准表头字段（第一行，固定不变）
        self.standard_headers = [
            '日期', '班次', '产品型号', '工序名称', 
            '投入数(kg)', '良品数(kg)', '报废数(kg)'
        ]
        
        # 不良项字段（第二行，位置不固定）
        self.defect_headers = [
            '光箔*', '单面*', '测片/接带*', '断带*', 
            '打皱*', '错位*', '面密度异常*'
        ]
        
        # 工序排序规则
        self.process_order = {
            '正极双面涂布': 1,
            '负极双面涂布': 2,
            '正极辊压': 3,
            '负极辊压': 4,
            '正极分条': 5,
            '负极分条': 6
        }
    
    def detect_headers(self, file_path: str) -> Dict[str, any]:
        """
        检测CSV文件的表头结构
        专门处理两行固定表头格式
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            包含表头信息的字典
        """
        try:
            # 读取文件前两行
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                raise ValueError("文件行数不足，至少需要两行表头")
            
            # 解析表头
            first_row = [line.strip() for line in lines[0].strip().split(',')]
            second_row = [line.strip() for line in lines[1].strip().split(',')]
            
            # 跳过两行表头，从第三行开始读取数据
            df = pd.read_csv(file_path, skiprows=2, header=None, encoding='utf-8')
            
            # 构建完整的列名：第一行 + 第二行
            column_names = first_row + second_row
            
            # 确保DataFrame列数与表头匹配
            if len(df.columns) < len(column_names):
                # 如果数据列不够，补充缺失列（填充0）
                for i in range(len(column_names) - len(df.columns)):
                    df[len(df.columns)] = 0
            elif len(df.columns) > len(column_names):
                # 如果数据列太多，截取匹配的列数
                df = df.iloc[:, :len(column_names)]
            
            # 设置列名
            df.columns = column_names[:len(df.columns)]
            
            # 构建字段映射
            field_mapping = {}
            for header in self.standard_headers:
                if header in df.columns:
                    field_mapping[header] = header
            
            # 构建不良项映射
            defect_mapping = {}
            for header in self.defect_headers:
                if header in df.columns:
                    defect_mapping[header] = header
            
            return {
                'format': 'two_row_fixed',
                'is_two_row_format': True,
                'data': df,
                'field_mapping': field_mapping,
                'defect_mapping': defect_mapping,
                'has_light_foil': '光箔*' in defect_mapping,
                'light_foil_column': defect_mapping.get('光箔*'),
                'scrap_column': field_mapping.get('报废数(kg)'),
                'columns': list(df.columns),
                'first_row_headers': first_row,
                'second_row_headers': second_row
            }
                
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试GBK编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    lines = f.readlines()
                
                first_row = [line.strip() for line in lines[0].strip().split(',')]
                second_row = [line.strip() for line in lines[1].strip().split(',')]
                
                df = pd.read_csv(file_path, skiprows=2, header=None, encoding='gbk')
                
                column_names = first_row + second_row
                
                if len(df.columns) < len(column_names):
                    for i in range(len(column_names) - len(df.columns)):
                        df[len(df.columns)] = 0
                elif len(df.columns) > len(column_names):
                    df = df.iloc[:, :len(column_names)]
                
                df.columns = column_names[:len(df.columns)]
                
                field_mapping = {}
                for header in self.standard_headers:
                    if header in df.columns:
                        field_mapping[header] = header
                
                defect_mapping = {}
                for header in self.defect_headers:
                    if header in df.columns:
                        defect_mapping[header] = header
                
                return {
                    'format': 'two_row_fixed',
                    'is_two_row_format': True,
                    'data': df,
                    'field_mapping': field_mapping,
                    'defect_mapping': defect_mapping,
                    'has_light_foil': '光箔*' in defect_mapping,
                    'light_foil_column': defect_mapping.get('光箔*'),
                    'scrap_column': field_mapping.get('报废数(kg)'),
                    'columns': list(df.columns),
                    'first_row_headers': first_row,
                    'second_row_headers': second_row
                }
            except Exception as e2:
                raise Exception(f"文件读取失败: {str(e2)}")
        except Exception as e:
            raise Exception(f"表头检测失败: {str(e)}")
    
    def calculate_net_scrap(self, data: pd.DataFrame, scrap_column: str, 
                          light_foil_column: Optional[str] = None) -> pd.Series:
        """
        计算去光箔报废 = 报废 - 光箔
        
        Args:
            data: 数据DataFrame
            scrap_column: 报废数字段名
            light_foil_column: 光箔字段名（可选）
            
        Returns:
            去光箔报废系列
        """
        try:
            # 确保报废列存在
            if scrap_column not in data.columns:
                raise ValueError(f"报废列 '{scrap_column}' 不存在")
            
            scrap_data = pd.to_numeric(data[scrap_column], errors='coerce').fillna(0)
            
            # 如果存在光箔列，计算去光箔报废
            if light_foil_column and light_foil_column in data.columns:
                light_foil_data = pd.to_numeric(data[light_foil_column], errors='coerce').fillna(0)
                net_scrap = scrap_data - light_foil_data
            else:
                # 没有光箔数据，直接使用报废数
                net_scrap = scrap_data
            
            return net_scrap
            
        except Exception as e:
            print(f"计算去光箔报废失败: {str(e)}")
            # 失败时返回原始报废数据
            return pd.to_numeric(data[scrap_column], errors='coerce').fillna(0)
    
    def sort_by_process(self, data: pd.DataFrame, process_column: str) -> pd.DataFrame:
        """
        按工序名称排序：先正极再负极双面涂布、辊压、分条
        
        Args:
            data: 数据DataFrame
            process_column: 工序名称字段
            
        Returns:
            排序后的DataFrame
        """
        try:
            # 添加排序序号
            data['process_order'] = data[process_column].map(self.process_order)
            
            # 对未匹配的工序设置较大的排序值
            data['process_order'] = data['process_order'].fillna(999)
            
            # 按排序序号排序
            data_sorted = data.sort_values('process_order')
            
            # 删除临时排序列
            data_sorted = data_sorted.drop('process_order', axis=1)
            
            return data_sorted
            
        except Exception as e:
            print(f"工序排序失败: {str(e)}")
            return data
    
    def get_available_fields(self, header_info: Dict) -> List[Dict]:
        """
        获取可用于筛选的字段列表
        
        Returns:
            字段列表，每个字段包含名称、类型、是否可用于汇总等信息
        """
        fields = []
        
        # 标准字段
        for field_name, column_name in header_info['field_mapping'].items():
            field_info = {
                'name': field_name,
                'column': column_name,
                'type': 'standard',
                'can_aggregate': field_name in ['投入数(kg)', '良品数(kg)', '报废数(kg)'],
                'selected': True
            }
            fields.append(field_info)
        
        # 不良项字段
        for defect_name, column_name in header_info['defect_mapping'].items():
            field_info = {
                'name': defect_name,
                'column': column_name,
                'type': 'defect',
                'can_aggregate': True,
                'selected': False
            }
            fields.append(field_info)
        
        # 添加计算字段
        fields.append({
            'name': '去光箔报废',
            'column': '去光箔报废',
            'type': 'calculated',
            'can_aggregate': True,
            'selected': True
        })
        
        return fields