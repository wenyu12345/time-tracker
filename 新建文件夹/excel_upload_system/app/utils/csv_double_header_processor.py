import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import re
import json
import hashlib
from collections import defaultdict
import logging
from app.utils.cache_manager import cache_manager

logger = logging.getLogger(__name__)

class CSVDoubleHeaderProcessor:
    """CSV双层表头处理器
    专门处理双层表头CSV文件，支持表头识别、数据处理、多条件筛选和求和功能
    """
    
    def __init__(self):
        # 定义标准字段与可能的表头名称映射
        self.HEADER_MAPPING = {
            '日期': ['日期', 'Date', '日期时间', '时间', 'datetime', '生产日期', 'product_date', '日期时间'],
            '班次': ['班次', 'Shift', '班', '班别', '早班', '中班', '晚班', '早', '中', '晚', 'day', 'middle', 'night'],
            '产品型号': ['产品型号', '产品', '型号', 'Product', 'Model', '物料号', 'material_id', '物料编码', 'material_code', '料号'],
            '工序名称': ['工序名称', '工序', 'Process', '工序名', '工步', 'step', '操作', 'operation', '工序号', 'process_id'],
            '良品数(kg)': ['良品数(kg)', '良品数', '良品', 'Good', 'Yield', '合格数', 'qualified', '合格量', '产量', 'output'],
            '报废数(kg)': ['报废数(kg)', '报废数', '报废', 'Waste', 'Scrap', '废品数', '不良数', 'defective', '不良量', 'reject']
        }
        
        # 定义需要进行数值处理的字段
        self.NUMERIC_FIELDS = ['良品数(kg)', '报废数(kg)']
    
    def clean_header_name(self, header: str) -> Tuple[str, str]:
        """
        清理表头名称，去除多余字符和空格
        
        Args:
            header: 原始表头名称
        
        Returns:
            tuple: (清理后的表头, 清理后的小写表头)
        """
        if not isinstance(header, str):
            header = str(header)
        
        # 去除首尾空格
        header = header.strip()
        
        # 去除特殊字符，只保留字母、数字、中文和常见符号
        header = re.sub(r'[\s\u3000]+', ' ', header)  # 替换所有空白字符为单个空格
        header = re.sub(r'[\u00A0\t\n\r]+', ' ', header)  # 替换不间断空格和制表符
        
        # 清理一些常见的特殊字符
        header = re.sub(r'[\(\)\[\]{}]+', '', header)  # 去除括号
        
        # 转换为小写进行匹配（仅对英文部分）
        header_lower = header.lower()
        
        return header, header_lower
    
    def identify_and_map_headers(self, headers: List[str]) -> Tuple[Dict[str, str], List[str]]:
        """
        识别并映射表头字段
        
        Args:
            headers: 原始表头列表
        
        Returns:
            tuple: (字段映射字典, 未映射的表头列表)
        """
        field_mapping = {}
        used_standard_fields = set()
        unmapped_headers = []
        
        # 首先进行精确匹配
        for header in headers:
            clean_head, clean_head_lower = self.clean_header_name(header)
            
            # 检查精确匹配
            for standard_field, possible_names in self.HEADER_MAPPING.items():
                if standard_field == clean_head or clean_head_lower == standard_field.lower():
                    field_mapping[header] = standard_field
                    used_standard_fields.add(standard_field)
                    break
                
                # 检查可能的名称列表中的精确匹配
                for possible_name in possible_names:
                    if possible_name == clean_head or clean_head_lower == possible_name.lower():
                        field_mapping[header] = standard_field
                        used_standard_fields.add(standard_field)
                        break
                else:
                    continue  # 内循环未break，继续检查下一个标准字段
                break  # 找到匹配，跳出外循环
        
        # 然后进行模糊匹配（仅对未匹配的表头）
        for header in headers:
            if header in field_mapping:
                continue  # 已经匹配过的跳过
            
            clean_head, clean_head_lower = self.clean_header_name(header)
            
            # 模糊匹配：检查是否包含关键词
            matched = False
            for standard_field, possible_names in self.HEADER_MAPPING.items():
                if standard_field in used_standard_fields:
                    continue  # 已经被使用的标准字段跳过
                
                # 检查标准字段名是否在清理后的表头中
                if standard_field.lower() in clean_head_lower:
                    field_mapping[header] = standard_field
                    used_standard_fields.add(standard_field)
                    matched = True
                    break
                
                # 检查可能的名称是否在清理后的表头中
                for possible_name in possible_names:
                    if possible_name.lower() in clean_head_lower:
                        field_mapping[header] = standard_field
                        used_standard_fields.add(standard_field)
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                unmapped_headers.append(header)
        
        return field_mapping, unmapped_headers
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """
        解析日期字符串为标准格式
        
        Args:
            date_str: 日期字符串
        
        Returns:
            标准格式的日期字符串或None
        """
        if pd.isna(date_str) or not date_str:
            return None
        
        # 尝试多种日期格式
        formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
            '%Y年%m月%d日', '%Y年%m月%d日 %H:%M:%S'
        ]
        
        # 尝试直接解析
        for fmt in formats:
            try:
                dt = pd.to_datetime(date_str, format=fmt)
                return dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                continue
        
        # 尝试自动解析
        try:
            dt = pd.to_datetime(date_str)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            pass
        
        # 尝试处理Excel日期序列号
        try:
            num_value = float(date_str)
            dt = pd.to_datetime('1899-12-30') + pd.Timedelta(days=num_value)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            pass
        
        return None  # 无法识别的日期格式
    
    def process_file(self, file_content: bytes, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        处理双层表头CSV文件
        
        Args:
            file_content: 文件内容字节流
            encoding: 文件编码
        
        Returns:
            处理结果字典
        """
        try:
            # 生成缓存键
            cache_key = cache_manager.generate_cache_key(file_content, {'encoding': encoding})
            
            # 尝试从缓存获取结果
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info("从缓存获取文件处理结果")
                # 重建DataFrame对象
                if 'data' in cached_result:
                    cached_result['data'] = pd.DataFrame(cached_result['data'])
                return cached_result
            
            # 读取CSV文件，获取前两行作为表头
            # 使用更高效的读取方式，指定低内存模式
            df_raw = pd.read_csv(
                pd.io.common.BytesIO(file_content), 
                encoding=encoding, 
                header=[0, 1],
                low_memory=False
            )
            
            # 获取原始表头
            raw_headers = df_raw.columns.tolist()
            
            # 处理双层表头，创建扁平化的表头
            flat_headers = []
            for h1, h2 in raw_headers:
                # 如果第二层表头为空或重复，只使用第一层
                if pd.isna(h2) or h2 == h1 or h2.strip() == '':
                    flat_headers.append(str(h1))
                else:
                    # 组合两层表头
                    flat_headers.append(f"{h1}_{h2}")
            
            # 重命名列
            df_raw.columns = flat_headers
            
            # 识别并映射表头
            field_mapping, unmapped_headers = self.identify_and_map_headers(flat_headers)
            
            # 应用字段映射（直接在原DataFrame上操作，避免复制）
            rename_dict = {}
            for original, standard in field_mapping.items():
                if original in df_raw.columns:
                    rename_dict[original] = standard
            
            if rename_dict:
                df_raw.rename(columns=rename_dict, inplace=True)
            
            # 处理日期字段
            if '日期' in df_raw.columns:
                # 使用向量化操作，避免apply
                df_raw['日期'] = df_raw['日期'].apply(self.parse_date)
            
            # 处理数值字段
            for field in self.NUMERIC_FIELDS:
                if field in df_raw.columns:
                    # 尝试将字段转换为数值，使用更高效的数据类型
                    df_raw[field] = pd.to_numeric(df_raw[field], errors='coerce', downcast='float')
                    df_raw[field].fillna(0, inplace=True)
            
            # 优化内存使用：移除未使用的列
            used_columns = list(rename_dict.values()) + unmapped_headers
            df_raw = df_raw[used_columns]
            
            # 获取所有唯一的值用于筛选
            filter_options = {}
            for col in ['日期', '班次', '产品型号', '工序名称']:
                if col in df_raw.columns:
                    # 使用更高效的方式获取唯一值
                    unique_values = df_raw[col].dropna().unique()
                    # 确保都是字符串类型
                    unique_values = [str(v) for v in unique_values if v]
                    filter_options[col] = sorted(unique_values)
            
            # 准备缓存结果
            result = {
                'success': True,
                'data': df_raw.to_dict('records'),  # 转换为字典以便缓存
                'field_mapping': field_mapping,
                'unmapped_headers': unmapped_headers,
                'columns': df_raw.columns.tolist(),
                'filter_options': filter_options,
                'preview': df_raw.head(10).to_dict('records')
            }
            
            # 缓存结果，过期时间1小时
            cache_manager.set(cache_key, result, expire_seconds=3600)
            
            # 恢复DataFrame对象
            result['data'] = df_raw
            
            return result
        
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                return self.process_file(file_content, encoding='gbk')
            except Exception as e:
                logger.error(f"文件编码错误: {str(e)}")
                return {'success': False, 'error': f'文件编码错误: {str(e)}'}
        except Exception as e:
            logger.error(f"文件处理失败: {str(e)}")
            return {'success': False, 'error': f'文件处理失败: {str(e)}'}
    
    def filter_and_sum(self, df: pd.DataFrame, filters: Dict[str, List[str]], sum_fields: List[str]) -> Dict[str, Any]:
        """
        应用多条件筛选并对指定字段求和
        
        Args:
            df: 处理后的DataFrame
            filters: 筛选条件字典 {字段名: [值列表]}
            sum_fields: 需要求和的字段列表
        
        Returns:
            筛选结果和求和结果
        """
        try:
            # 生成缓存键
            # 使用DataFrame的哈希值和筛选参数作为缓存键
            df_hash = hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()
            cache_key = cache_manager.generate_cache_key(
                df_hash.encode(), 
                {'filters': filters, 'sum_fields': sum_fields}
            )
            
            # 尝试从缓存获取结果
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info("从缓存获取筛选求和结果")
                return cached_result
            
            # 应用筛选条件
            filtered_df = df.copy()
            for field, values in filters.items():
                if field in filtered_df.columns and values:
                    # 确保值类型匹配
                    filtered_df = filtered_df[filtered_df[field].astype(str).isin([str(v) for v in values])]
            
            # 计算求和结果
            sums = {}
            for field in sum_fields:
                if field in filtered_df.columns:
                    # 确保字段是数值类型
                    try:
                        numeric_values = pd.to_numeric(filtered_df[field], errors='coerce')
                        sums[field] = float(numeric_values.sum())
                    except Exception as e:
                        logger.warning(f"字段求和失败 {field}: {str(e)}")
                        sums[field] = 0
            
            # 按产品型号和工序名称分组求和
            group_sums = None
            if all(col in filtered_df.columns for col in ['产品型号', '工序名称']):
                group_by = ['产品型号', '工序名称']
                if '班次' in filtered_df.columns:
                    group_by.append('班次')
                if '日期' in filtered_df.columns:
                    group_by.append('日期')
                
                # 确保只对存在的列进行分组
                valid_group_by = [col for col in group_by if col in filtered_df.columns]
                
                # 选择需要求和的列
                valid_sum_fields = [field for field in sum_fields if field in filtered_df.columns]
                
                if valid_group_by and valid_sum_fields:
                    group_sums = filtered_df.groupby(valid_group_by)[valid_sum_fields].sum().reset_index()
                    group_sums = group_sums.to_dict('records')
            
            # 准备结果
            result = {
                'success': True,
                'total_count': len(filtered_df),
                'sums': sums,
                'group_sums': group_sums,
                'filtered_data': filtered_df.to_dict('records')
            }
            
            # 缓存结果，过期时间30分钟
            cache_manager.set(cache_key, result, expire_seconds=1800)
            
            return result
        except Exception as e:
            logger.error(f"筛选求和失败: {str(e)}")
            return {'success': False, 'error': f'筛选求和失败: {str(e)}'}
