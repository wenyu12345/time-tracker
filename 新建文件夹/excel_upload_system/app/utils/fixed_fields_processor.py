import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from collections import defaultdict
from app.utils.utilities import safe_json_serialize
import logging

logger = logging.getLogger(__name__)

class FixedFieldsProcessor:
    """固定字段处理器 - 专门处理用户指定的汇总字段"""
    
    def __init__(self):
        # 固定汇总字段
        self.fixed_aggregate_fields = [
            '日期', '班次', '产品型号', '工序名称', '良品数(kg)', '报废数(kg)', '光箔*'
        ]
        
        # 可汇总的数值字段
        self.numeric_fields = ['良品数(kg)', '报废数(kg)', '光箔*']
    
    def get_available_fields(self, header_info: Dict, columns_list: List[str]) -> List[Dict]:
        """获取固定字段的可用性"""
        available_fields = []
        
        for field_name in self.fixed_aggregate_fields:
            column_name = None
            field_type = 'standard'
            
            # 查找字段对应的列名
            if field_name in header_info.get('field_mapping', {}):
                column_name = header_info['field_mapping'][field_name]
                field_type = 'standard'
            elif field_name in header_info.get('defect_mapping', {}):
                column_name = header_info['defect_mapping'][field_name]
                field_type = 'defect'
            elif field_name in columns_list:
                column_name = field_name
                field_type = 'defect' if '*' in field_name else 'standard'
            
            # 只有存在的字段才添加
            if column_name and column_name in columns_list:
                available_fields.append({
                    'name': field_name,
                    'column': column_name,
                    'type': field_type,
                    'can_aggregate': field_name in self.numeric_fields,
                    'selected': True  # 默认全部选中
                })
        
        return available_fields
    
    def calculate_summary(self, df_list: list, selected_fields: list, header_info: Dict) -> Dict:
        """基于固定字段计算汇总"""
        try:
            # 转换为DataFrame
            if not df_list:
                return {
                    'total_records': 0,
                    'group_summaries': {},
                    'total_summary': {}
                }
            
            df = pd.DataFrame(df_list)
            
            # 获取要汇总的字段
            aggregate_fields = []
            for field_name in self.fixed_aggregate_fields:
                # 检查是否被屏蔽
                is_disabled = False
                for selected_field in selected_fields:
                    if selected_field.get('name') == field_name and not selected_field.get('selected', True):
                        is_disabled = True
                        break
                
                if not is_disabled:
                    # 查找对应的列名
                    column_name = None
                    if field_name in header_info.get('field_mapping', {}):
                        column_name = header_info['field_mapping'][field_name]
                    elif field_name in header_info.get('defect_mapping', {}):
                        column_name = header_info['defect_mapping'][field_name]
                    elif field_name in df.columns:
                        column_name = field_name
                    
                    if column_name:
                        field_type = 'standard' if field_name in header_info.get('field_mapping', {}) else 'defect'
                        aggregate_fields.append({
                            'name': field_name,
                            'column': column_name,
                            'type': field_type,
                            'can_aggregate': field_name in self.numeric_fields,
                            'selected': True
                        })
            
            # 生成汇总
            return self._generate_fixed_summary(df, aggregate_fields, header_info)
            
        except Exception as e:
            logger.error(f"计算汇总失败: {str(e)}")
            return {
                'total_records': 0,
                'group_summaries': {},
                'total_summary': {}
            }
    
    def _generate_fixed_summary(self, df: pd.DataFrame, aggregate_fields: list, header_info: Dict) -> Dict:
        """生成固定字段的汇总数据"""
        summary = {
            'total_records': len(df),
            'group_summaries': {}
        }
        
        # 总体汇总
        total_summary = {}
        for field in aggregate_fields:
            column = field['column']
            if column in df.columns:
                if field['can_aggregate']:
                    # 数值字段计算统计
                    col_data = pd.to_numeric(df[column], errors='coerce').fillna(0)
                    total_summary[field['name']] = {
                        'sum': float(col_data.sum()),
                        'avg': float(col_data.mean()),
                        'max': float(col_data.max()),
                        'min': float(col_data.min()),
                        'count': int(col_data.count()),
                        'std': float(col_data.std()),
                        'median': float(col_data.median()),
                        'q25': float(col_data.quantile(0.25)),
                        'q75': float(col_data.quantile(0.75))
                    }
                else:
                    # 非数值字段只计数
                    total_summary[field['name']] = {
                        'count': int(df[column].count()),
                        'unique': int(df[column].nunique()),
                        'values': df[column].unique().tolist()[:10]  # 显示前10个唯一值
                    }
        summary['total_summary'] = total_summary
        
        # 按工序分组汇总
        process_column = None
        if '工序名称' in header_info.get('field_mapping', {}):
            process_column = header_info['field_mapping']['工序名称']
        elif '工序名称' in df.columns:
            process_column = '工序名称'
            
        if process_column and process_column in df.columns:
            process_summary = {}
            for process in df[process_column].unique():
                process_data = df[df[process_column] == process]
                process_data_summary = {}
                
                for field in aggregate_fields:
                        column = field['column']
                        if column in process_data.columns:
                            if field['can_aggregate']:
                                col_data = pd.to_numeric(process_data[column], errors='coerce').fillna(0)
                                process_data_summary[field['name']] = {
                                    'sum': float(col_data.sum()),
                                    'avg': float(col_data.mean()),
                                    'max': float(col_data.max()),
                                    'min': float(col_data.min()),
                                    'count': int(col_data.count()),
                                    'std': float(col_data.std()),
                                    'median': float(col_data.median()),
                                    'q25': float(col_data.quantile(0.25)),
                                    'q75': float(col_data.quantile(0.75))
                                }
                            else:
                                process_data_summary[field['name']] = {
                                    'count': int(process_data[column].count()),
                                    'unique': int(process_data[column].nunique()),
                                    'values': process_data[column].unique().tolist()[:5]
                                }
                
                process_summary[process] = {
                    'records': len(process_data),
                    'summary': process_data_summary
                }
            summary['group_summaries']['by_process'] = process_summary
        
        # 按班次分组汇总
        shift_column = None
        if '班次' in header_info.get('field_mapping', {}):
            shift_column = header_info['field_mapping']['班次']
        elif '班次' in df.columns:
            shift_column = '班次'
            
        if shift_column and shift_column in df.columns:
            shift_summary = {}
            for shift in df[shift_column].unique():
                shift_data = df[df[shift_column] == shift]
                shift_data_summary = {}
                
                for field in aggregate_fields:
                    column = field['column']
                    if column in shift_data.columns:
                        if field['can_aggregate']:
                            col_data = pd.to_numeric(shift_data[column], errors='coerce').fillna(0)
                            shift_data_summary[field['name']] = {
                                'sum': float(col_data.sum()),
                                'avg': float(col_data.mean()),
                                'max': float(col_data.max()),
                                'min': float(col_data.min()),
                                'count': int(col_data.count()),
                                'std': float(col_data.std()),
                                'median': float(col_data.median()),
                                'q25': float(col_data.quantile(0.25)),
                                'q75': float(col_data.quantile(0.75))
                            }
                        else:
                            shift_data_summary[field['name']] = {
                                'count': int(shift_data[column].count()),
                                'unique': int(shift_data[column].nunique()),
                                'values': shift_data[column].unique().tolist()[:5]
                            }
                
                shift_summary[shift] = {
                    'records': len(shift_data),
                    'summary': shift_data_summary
                }
            summary['group_summaries']['by_shift'] = shift_summary
        
        # 按产品型号分组汇总
        product_column = None
        if '产品型号' in header_info.get('field_mapping', {}):
            product_column = header_info['field_mapping']['产品型号']
        elif '产品型号' in df.columns:
            product_column = '产品型号'
            
        if product_column and product_column in df.columns:
            product_summary = {}
            for product in df[product_column].unique():
                product_data = df[df[product_column] == product]
                product_data_summary = {}
                
                for field in aggregate_fields:
                    column = field['column']
                    if column in product_data.columns:
                        if field['can_aggregate']:
                            col_data = pd.to_numeric(product_data[column], errors='coerce').fillna(0)
                            product_data_summary[field['name']] = {
                                'sum': float(col_data.sum()),
                                'avg': float(col_data.mean()),
                                'max': float(col_data.max()),
                                'min': float(col_data.min()),
                                'count': int(col_data.count()),
                                'std': float(col_data.std()),
                                'median': float(col_data.median()),
                                'q25': float(col_data.quantile(0.25)),
                                'q75': float(col_data.quantile(0.75))
                            }
                        else:
                            product_data_summary[field['name']] = {
                                'count': int(product_data[column].count()),
                                'unique': int(product_data[column].nunique()),
                                'values': product_data[column].unique().tolist()[:5]
                            }
                
                product_summary[product] = {
                    'records': len(product_data),
                    'summary': product_data_summary
                }
            summary['group_summaries']['by_product'] = product_summary
        
        # 添加计算字段
        summary['calculated_fields'] = self._calculate_derived_fields(summary, aggregate_fields)
        
        return summary
    
    def _calculate_derived_fields(self, summary: Dict, aggregate_fields: list) -> Dict:
        """计算衍生字段"""
        calculated = {}
        total_summary = summary.get('total_summary', {})
        
        # 计算总体良品率
        good_data = total_summary.get('良品数(kg)', {})
        bad_data = total_summary.get('报废数(kg)', {})
        
        if good_data and bad_data:
            good_sum = good_data.get('sum', 0)
            bad_sum = bad_data.get('sum', 0)
            total_sum = good_sum + bad_sum
            
            if total_sum > 0:
                calculated['总体良品率'] = {
                    'value': (good_sum / total_sum) * 100,
                    'unit': '%',
                    'description': '良品数占总投入数的百分比'
                }
                calculated['总体报废率'] = {
                    'value': (bad_sum / total_sum) * 100,
                    'unit': '%',
                    'description': '报废数占总投入数的百分比'
                }
        
        # 计算光箔不良占比
        foil_data = total_summary.get('光箔*', {})
        if foil_data:
            foil_sum = foil_data.get('sum', 0)
            if total_sum > 0:
                calculated['光箔不良占比'] = {
                    'value': (foil_sum / total_sum) * 100,
                    'unit': '%',
                    'description': '光箔不良数占总投入数的百分比'
                }
        
        # 按分组的衍生字段计算
        group_summaries = summary.get('group_summaries', {})
        
        if group_summaries.get('by_process'):
            process_rates = {}
            process_efficiency = {}
            
            for process_name, process_data in group_summaries['by_process'].items():
                process_summary = process_data.get('summary', {})
                process_good = process_summary.get('良品数(kg)', {})
                process_bad = process_summary.get('报废数(kg)', {})
                
                if process_good and process_bad:
                    good_sum = process_good.get('sum', 0)
                    bad_sum = process_bad.get('sum', 0)
                    process_total = good_sum + bad_sum
                    
                    if process_total > 0:
                        process_rates[process_name] = (good_sum / process_total) * 100
                        
                        # 计算工序效率（基于良品数）
                        if good_sum > 0:
                            process_efficiency[process_name] = good_sum / process_data.get('records', 1)
            
            calculated['工序良品率排名'] = dict(sorted(process_rates.items(), key=lambda x: x[1], reverse=True))
            calculated['工序生产效率'] = process_efficiency
        
        if group_summaries.get('by_shift'):
            shift_rates = {}
            
            for shift_name, shift_data in group_summaries['by_shift'].items():
                shift_summary = shift_data.get('summary', {})
                shift_good = shift_summary.get('良品数(kg)', {})
                shift_bad = shift_summary.get('报废数(kg)', {})
                
                if shift_good and shift_bad:
                    good_sum = shift_good.get('sum', 0)
                    bad_sum = shift_bad.get('sum', 0)
                    shift_total = good_sum + bad_sum
                    
                    if shift_total > 0:
                        shift_rates[shift_name] = (good_sum / shift_total) * 100
            
            calculated['班次良品率'] = shift_rates
        
        # 统计指标分析
        if good_data and bad_data:
            calculated['生产稳定性分析'] = self._analyze_production_stability(good_data, bad_data)
        
        return calculated
    
    def _analyze_production_stability(self, good_data: Dict, bad_data: Dict) -> Dict:
        """分析生产稳定性"""
        analysis = {}
        
        # 基于标准差的稳定性分析
        if 'std' in good_data and 'avg' in good_data:
            good_avg = good_data.get('avg', 0)
            good_std = good_data.get('std', 0)
            
            if good_avg > 0:
                cv = (good_std / good_avg) * 100  # 变异系数
                if cv < 10:
                    stability_level = '非常稳定'
                elif cv < 20:
                    stability_level = '稳定'
                elif cv < 30:
                    stability_level = '一般'
                else:
                    stability_level = '不稳定'
                
                analysis['良品数稳定性'] = {
                    'cv_value': cv,
                    'stability_level': stability_level,
                    'description': f'变异系数为{cv:.2f}%，生产{stability_level}'
                }
        
        # 质量一致性分析
        if 'std' in bad_data and 'avg' in bad_data:
            bad_avg = bad_data.get('avg', 0)
            bad_std = bad_data.get('std', 0)
            
            if bad_avg > 0:
                bad_cv = (bad_std / bad_avg) * 100
                analysis['质量一致性'] = {
                    'cv_value': bad_cv,
                    'description': f'报废数变异系数为{bad_cv:.2f}%'
                }
        
        return analysis
    
    def apply_filters(self, df_list: list, filter_config: Dict, header_info: Dict) -> Dict[str, Any]:
        """应用筛选条件"""
        try:
            if not df_list:
                return {
                    'success': True,
                    'data': [],
                    'columns': []
                }
            
            df = pd.DataFrame(df_list)
            
            # 日期筛选
            if 'date_range' in filter_config:
                date_range = filter_config['date_range']
                date_column = None
                if '日期' in header_info.get('field_mapping', {}):
                    date_column = header_info['field_mapping']['日期']
                elif '日期' in df.columns:
                    date_column = '日期'
                    
                if date_column and date_column in df.columns:
                    start_date = pd.to_datetime(date_range.get('start')) if date_range.get('start') else None
                    end_date = pd.to_datetime(date_range.get('end')) if date_range.get('end') else None
                    
                    if start_date:
                        df = df[pd.to_datetime(df[date_column], errors='coerce') >= start_date]
                    if end_date:
                        df = df[pd.to_datetime(df[date_column], errors='coerce') <= end_date]
            
            # 工序筛选
            if 'process_filter' in filter_config:
                processes = filter_config['process_filter']
                process_column = None
                if '工序名称' in header_info.get('field_mapping', {}):
                    process_column = header_info['field_mapping']['工序名称']
                elif '工序名称' in df.columns:
                    process_column = '工序名称'
                    
                if process_column and process_column in df.columns and processes:
                    df = df[df[process_column].isin(processes)]
            
            # 班次筛选（支持ALL）
            if 'shift_filter' in filter_config:
                shifts = filter_config['shift_filter']
                shift_column = None
                if '班次' in header_info.get('field_mapping', {}):
                    shift_column = header_info['field_mapping']['班次']
                elif '班次' in df.columns:
                    shift_column = '班次'
                    
                if shift_column and shift_column in df.columns and shifts:
                    # 如果选择ALL，不过滤班次
                    if 'ALL' not in shifts:
                        df = df[df[shift_column].isin(shifts)]
            
            # 字段屏蔽筛选
            if 'selected_fields' in filter_config:
                selected_fields = filter_config['selected_fields']
                columns_to_keep = []
                
                for field_name in self.fixed_aggregate_fields:
                    # 检查是否被屏蔽
                    is_disabled = False
                    for selected_field in selected_fields:
                        if selected_field.get('name') == field_name and not selected_field.get('selected', True):
                            is_disabled = True
                            break
                    
                    if not is_disabled:
                        # 查找对应的列名
                        if field_name in header_info.get('field_mapping', {}):
                            column_name = header_info['field_mapping'][field_name]
                        elif field_name in header_info.get('defect_mapping', {}):
                            column_name = header_info['defect_mapping'][field_name]
                        elif field_name in df.columns:
                            column_name = field_name
                        
                        if column_name and column_name in df.columns:
                            columns_to_keep.append(column_name)
                
                # 只保留选中的列
                if columns_to_keep:
                    df = df[columns_to_keep]
            
            return {
                'success': True,
                'data': safe_json_serialize(df.to_dict('records')),
                'columns': list(df.columns)
            }
            
        except Exception as e:
            logger.error(f"筛选应用失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'columns': []
            }