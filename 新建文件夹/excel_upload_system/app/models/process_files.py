"""工艺文件管理数据模型 - Version 4.0"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional


class ProcessFileManager:
    """工艺文件管理类 - Version 4.0"""
    
    # 默认字段配置
    DEFAULT_FIELDS = [
        {'key': 'model', 'label': '型号', 'visible': True, 'order': 1, 'required': False},
        {'key': 'test_type', 'label': '试验类型', 'visible': True, 'order': 2, 'required': False},
        {'key': 'electrode_type', 'label': '正负极', 'visible': True, 'order': 3, 'required': False, 'options': ['正', '负']},
        {'key': 'roll1_thickness', 'label': '一辊厚度', 'visible': True, 'order': 4, 'required': False},
        {'key': 'roll2_thickness', 'label': '二辊厚度', 'visible': True, 'order': 5, 'required': False},
        {'key': 'roll1_gap_operate', 'label': '一辊辊缝(操作侧)', 'visible': True, 'order': 6, 'required': False},
        {'key': 'roll1_gap_drive', 'label': '一辊辊缝(传动侧)', 'visible': True, 'order': 7, 'required': False},
        {'key': 'roll1_pressure_operate', 'label': '一辊压力(操作侧)', 'visible': True, 'order': 8, 'required': False},
        {'key': 'roll1_pressure_drive', 'label': '一辊压力(传动侧)', 'visible': True, 'order': 9, 'required': False},
        {'key': 'roll2_gap_operate', 'label': '二辊辊缝(操作侧)', 'visible': True, 'order': 10, 'required': False},
        {'key': 'roll2_gap_drive', 'label': '二辊辊缝(传动侧)', 'visible': True, 'order': 11, 'required': False},
        {'key': 'roll2_pressure_operate', 'label': '二辊压力(操作侧)', 'visible': True, 'order': 12, 'required': False},
        {'key': 'roll2_pressure_drive', 'label': '二辊压力(传动侧)', 'visible': True, 'order': 13, 'required': False}
    ]
    
    def __init__(self):
        """Initialize process file manager"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_file = os.path.join(project_root, 'data', 'process_files.json')
        self.config_file = os.path.join(project_root, 'data', 'process_config.json')
        self.ensure_data_dir()
        self.load_data()
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.data_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def load_data(self):
        """Load data from file"""
        if not os.path.exists(self.data_file):
            self.data = {'records': []}
            self.save_data()
        else:
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                self.data = {'records': []}
        
        if not os.path.exists(self.config_file):
            self.config = {'fields': self.DEFAULT_FIELDS.copy()}
            self.save_config()
        else:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                self.config = {'fields': self.DEFAULT_FIELDS.copy()}
                self.save_config()
    
    def save_data(self):
        """保存数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
    
    def get_fields(self) -> List[Dict]:
        """获取当前字段配置，按order排序"""
        fields = sorted(self.config.get('fields', self.DEFAULT_FIELDS.copy()), 
                       key=lambda x: x.get('order', 999))
        return fields
    
    def get_visible_fields(self) -> List[Dict]:
        """获取可见的字段"""
        return [f for f in self.get_fields() if f.get('visible', True)]

    def get_ui_settings(self) -> Dict:
        """获取UI配置"""
        default_settings = {
            'detail_modal_width': 800,
            'detail_textarea_height': 500,
            'detail_font_size': 14
        }
        ui_settings = self.config.get('ui_settings', {})
        for key, value in default_settings.items():
            if key not in ui_settings:
                ui_settings[key] = value
        return ui_settings

    def save_ui_settings(self, settings: Dict) -> Dict:
        """保存UI配置"""
        self.config['ui_settings'] = settings
        success = self.save_config()
        if success:
            return {'success': True}
        return {'success': False, 'error': '保存失败'}
    
    def update_field_order(self, field_keys: List[str]) -> Dict:
        """更新字段排序"""
        fields = self.config.get('fields', [])
        for index, key in enumerate(field_keys):
            for field in fields:
                if field['key'] == key:
                    field['order'] = index + 1
                    break
        
        success = self.save_config()
        if success:
            return {'success': True}
        return {'success': False, 'error': '保存失败'}
    
    def update_field_visibility(self, field_key: str, visible: bool) -> Dict:
        """更新字段可见性"""
        fields = self.config.get('fields', [])
        for field in fields:
            if field['key'] == field_key:
                field['visible'] = visible
                break
        
        success = self.save_config()
        if success:
            return {'success': True}
        return {'success': False, 'error': '保存失败'}
    
    def add_custom_field(self, key: str, label: str, field_type: str = 'text', required: bool = False) -> Dict:
        """添加自定义字段"""
        fields = self.config.get('fields', [])
        if any(f['key'] == key for f in fields):
            return {'success': False, 'error': '字段已存在'}
        
        new_field = {
            'key': key,
            'label': label,
            'type': field_type,
            'visible': True,
            'order': len(fields) + 1,
            'required': required
        }
        
        fields.append(new_field)
        success = self.save_config()
        if success:
            return {'success': True, 'field': new_field}
        return {'success': False, 'error': '保存失败'}
    
    def delete_field(self, field_key: str) -> Dict:
        """删除字段"""
        default_keys = [f['key'] for f in self.DEFAULT_FIELDS]
        if field_key in default_keys:
            return {'success': False, 'error': '默认字段不能删除，只能隐藏'}
        
        fields = self.config.get('fields', [])
        original_count = len(fields)
        fields = [f for f in fields if f['key'] != field_key]
        
        if len(fields) == original_count:
            return {'success': False, 'error': '字段不存在'}
        
        self.config['fields'] = fields
        success = self.save_config()
        if success:
            return {'success': True}
        return {'success': False, 'error': '保存失败'}
    
    def add_record(self, record_data: Dict) -> Dict:
        """添加工艺文件记录"""
        try:
            record = {
                'id': str(uuid.uuid4()),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            fields = self.get_fields()
            for field in fields:
                key = field['key']
                value = record_data.get(key, '')
                record[key] = str(value).strip() if value is not None else ''
            
            self.data['records'].append(record)
            success = self.save_data()
            
            if success:
                return {'success': True, 'record': record}
            return {'success': False, 'error': '保存失败'}
            
        except Exception as e:
            return {'success': False, 'error': f'添加失败: {str(e)}'}
    
    def get_records(self, search: str = '', sort_by: str = 'created_at', sort_order: str = 'desc', filters: Dict = None) -> List[Dict]:
        """获取工艺文件记录"""
        records = self.data.get('records', [])
        
        if search:
            search_lower = search.lower()
            records = [
                r for r in records
                if any(search_lower in str(r.get(key, '')).lower() for key in r.keys())
            ]
        
        # 应用筛选器
        if filters:
            for key, value in filters.items():
                if value:
                    records = [
                        r for r in records
                        if str(r.get(key, '')).strip() == str(value).strip()
                    ]
        
        if sort_by and sort_by in records[0] if records else False:
            records.sort(
                key=lambda x: str(x.get(sort_by, '')),
                reverse=(sort_order == 'desc')
            )
        else:
            records.sort(
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
        
        return records
    
    def get_record_by_id(self, record_id: str) -> Optional[Dict]:
        """根据ID获取记录"""
        for record in self.data.get('records', []):
            if record['id'] == record_id:
                return record
        return None
    
    def update_record(self, record_id: str, record_data: Dict) -> Dict:
        """更新工艺文件记录"""
        try:
            record = self.get_record_by_id(record_id)
            if not record:
                return {'success': False, 'error': '记录不存在'}
            
            fields = self.get_fields()
            for field in fields:
                key = field['key']
                if key in record_data:
                    value = record_data.get(key)
                    record[key] = str(value).strip() if value is not None else ''
            
            record['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            success = self.save_data()
            if success:
                return {'success': True, 'record': record}
            return {'success': False, 'error': '保存失败'}
            
        except Exception as e:
            return {'success': False, 'error': f'更新失败: {str(e)}'}
    
    def delete_record(self, record_id: str) -> Dict:
        """删除工艺文件记录"""
        for i, record in enumerate(self.data.get('records', [])):
            if record['id'] == record_id:
                self.data['records'].pop(i)
                success = self.save_data()
                if success:
                    return {'success': True, 'message': '删除成功'}
                return {'success': False, 'error': '保存失败'}
        
        return {'success': False, 'error': '记录不存在'}
    
    def export_records(self, record_ids: List[str] = None) -> List[Dict]:
        """导出记录"""
        records = self.data.get('records', [])
        
        if record_ids:
            records = [r for r in records if r['id'] in record_ids]
        
        visible_fields = [f['key'] for f in self.get_visible_fields()]
        export_data = []
        
        for record in records:
            export_record = {
                'created_at': record.get('created_at', ''),
                'updated_at': record.get('updated_at', '')
            }
            for key in visible_fields:
                export_record[key] = record.get(key, '')
            export_data.append(export_record)
        
        return export_data
