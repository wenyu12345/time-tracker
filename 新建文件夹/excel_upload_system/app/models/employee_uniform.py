"""员工工装管理数据模型"""
import json
import os
import uuid
import logging
import sys
from datetime import datetime
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(stream=sys.stdout)]
)
logger = logging.getLogger(__name__)


class EmployeeUniformManager:
    """员工工装管理类"""
    
    def __init__(self):
        """Initialize employee uniform manager"""
        self.data_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'employee_uniforms.json'
        )
        self.ensure_data_dir()
        self.load_data()
        # Using English to avoid encoding issues
        logger.info("Employee uniform manager initialized")
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.data_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def load_data(self):
        """Load data from file"""
        if not os.path.exists(self.data_file):
            # Initialize empty data structure
            self.data = {
                'employees': [],  # Employee list
                'uniform_types': [],  # Uniform types list
                'uniform_records': []  # Uniform records
            }
            logger.info(f"Data file not found, initializing empty data structure: {self.data_file}")
            self.save_data()
        else:
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Successfully loaded data file: {self.data_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Data file format error: {str(e)}")
                # If loading fails, initialize empty data
                self.data = {
                    'employees': [],
                    'uniform_types': [],
                    'uniform_records': []
                }
            except Exception as e:
                logger.error(f"Failed to load employee uniform data: {str(e)}")
                # If loading fails, initialize empty data
                self.data = {
                    'employees': [],
                    'uniform_types': [],
                    'uniform_records': []
                }
    
    def save_data(self):
        """保存数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved data to file: {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {str(e)}")
            return False
    
    # 员工相关操作
    def add_employee(self, name: str, employee_id: str) -> Dict:
        """添加员工"""
        # 数据验证
        if not name or not employee_id:
            logger.warning("Employee name or employee ID cannot be empty")
            return {'success': False, 'error': '员工姓名和工号不能为空'}
        
        # 检查工号是否已存在
        for emp in self.data['employees']:
            if emp['employee_id'] == employee_id:
                logger.warning(f"Employee ID already exists: {employee_id}")
                return {'success': False, 'error': '工号已存在'}
        
        # 使用UUID生成唯一ID
        employee = {
            'id': str(uuid.uuid4()),  # 使用UUID生成唯一ID
            'name': name.strip(),
            'employee_id': employee_id.strip(),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.data['employees'].append(employee)
        success = self.save_data()
        
        if success:
            logger.info(f"Successfully added employee: {name} ({employee_id})")
            return {'success': True, 'employee': employee}
        else:
            # 保存失败，回滚 - 删除刚添加的员工，而不是最后一个
            self.data['employees'] = [emp for emp in self.data['employees'] if emp['employee_id'] != employee_id]
            logger.error(f"Failed to add employee: {name} ({employee_id})")
            return {'success': False, 'error': '保存失败'}
    
    def get_employees(self) -> List[Dict]:
        """获取所有员工"""
        return self.data['employees']
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict]:
        """根据工号获取员工"""
        for emp in self.data['employees']:
            if emp['employee_id'] == employee_id:
                return emp
        return None
    
    def delete_employee(self, employee_id: str) -> Dict:
        """删除员工"""
        # 检查是否有工装领取记录
        has_records = any(record['employee_id'] == employee_id for record in self.data['uniform_records'])
        if has_records:
            logger.warning(f"Employee {employee_id} has uniform records, cannot delete")
            return {'success': False, 'error': '该员工存在工装领取记录，无法删除'}
        
        # 查找并删除员工
        for i, emp in enumerate(self.data['employees']):
            if emp['employee_id'] == employee_id:
                employee_name = emp['name']
                self.data['employees'].pop(i)
                success = self.save_data()
                if success:
                    logger.info(f"Successfully deleted employee: {employee_name} ({employee_id})")
                    return {'success': True, 'message': '员工删除成功'}
                else:
                    # 保存失败，回滚
                    self.data['employees'].insert(i, emp)
                    logger.error(f"Failed to delete employee: {employee_name} ({employee_id})")
                    return {'success': False, 'error': '保存失败'}
        
        logger.warning(f"Employee not found: {employee_id}")
        return {'success': False, 'error': '员工不存在'}
    
    def update_employee(self, employee_id: str, name: Optional[str] = None, new_employee_id: Optional[str] = None) -> Dict:
        """更新员工信息，支持修改工号和姓名
        
        Args:
            employee_id: 当前员工工号
            name: 新员工姓名（可选）
            new_employee_id: 新员工工号（可选）
        
        Returns:
            dict: 包含更新结果的字典
        """
        try:
            # 查找员工
            employee_index = None
            for i, emp in enumerate(self.data['employees']):
                if emp['employee_id'] == employee_id:
                    employee_index = i
                    break
            
            if employee_index is None:
                logger.warning(f"Employee not found: {employee_id}")
                return {'success': False, 'error': '员工不存在'}
            
            # 检查是否提供了要更新的字段
            if name is None and new_employee_id is None:
                logger.warning(f"No fields provided for update: {employee_id}")
                return {'success': False, 'error': '至少需要提供姓名或工号'}
            
            # 检查新工号是否已存在
            if new_employee_id:
                if new_employee_id != employee_id:
                    for emp in self.data['employees']:
                        if emp['employee_id'] == new_employee_id:
                            logger.warning(f"New employee ID already exists: {new_employee_id}")
                            return {'success': False, 'error': '工号已存在'}
            
            # 检查姓名是否有效
            if name is not None:
                if not name.strip():
                    logger.warning(f"Empty name provided for employee: {employee_id}")
                    return {'success': False, 'error': '员工姓名不能为空'}
            
            # 更新员工信息
            employee = self.data['employees'][employee_index]
            
            if name is not None:
                employee['name'] = name.strip()
            
            # 如果需要更新工号，同时更新所有相关记录
            if new_employee_id and new_employee_id != employee_id:
                old_employee_id = employee['employee_id']
                employee['employee_id'] = new_employee_id.strip()
                
                # 更新所有相关的工装领取记录
                for record in self.data['uniform_records']:
                    if record['employee_id'] == old_employee_id:
                        record['employee_id'] = new_employee_id.strip()
            
            # 保存数据
            success = self.save_data()
            if success:
                logger.info(f"Successfully updated employee: {employee_id}")
                return {'success': True, 'employee': employee}
            else:
                logger.error(f"Failed to update employee: {employee_id}")
                return {'success': False, 'error': '保存失败'}
        
        except Exception as e:
            logger.error(f"Failed to update employee: {employee_id}, Error: {str(e)}")
            return {'success': False, 'error': '更新员工信息失败'}
    
    # 工装类型相关操作
    def add_uniform_type(self, name: str, description: str = '') -> Dict:
        """添加工装类型"""
        # 数据验证
        if not name:
            logger.warning("Uniform type name cannot be empty")
            return {'success': False, 'error': '工装类型名称不能为空'}
        
        # 检查类型名称是否已存在
        for uniform_type in self.data['uniform_types']:
            if uniform_type['name'] == name:
                logger.warning(f"Uniform type already exists: {name}")
                return {'success': False, 'error': '工装类型已存在'}
        
        # 使用UUID生成唯一ID
        uniform_type = {
            'id': str(uuid.uuid4()),
            'name': name.strip(),
            'description': description.strip(),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.data['uniform_types'].append(uniform_type)
        success = self.save_data()
        
        if success:
            logger.info(f"Successfully added uniform type: {name}")
            return {'success': True, 'uniform_type': uniform_type}
        else:
            # 保存失败，回滚
            self.data['uniform_types'].pop()
            logger.error(f"Failed to add uniform type: {name}")
            return {'success': False, 'error': '保存失败'}
    
    def get_uniform_types(self) -> List[Dict]:
        """获取所有工装类型"""
        return self.data['uniform_types']
    
    def delete_uniform_type(self, type_id: str) -> Dict:
        """删除工装类型"""
        # 检查是否有工装领取记录使用该类型
        has_records = any(record.get('uniform_type_id') == type_id for record in self.data['uniform_records'])
        if has_records:
            logger.warning(f"Uniform type {type_id} is in use, cannot delete")
            return {'success': False, 'error': '该工装类型正在被使用，无法删除'}
        
        # 查找并删除类型
        for i, uniform_type in enumerate(self.data['uniform_types']):
            if uniform_type['id'] == type_id:
                type_name = uniform_type['name']
                self.data['uniform_types'].pop(i)
                success = self.save_data()
                if success:
                    logger.info(f"Successfully deleted uniform type: {type_name} ({type_id})")
                    return {'success': True, 'message': '工装类型删除成功'}
                else:
                    # 保存失败，回滚
                    self.data['uniform_types'].insert(i, uniform_type)
                    logger.error(f"Failed to delete uniform type: {type_name} ({type_id})")
                    return {'success': False, 'error': '保存失败'}
        
        logger.warning(f"Uniform type not found: {type_id}")
        return {'success': False, 'error': '工装类型不存在'}
    
    # 工装领取记录相关操作
    def add_uniform_record(self, employee_id: str, uniform_type_id: str, issue_date: str = None, silent: bool = False) -> Dict:
        """添加工装领取记录
        
        参数:
        - employee_id: 员工ID
        - uniform_type_id: 工装类型ID
        - issue_date: 发放日期，默认为当前日期
        - silent: 是否静默模式，默认为False。如果为True，则不记录日志中的钉钉通知相关信息
        """
        # 检查员工是否存在
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            logger.warning(f"Employee not found: {employee_id}")
            return {'success': False, 'error': '员工不存在'}
        
        # 检查工装类型是否存在
        uniform_type = None
        for ut in self.data['uniform_types']:
            if ut['id'] == uniform_type_id:
                uniform_type = ut
                break
        if not uniform_type:
            logger.warning(f"Uniform type not found: {uniform_type_id}")
            return {'success': False, 'error': '工装类型不存在'}
        
        # 验证日期格式
        if issue_date:
            try:
                # 验证日期格式是否正确
                datetime.strptime(issue_date, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Date format error: {issue_date}")
                return {'success': False, 'error': '日期格式错误，应为YYYY-MM-DD'}
        else:
            issue_date = datetime.now().strftime('%Y-%m-%d')
        
        # 使用UUID生成唯一ID
        record = {
            'id': str(uuid.uuid4()),
            'employee_id': employee_id,
            'employee_name': employee['name'],
            'uniform_type_id': uniform_type_id,
            'uniform_type_name': uniform_type['name'],
            'issue_date': issue_date,
            'recorded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'quantity': 1  # 默认数量为1
        }
        
        self.data['uniform_records'].append(record)
        success = self.save_data()
        
        if success:
            if not silent:
                logger.info(f"Successfully added uniform record: {employee['name']} - {uniform_type['name']}")
            else:
                logger.debug(f"Silently added uniform record: {employee['name']} - {uniform_type['name']}")
            return {'success': True, 'record': record}
        else:
            # 保存失败，回滚
            self.data['uniform_records'].pop()
            logger.error(f"Failed to add uniform record")
            return {'success': False, 'error': '保存失败'}
    
    def get_uniform_records(self, employee_id: str = None) -> List[Dict]:
        """获取工装领取记录"""
        if employee_id:
            return [record for record in self.data['uniform_records'] if record['employee_id'] == employee_id]
        return self.data['uniform_records']
    
    def get_employee_uniform_history(self, employee_id: str) -> Dict:
        """获取员工的工装领取历史"""
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            return {'success': False, 'error': '员工不存在'}
        
        records = self.get_uniform_records(employee_id)
        
        return {
            'success': True,
            'employee': employee,
            'records': records
        }
    
    def get_uniform_summary(self, uniform_type_id: str = '', year: str = '', search: str = '') -> Dict:
        """获取员工工装领取汇总信息
        
        Args:
            uniform_type_id: 工装类型ID筛选
            year: 年份筛选
            search: 搜索关键词（员工姓名或工号）
            
        Returns:
            dict: 包含所有员工汇总信息的字典
        """
        try:
            import datetime
            
            # 获取当前年份
            target_year = int(year) if year else datetime.datetime.now().year
            # 获取今天的日期
            today = datetime.datetime.now().date()
            
            # 初始化汇总数据
            summary = []
            
            # 应用员工筛选（搜索）
            filtered_employees = self.data['employees']
            if search:
                search_lower = search.lower()
                filtered_employees = [
                    emp for emp in self.data['employees']
                    if search_lower in emp['employee_id'].lower() or search_lower in emp['name'].lower()
                ]
            
            # 为每个员工计算汇总信息
            for employee in filtered_employees:
                employee_id = employee['employee_id']
                employee_name = employee['name']
                
                # 查找该员工的所有领取记录
                employee_records = []
                for record in self.data['uniform_records']:
                    if record['employee_id'] == employee_id:
                        # 应用工装类型筛选
                        if uniform_type_id and record.get('uniform_type_id') != uniform_type_id:
                            continue
                            
                        # 转换日期字符串为datetime对象
                        try:
                            record_date = datetime.datetime.strptime(record['issue_date'], '%Y-%m-%d').date()
                            record_with_date = record.copy()
                            record_with_date['date_obj'] = record_date
                            employee_records.append(record_with_date)
                        except ValueError:
                            # 跳过日期格式无效的记录
                            continue
                
                # 计算今年领取套数
                this_year_count = 0
                last_issue_date = None
                
                if employee_records:
                    # 按日期降序排序
                    employee_records.sort(key=lambda x: x['date_obj'], reverse=True)
                    
                    # 获取最后一次领取日期
                    last_issue_date = employee_records[0]['date_obj']
                    
                    # 计算目标年份领取的记录数
                    this_year_count = len([r for r in employee_records 
                                         if r['date_obj'].year == target_year])
                
                # 计算距离上次领取的天数
                days_since_last_issue = 0
                if last_issue_date:
                    days_since_last_issue = (today - last_issue_date).days
                
                # 添加到汇总列表
                summary.append({
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'this_year_count': this_year_count,
                    'days_since_last_issue': days_since_last_issue
                })
            
            # 按员工工号排序
            summary.sort(key=lambda x: x['employee_id'])
            
            return {
                'success': True,
                'summary': summary
            }
        except Exception as e:
            logger.error(f"Failed to get uniform summary, Error: {str(e)}")
            return {'success': False, 'error': '获取汇总信息失败'}
    
    def delete_uniform_record(self, record_id: str) -> Dict:
        """删除工装领取记录"""
        for i, record in enumerate(self.data['uniform_records']):
            if record['id'] == record_id:
                record_info = f"{record['employee_name']} - {record['uniform_type_name']} ({record['issue_date']})"
                self.data['uniform_records'].pop(i)
                success = self.save_data()
                if success:
                    logger.info(f"Successfully deleted uniform record: {record_info}")
                    return {'success': True, 'message': '工装领取记录删除成功'}
                else:
                    # 保存失败，回滚
                    self.data['uniform_records'].insert(i, record)
                    logger.error(f"Failed to delete uniform record: {record_info}")
                    return {'success': False, 'error': '保存失败'}
        
        logger.warning(f"Uniform record not found: {record_id}")
        return {'success': False, 'error': '工装领取记录不存在'}
