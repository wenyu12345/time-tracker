import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from collections import defaultdict
from app.utils.csv_header_detector import CSVHeaderDetector
from app.utils.utilities import convert_numpy_types, safe_json_serialize
import logging

logger = logging.getLogger(__name__)

class CSVDataProcessor:
    """CSV数据处理服务，支持新的表头识别模式"""
    
    def __init__(self):
        self.header_detector = CSVHeaderDetector()
    
    def process_file(self, file_path: str, filter_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理CSV文件
        
        Args:
            file_path: 文件路径
            filter_config: 筛选配置
            
        Returns:
            处理结果
        """
        try:
            # 1. 检测表头结构
            logger.info(f"开始检测文件表头结构: {file_path}")
            header_info = self.header_detector.detect_headers(file_path)
            
            # 2. 获取数据
            df = header_info['data']
            
            # 3. 数据清洗
            df_cleaned = self._clean_data(df, header_info)
            
            # 4. 计算去光箔报废
            if header_info['scrap_column']:
                net_scrap = self.header_detector.calculate_net_scrap(
                    df_cleaned, 
                    header_info['scrap_column'],
                    header_info['light_foil_column']
                )
                df_cleaned['去光箔报废'] = net_scrap
            
            # 5. 按工序排序
            if '工序名称' in header_info['field_mapping']:
                process_column = header_info['field_mapping']['工序名称']
                df_cleaned = self.header_detector.sort_by_process(df_cleaned, process_column)
            
            # 6. 应用筛选配置
            if filter_config:
                df_filtered = self._apply_filters(df_cleaned, filter_config)
            else:
                df_filtered = df_cleaned
            
            # 7. 生成汇总数据
            summary = self._generate_summary(df_filtered, header_info, filter_config)
            
            # 8. 获取可用字段
            available_fields = self.header_detector.get_available_fields(header_info)
            
            return {
                'success': True,
                'data': safe_json_serialize(df_filtered.to_dict('records')),
                'summary': safe_json_serialize(summary),
                'header_info': safe_json_serialize(header_info),
                'available_fields': safe_json_serialize(available_fields),
                'total_rows': len(df_filtered),
                'original_rows': len(df)
            }
            
        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'summary': None
            }
    
    def _clean_data(self, df: pd.DataFrame, header_info: Dict) -> pd.DataFrame:
        """数据清洗"""
        df_clean = df.copy()
        
        # 转换数值字段
        numeric_fields = ['投入数(kg)', '良品数(kg)', '报废数(kg)']
        for field in numeric_fields:
            if field in header_info['field_mapping']:
                column = header_info['field_mapping'][field]
                if column in df_clean.columns:
                    df_clean[column] = pd.to_numeric(df_clean[column], errors='coerce').fillna(0)
        
        # 转换不良项字段
        if header_info['format'] == 'two_row':
            for defect_name, column in header_info['defect_mapping'].items():
                if column in df_clean.columns:
                    df_clean[column] = pd.to_numeric(df_clean[column], errors='coerce').fillna(0)
        
        # 日期字段处理
        if '日期' in header_info['field_mapping']:
            date_column = header_info['field_mapping']['日期']
            if date_column in df_clean.columns:
                df_clean[date_column] = pd.to_datetime(df_clean[date_column], errors='coerce')
        
        return df_clean
    
    def _apply_filters(self, df: pd.DataFrame, filter_config: Dict, header_info: Dict = None) -> pd.DataFrame:
        """应用筛选配置"""
        df_filtered = df.copy()
        
        # 日期筛选
        if 'date_range' in filter_config:
            date_range = filter_config['date_range']
            date_column = None
            if header_info and '日期' in header_info.get('field_mapping', {}):
                date_column = header_info['field_mapping']['日期']
            elif '日期' in df_filtered.columns:
                date_column = '日期'
                
            if date_column and date_column in df_filtered.columns:
                start_date = pd.to_datetime(date_range.get('start'))
                end_date = pd.to_datetime(date_range.get('end'))
                if start_date:
                    df_filtered = df_filtered[df_filtered[date_column] >= start_date]
                if end_date:
                    df_filtered = df_filtered[df_filtered[date_column] <= end_date]
        
        # 工序筛选
        if 'process_filter' in filter_config:
            processes = filter_config['process_filter']
            process_column = None
            if header_info and '工序名称' in header_info.get('field_mapping', {}):
                process_column = header_info['field_mapping']['工序名称']
            elif '工序名称' in df_filtered.columns:
                process_column = '工序名称'
                
            if process_column and process_column in df_filtered.columns and processes:
                df_filtered = df_filtered[df_filtered[process_column].isin(processes)]
        
        # 班次筛选
        if 'shift_filter' in filter_config:
            shifts = filter_config['shift_filter']
            shift_column = None
            if header_info and '班次' in header_info.get('field_mapping', {}):
                shift_column = header_info['field_mapping']['班次']
            elif '班次' in df_filtered.columns:
                shift_column = '班次'
                
            if shift_column and shift_column in df_filtered.columns and shifts:
                # 如果选择ALL，不过滤班次
                if 'ALL' not in shifts:
                    df_filtered = df_filtered[df_filtered[shift_column].isin(shifts)]
        
        return df_filtered
    
    def calculate_summary(self, df_list: list, selected_fields: list, header_info: Dict) -> Dict:
        """生成汇总数据"""
        summary = {
            'total_records': len(df),
            'group_summaries': {}
        }
        
        # 定义固定的汇总字段
        default_aggregate_fields = ['日期', '班次', '产品型号', '工序名称', '良品数(kg)', '报废数(kg)', '光箔*']
        
        # 获取参与汇总的字段
        aggregate_fields = []
        if filter_config and 'selected_fields' in filter_config:
            selected_fields = filter_config['selected_fields']
            for field_name in default_aggregate_fields:
                # 检查是否被屏蔽
                is_disabled = False
                for selected_field in selected_fields:
                    if selected_field.get('name') == field_name and not selected_field.get('selected', True):
                        is_disabled = True
                        break
                
                if not is_disabled:
                    # 查找对应的列名
                    column_name = None
                    if field_name in header_info['field_mapping']:
                        column_name = header_info['field_mapping'][field_name]
                    elif field_name in header_info['defect_mapping']:
                        column_name = header_info['defect_mapping'][field_name]
                    elif field_name in df.columns:
                        column_name = field_name
                    
                    if column_name:
                        field_type = 'standard' if field_name in header_info['field_mapping'] else 'defect'
                        aggregate_fields.append({
                            'name': field_name,
                            'column': column_name,
                            'type': field_type,
                            'can_aggregate': field_name in ['良品数(kg)', '报废数(kg)', '光箔*'],
                            'selected': True
                        })
        else:
            # 默认使用所有固定字段
            for field_name in default_aggregate_fields:
                column_name = None
                if field_name in header_info['field_mapping']:
                    column_name = header_info['field_mapping'][field_name]
                elif field_name in header_info['defect_mapping']:
                    column_name = header_info['defect_mapping'][field_name]
                elif field_name in df.columns:
                    column_name = field_name
                
                if column_name:
                    field_type = 'standard' if field_name in header_info['field_mapping'] else 'defect'
                    aggregate_fields.append({
                        'name': field_name,
                        'column': column_name,
                        'type': field_type,
                        'can_aggregate': field_name in ['良品数(kg)', '报废数(kg)', '光箔*'],
                        'selected': True
                    })
        
        # 总体汇总
        total_summary = {}
        for field in aggregate_fields:
            column = field['column']
            if column in df.columns:
                total_summary[field['name']] = {
                    'sum': float(df[column].sum()),
                    'avg': float(df[column].mean()),
                    'max': float(df[column].max()),
                    'min': float(df[column].min()),
                    'count': int(df[column].count())
                }
        summary['total_summary'] = total_summary
        
        # 按工序分组汇总
        if '工序名称' in header_info['field_mapping']:
            process_column = header_info['field_mapping']['工序名称']
            if process_column in df.columns:
                process_summary = {}
                for process in df[process_column].unique():
                    process_data = df[df[process_column] == process]
                    process_data_summary = {}
                    
                    for field in aggregate_fields:
                        column = field['column']
                        if column in process_data.columns:
                            process_data_summary[field['name']] = {
                                'sum': float(process_data[column].sum()),
                                'avg': float(process_data[column].mean()),
                                'max': float(process_data[column].max()),
                                'min': float(process_data[column].min()),
                                'count': int(process_data[column].count())
                            }
                    
                    process_summary[process] = {
                        'records': len(process_data),
                        'summary': process_data_summary
                    }
                
                summary['group_summaries']['by_process'] = process_summary
        
        # 按班次分组汇总
        if '班次' in header_info['field_mapping']:
            shift_column = header_info['field_mapping']['班次']
            if shift_column in df.columns:
                shift_summary = {}
                for shift in df[shift_column].unique():
                    shift_data = df[df[shift_column] == shift]
                    shift_data_summary = {}
                    
                    for field in aggregate_fields:
                        column = field['column']
                        if column in shift_data.columns:
                            shift_data_summary[field['name']] = {
                                'sum': float(shift_data[column].sum()),
                                'avg': float(shift_data[column].mean()),
                                'max': float(shift_data[column].max()),
                                'min': float(shift_data[column].min()),
                                'count': int(shift_data[column].count())
                            }
                    
                    shift_summary[shift] = {
                        'records': len(shift_data),
                        'summary': shift_data_summary
                    }
                
                summary['group_summaries']['by_shift'] = shift_summary
        
        return summary
    
    def get_field_statistics(self, df: pd.DataFrame, field_config: Dict) -> Dict:
        """获取字段统计信息"""
        column = field_config['column']
        if column not in df.columns:
            return {}
        
        data = df[column]
        
        if field_config.get('can_aggregate'):
            return {
                'sum': float(data.sum()),
                'avg': float(data.mean()),
                'max': float(data.max()),
                'min': float(data.min()),
                'std': float(data.std()),
                'count': int(data.count())
            }
        else:
            return {
                'unique_count': int(data.nunique()),
                'most_common': data.value_counts().head(5).to_dict()
            }
    
    def apply_filters(self, csv_data: List[Dict], filter_config: Dict) -> Dict[str, Any]:
        """
        应用筛选条件到数据
        
        Args:
            csv_data: 数据列表（已从JSON反序列化）
            filter_config: 筛选配置
            
        Returns:
            包含筛选后数据的字典
        """
        try:
            # 将数据列表转换为DataFrame
            df = pd.DataFrame(csv_data)
            
            # 应用筛选
            df_filtered = self._apply_filters(df, filter_config)
            
            # 将筛选后的数据转换为可序列化的格式
            data_list = df_filtered.to_dict('records')
            columns_list = df_filtered.columns.tolist()
            
            return {
                'success': True,
                'data': data_list,
                'columns': columns_list
            }
            
        except Exception as e:
            logger.error(f"应用筛选失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'columns': []
            }
    
    def calculate_summary(self, csv_data: List[Dict], selected_fields: List[Dict]) -> Dict:
        """
        计算汇总统计信息
        
        Args:
            csv_data: 数据列表
            selected_fields: 选中的字段配置列表
            
        Returns:
            汇总统计结果
        """
        try:
            # 将数据列表转换为DataFrame
            df = pd.DataFrame(csv_data)
            
            # 生成汇总数据
            summary = {
                'total_records': len(df),
                'total_summary': {}
            }
            
            # 为每个选中的可聚合字段计算统计值
            for field in selected_fields:
                if field.get('can_aggregate') and field.get('selected'):
                    column = field.get('column') or field.get('name')
                    if column in df.columns:
                        # 确保数据是数值类型
                        if not pd.api.types.is_numeric_dtype(df[column]):
                            df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0)
                        
                        summary['total_summary'][field.get('name', column)] = {
                            'sum': convert_numpy_types(df[column].sum()),
                            'avg': convert_numpy_types(df[column].mean()),
                            'max': convert_numpy_types(df[column].max()),
                            'min': convert_numpy_types(df[column].min()),
                            'count': convert_numpy_types(df[column].count())
                        }
            
            # 使用统一的序列化函数确保结果可JSON序列化
            return safe_json_serialize(summary)
            
        except Exception as e:
            logger.error(f"计算汇总失败: {str(e)}")
            return {
                'total_records': 0,
                'total_summary': {}
            }