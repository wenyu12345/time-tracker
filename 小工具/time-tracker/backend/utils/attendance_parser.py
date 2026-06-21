"""中文考勤文本解析器（"考勤技能"）

支持的输入格式示例：
  6月11日，白班应出36人，实际出勤32人，请假1人，自离3人，
  配料：刘虎、蒋江坤、黄春、宋春祥、郑成功
  正1D836涂布人员：李景均、李培嘉
  请假：宁福
  调休：李景均
  自离：赵红丽、韦广阔、周雨馨

分隔符可以是：: ： 、 , 逗号

支持关键字匹配：
- 配料 → 配料
- 辊压 → 辊压
- 涂布 → 涂布  
- 分条/激光切 → 激光切
- 职能 → 职能
- 物料/物料员 → 物料
- 主管 → 主管
- 领班 → 领班
- 发片 → 发片
"""
import re
from datetime import datetime
from typing import Dict, List, Optional
from .role_mapping import get_base_role


def parse_attendance_text(text: str) -> Dict:
    """将中文考勤文本解析为结构化数据
    
    返回格式:
    {
        "date": "2026-06-11",
        "shift": "白班",
        "attendance": {"配料": ["刘虎", ...], ...},
        "leave": ["宁福"],
        "absent": [],
        "in_lieu": ["李景均"],
        "resigned": ["赵红丽", ...]
    }
    """
    if not text:
        raise ValueError("考勤文本为空")
    
    # 标准化：去掉多余空白，统一行尾
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        raise ValueError("考勤文本没有内容")
    
    result = {
        "date": None,
        "shift": "白班",
        "attendance": {},
        "leave": [],
        "absent": [],
        "in_lieu": [],
        "resigned": []
    }
    
    # 用于收集日期/班别（第一行通常有）
    header_processed = False
    
    for line in lines:
        # 解析日期和班别（通常在第一行）
        # 格式: "6月11日，白班应出36人，实际出勤32人，请假1人，自离3人"
        date_match = re.search(r'(\d{1,2})[月\-\/](\d{1,2})[日号\-\/](\d{4})?', line)
        shift_match = re.search(r'(白班|夜班|长白班|A班|B班)', line)
        
        if date_match and not result["date"]:
            m = date_match.group(1)
            d = date_match.group(2)
            y = date_match.group(3) or "2026"
            result["date"] = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        
        if shift_match and not result.get("shift_set"):
            shift = shift_match.group(1)
            shift_map = {"白班": "白班", "A班": "白班", "夜班": "夜班", "B班": "夜班", "长白班": "长白班"}
            result["shift"] = shift_map.get(shift, "白班")
            result["shift_set"] = True
        
        # 解析岗位：人员列表
        # 格式: "配料：刘虎、蒋江坤、黄春、宋春祥、郑成功"
        # 或者: "正1D836涂布人员：李景均、李培嘉、"
        if not date_match and not shift_match:
            _parse_role_line(line, result)
        elif date_match and not result["date"]:
            _parse_role_line(line, result)
        else:
            # 头部行可能同时包含"请假：宁福"之类的内容
            _parse_role_line(line, result)
    
    # 移除临时标志
    result.pop("shift_set", None)
    
    # 如果没有日期，默认今天
    if not result["date"]:
        result["date"] = datetime.today().strftime("%Y-%m-%d")
    
    return result


def _parse_role_line(line: str, result: Dict) -> None:
    """解析一行岗位/角色数据

    格式:
      "岗位名：用户1、用户2、用户3"
      "请假：宁福"
      "调休：李景均"
      "自离：赵红丽、韦广阔、周雨馨"
      "未到岗：员工A、员工B"
    """
    # 标准化冒号
    line = line.strip()
    if not line:
        return
    
    # 匹配 "岗位名：用户1、用户2..." 格式
    # 支持中英文冒号、"人员"后缀
    m = re.match(r'^([^:：]+?)[：:]\s*(.+)$', line)
    if not m:
        return
    
    role_name_raw = m.group(1).strip()
    users_str = m.group(2).strip()
    
    # 去掉"人员"后缀（如"正1D836涂布人员" → "正1D836涂布"）
    role_name = re.sub(r'人员$', '', role_name_raw)
    role_name = role_name.strip()
    
    # 如果行尾有逗号、顿号，去掉（用户输入的格式问题）
    users_str = users_str.rstrip(',，、、.。 \t')
    
    if not users_str:
        return
    
    # 拆分用户列表
    users = []
    for u in re.split(r'[、,，\s]+', users_str):
        u = u.strip()
        if u and u not in ('', '无', '无人员', '空', '0'):
            users.append(u)
    
    if not users:
        return
    
    # 判断岗位类型（请假/自离/未到岗/调休/普通岗位）
    role_keywords = {
        "请假": "leave",
        "未到岗": "absent",
        "缺勤": "absent",
        "调休": "in_lieu",
        "自离": "resigned",
        "离职": "resigned",
        "": None,
    }

    # ★ 使用关键字匹配映射到基础岗位
    # 注意：职能现在是普通岗位，不是特殊状态
    base_role = get_base_role(role_name)

    # 只有特殊状态（请假/自离/未到岗/调休）才走特殊处理
    if role_name in role_keywords and role_keywords[role_name] in ("leave", "absent", "resigned", "in_lieu"):
        key = role_keywords[role_name]
        result[key].extend(users)
    else:
        # 普通岗位，用基础岗位名
        role_name = base_role
        # 已有则合并，无则新增
        if role_name in result["attendance"]:
            for u in users:
                if u not in result["attendance"][role_name]:
                    result["attendance"][role_name].append(u)
        else:
            result["attendance"][role_name] = users
