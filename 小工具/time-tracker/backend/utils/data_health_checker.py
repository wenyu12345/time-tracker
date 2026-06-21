"""数据体检器 - 检查考勤系统数据健康度

检查项目：
1. 重复工时记录 - 同一用户同一天有多条工时记录
2. 异常工时值 - 工时不是标准值（480/660/690分钟）
3. 用户无岗位 - 用户在 time_records 中但没有关联 user_roles
4. 自离人员有出勤 - 标记为"自离"但 description 为空（正常出勤）
5. 请假人员有出勤 - 标记为"请假"但 description 为空（正常出勤）
6. 岗位孤立 - user_roles 中有岗位但 time_records 中无记录
7. 日期异常 - 工时记录日期在未来或过于久远（<2024-01-01）
8. 用户孤立 - time_records 中有记录但 users 表中无此人
9. 工时为0但非请假 - 工时为0且不是请假/自离/未到岗
10. 多岗位用户 - 同一用户在 user_roles 中有多个不同岗位
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class DataHealthChecker:
    """数据体检器"""

    # 标准工时值（分钟）
    VALID_DURATIONS = {240, 480, 660, 690, 720}
    # 最早允许日期
    MIN_DATE = "2024-01-01"
    # 最大允许日期（今天+7天缓冲）
    MAX_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    def __init__(self, db):
        """初始化体检器
        
        Args:
            db: SQLite 数据库连接（来自 utils.db.get_db()）
        """
        self.db = db
        self.issues: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}

    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有体检项目
        
        Returns:
            包含体检结果的字典
        """
        self.issues = []
        self.stats = self._get_basic_stats()

        self._check_duplicate_records()
        self._check_abnormal_duration()
        self._check_users_without_role()
        self._check_resigned_has_attendance()
        self._check_leave_has_attendance()
        self._check_orphan_roles()
        self._check_abnormal_dates()
        self._check_orphan_users()
        self._check_zero_duration_not_leave()
        self._check_multi_role_users()

        return self.get_report()

    def _get_basic_stats(self) -> Dict[str, Any]:
        """获取基础统计"""
        stats = {}

        # 用户数
        r = self.db.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        stats['total_users'] = r['cnt']

        # 工时记录数
        r = self.db.execute("SELECT COUNT(*) as cnt FROM time_records").fetchone()
        stats['total_time_records'] = r['cnt']

        # 考勤记录数
        r = self.db.execute("SELECT COUNT(*) as cnt FROM attendance_records").fetchone()
        stats['total_attendance_records'] = r['cnt']

        # 岗位数
        r = self.db.execute("SELECT COUNT(*) as cnt FROM roles").fetchone()
        stats['total_roles'] = r['cnt']

        # 工时记录涉及的用户数
        r = self.db.execute(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM time_records"
        ).fetchone()
        stats['users_with_records'] = r['cnt']

        return stats

    def _add_issue(self, level: str, category: str, title: str,
                   description: str, count: int, detail: List[Any],
                   auto_fix_sql: Optional[str] = None,
                   auto_fix_params: Optional[tuple] = None):
        """添加一个问题项"""
        self.issues.append({
            'level': level,          # critical / warning / info
            'category': category,     # 类别标识
            'title': title,          # 简洁标题
            'description': description,  # 详细说明
            'count': count,          # 影响数量
            'detail': detail,        # 详细数据列表
            'auto_fix_sql': auto_fix_sql,
            'auto_fix_params': auto_fix_params,
        })

    # ===== 检查1: 重复工时记录 =====
    def _check_duplicate_records(self):
        """同一用户同一天有多条工时记录"""
        rows = self.db.execute("""
            SELECT user_id, DATE(start_time) as date_str, COUNT(*) as cnt,
                   GROUP_CONCAT(id) as record_ids
            FROM time_records
            GROUP BY user_id, DATE(start_time)
            HAVING cnt > 1
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知用户(ID={r['user_id']})"
            detail.append({
                'username': username,
                'date': r['date_str'],
                'count': r['cnt'],
                'record_ids': r['record_ids'].split(',')
            })

        self._add_issue(
            level='critical' if len(detail) > 0 else 'info',
            category='duplicate_records',
            title='重复工时记录',
            description='同一用户同一天有多条工时记录，会导致工时重复计算。'
                        '建议：保留最早记录，删除其余记录。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查2: 异常工时值 =====
    def _check_abnormal_duration(self):
        """工时不是标准值"""
        rows = self.db.execute(f"""
            SELECT tr.id, tr.user_id, tr.duration, tr.start_time, tr.description
            FROM time_records tr
            WHERE tr.duration NOT IN {tuple(self.VALID_DURATIONS)}
            AND tr.description NOT IN ('请假', '自离', '未到岗')
            ORDER BY tr.start_time DESC
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            hours = r['duration'] / 60
            detail.append({
                'id': r['id'],
                'username': username,
                'duration_min': r['duration'],
                'duration_hours': f"{hours:.1f}h",
                'date': r['start_time'][:10],
                'description': r['description'] or '(无)'
            })

        self._add_issue(
            level='warning' if len(detail) > 0 else 'info',
            category='abnormal_duration',
            title='异常工时值',
            description='工时不是标准值（白班660分/夜班690分/半天240分）。'
                        '可能原因：手动修改、数据导入错误。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查3: 用户无岗位 =====
    def _check_users_without_role(self):
        """用户在 time_records 中但没有关联 user_roles"""
        rows = self.db.execute("""
            SELECT DISTINCT tr.user_id, tr.start_time
            FROM time_records tr
            LEFT JOIN user_roles ur ON tr.user_id = ur.user_id
            WHERE ur.user_id IS NULL
            ORDER BY tr.start_time DESC
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            detail.append({
                'user_id': r['user_id'],
                'username': username,
                'last_record': r['start_time'][:10]
            })

        self._add_issue(
            level='warning' if len(detail) > 0 else 'info',
            category='users_without_role',
            title='用户无岗位',
            description='用户在工时记录中但没有分配岗位，'
                        '在考勤看板上不会显示。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查4: 自离人员有出勤 =====
    def _check_resigned_has_attendance(self):
        """description='自离' 但 duration>0（正常出勤）"""
        rows = self.db.execute("""
            SELECT tr.id, tr.user_id, tr.duration, tr.start_time
            FROM time_records tr
            WHERE tr.description = '自离' AND tr.duration > 0
            ORDER BY tr.start_time DESC
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            detail.append({
                'id': r['id'],
                'username': username,
                'duration': r['duration'],
                'date': r['start_time'][:10],
            })

        self._add_issue(
            level='info' if len(detail) > 0 else 'info',
            category='resigned_has_attendance',
            title='自离人员有工时（中途跑路）',
            description='标记为"自离"且有工时记录，说明该人员当天上了班但中途离开。'
                        '这是正常业务情况（如上班中途跑路），无需修复。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查5: 请假人员有出勤 =====
    def _check_leave_has_attendance(self):
        """description='请假' 但 duration>0（正常出勤）"""
        rows = self.db.execute("""
            SELECT tr.id, tr.user_id, tr.duration, tr.start_time
            FROM time_records tr
            WHERE tr.description = '请假' AND tr.duration > 0
            ORDER BY tr.start_time DESC
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            detail.append({
                'id': r['id'],
                'username': username,
                'duration': r['duration'],
                'date': r['start_time'][:10],
            })

        self._add_issue(
            level='warning' if len(detail) > 0 else 'info',
            category='leave_has_attendance',
            title='请假人员有正常出勤',
            description='标记为"请假"的记录但工时>0，说明该人员当天实际上班了。'
                        '可能是：标记错误或请假时长有误。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查6: 岗位孤立 =====
    def _check_orphan_roles(self):
        """user_roles 中有岗位但 time_records 中无当天记录"""
        # 找出所有有角色但无工时记录的用户（最近30天无记录）
        rows = self.db.execute("""
            SELECT DISTINCT ur.user_id, r.name as role_name
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            LEFT JOIN time_records tr ON tr.user_id = ur.user_id
              AND tr.start_time >= datetime('now', '-30 days')
            WHERE tr.id IS NULL
            ORDER BY ur.user_id
            LIMIT 50
        """).fetchall()

        detail = []
        seen = set()
        for r in rows:
            key = r['user_id']
            if key in seen:
                continue
            seen.add(key)
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            detail.append({
                'user_id': r['user_id'],
                'username': username,
                'last_role': r['role_name']
            })

        self._add_issue(
            level='info',
            category='orphan_roles',
            title='岗位孤立用户',
            description='有岗位分配但最近30天无工时记录。'
                        '可能原因：已离职、长期请假、或岗位分配未及时更新。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查7: 日期异常 =====
    def _check_abnormal_dates(self):
        """工时记录日期在未来或过于久远"""
        rows = self.db.execute("""
            SELECT id, user_id, start_time
            FROM time_records
            WHERE DATE(start_time) < ? OR DATE(start_time) > ?
            ORDER BY start_time DESC
            LIMIT 50
        """, (self.MIN_DATE, self.MAX_DATE)).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            is_future = r['start_time'][:10] > datetime.now().strftime("%Y-%m-%d")
            detail.append({
                'id': r['id'],
                'username': username,
                'date': r['start_time'][:10],
                'issue': '未来日期' if is_future else '日期过旧'
            })

        self._add_issue(
            level='critical' if len(detail) > 0 else 'info',
            category='abnormal_dates',
            title='日期异常记录',
            description='工时记录日期在系统允许范围之外。'
                        f'允许范围：{self.MIN_DATE} 至 {self.MAX_DATE}。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查8: 用户孤立 =====
    def _check_orphan_users(self):
        """time_records 中有记录但 users 表中无此人"""
        rows = self.db.execute("""
            SELECT DISTINCT tr.user_id, COUNT(*) as cnt
            FROM time_records tr
            LEFT JOIN users u ON u.id = tr.user_id
            WHERE u.id IS NULL
            GROUP BY tr.user_id
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            detail.append({
                'orphan_user_id': r['user_id'],
                'record_count': r['cnt'],
            })

        self._add_issue(
            level='critical' if len(detail) > 0 else 'info',
            category='orphan_users',
            title='孤立用户记录',
            description='工时记录关联了不存在的用户ID（users表中无此人）。'
                        '建议：清理这些孤立记录。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查9: 工时为0但非请假 =====
    def _check_zero_duration_not_leave(self):
        """工时为0但不是请假/自离/未到岗"""
        rows = self.db.execute("""
            SELECT id, user_id, duration, start_time, description
            FROM time_records
            WHERE duration = 0
            AND description NOT IN ('请假', '自离', '未到岗', '')
            ORDER BY start_time DESC
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            detail.append({
                'id': r['id'],
                'username': username,
                'date': r['start_time'][:10],
                'description': r['description'] or '(无)'
            })

        self._add_issue(
            level='warning' if len(detail) > 0 else 'info',
            category='zero_duration',
            title='工时为0但无状态',
            description='工时为0且没有请假/自离/未到岗标记，属于异常数据。',
            count=len(detail),
            detail=detail,
        )

    # ===== 检查10: 多岗位用户 =====
    def _check_multi_role_users(self):
        """同一用户在 user_roles 中有多个不同岗位"""
        rows = self.db.execute("""
            SELECT user_id, COUNT(DISTINCT role_id) as role_count,
                   GROUP_CONCAT(DISTINCT r.name) as roles
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            GROUP BY user_id
            HAVING role_count > 1
            LIMIT 50
        """).fetchall()

        detail = []
        for r in rows:
            user = self.db.execute(
                "SELECT username FROM users WHERE id = ?", (r['user_id'],)
            ).fetchone()
            username = user['username'] if user else f"未知(ID={r['user_id']})"
            detail.append({
                'user_id': r['user_id'],
                'username': username,
                'role_count': r['role_count'],
                'roles': r['roles'].split(',')
            })

        self._add_issue(
            level='info',
            category='multi_role_users',
            title='多岗位用户',
            description='同一用户分配了多个岗位。看板会显示优先级最高的岗位。'
                        '如非必要，建议每个用户只保留一个岗位。',
            count=len(detail),
            detail=detail,
        )

    def get_report(self) -> Dict[str, Any]:
        """获取体检报告"""
        critical_count = sum(1 for i in self.issues if i['level'] == 'critical')
        warning_count = sum(1 for i in self.issues if i['level'] == 'warning')
        info_count = sum(1 for i in self.issues if i['level'] == 'info')

        total_issues = sum(i['count'] for i in self.issues)

        # 健康评分（100分制）
        if self.stats['total_time_records'] == 0:
            health_score = 100
        else:
            # 每个问题扣分
            deduct = critical_count * 20 + warning_count * 5 + min(info_count, 10) * 0.5
            health_score = max(0, min(100, 100 - deduct))
            health_score = round(health_score, 1)

        # 健康等级
        if health_score >= 95:
            health_level = 'excellent'
            health_label = '优秀'
        elif health_score >= 80:
            health_level = 'good'
            health_label = '良好'
        elif health_score >= 60:
            health_level = 'warning'
            health_label = '需注意'
        else:
            health_level = 'critical'
            health_label = '需修复'

        return {
            'health_score': health_score,
            'health_level': health_level,
            'health_label': health_label,
            'stats': self.stats,
            'summary': {
                'critical_count': critical_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'total_issues': total_issues,
            },
            'issues': self.issues,
            'checked_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def auto_fix(self, category: str) -> Dict[str, Any]:
        """自动修复指定类别的问题
        
        Args:
            category: 问题类别（如 'duplicate_records'）
            
        Returns:
            修复结果
        """
        # 可自动修复的 SQL
        fix_sqls = {
            'duplicate_records': (
                '''DELETE FROM time_records
                   WHERE id NOT IN (
                       SELECT MIN(id) FROM time_records
                       GROUP BY user_id, DATE(start_time)
                   )''',
                None
            ),
            'orphan_users': (
                '''DELETE FROM time_records
                   WHERE user_id NOT IN (SELECT id FROM users)''',
                None
            ),
            'abnormal_dates': (
                '''DELETE FROM time_records
                   WHERE DATE(start_time) < '2024-01-01'
                      OR DATE(start_time) > date('now', '+7 days')''',
                None
            ),
        }

        if category not in fix_sqls:
            return {'success': False, 'message': f'{category} 暂无自动修复方案'}

        sql, params = fix_sqls[category]
        try:
            cur = self.db.execute(sql, params or ())
            self.db.commit()
            return {
                'success': True,
                'message': f'已修复 {category}，影响 {cur.rowcount} 条记录',
                'affected': cur.rowcount
            }
        except Exception as e:
            return {'success': False, 'message': f'修复失败: {str(e)}'}
