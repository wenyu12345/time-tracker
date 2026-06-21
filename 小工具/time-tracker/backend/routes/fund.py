from flask import Blueprint, request, jsonify
from utils.db import get_db
from datetime import datetime
import requests
import re
import logging

# 创建蓝图
fund_bp = Blueprint('fund', __name__)

# 钉钉机器人配置
DINGTALK_WEBHOOK = 'https://oapi.dingtalk.com/robot/send?access_token=96542078ec1e3ca21582ae18edeb6aedcfaf96bf3b4ec1f1f9ce98a2b6ba19a7'


def send_dingtalk_message(content):
    """发送钉钉消息"""
    try:
        data = {
            'msgtype': 'text',
            'text': {
                'content': content
            }
        }
        response = requests.post(DINGTALK_WEBHOOK, json=data, timeout=10)
        result = response.json()
        if result.get('errcode') == 0:
            logging.info(f"钉钉消息发送成功")
            return True
        else:
            logging.error(f"钉钉消息发送失败: {result}")
            return False
    except Exception as e:
        logging.error(f"发送钉钉消息异常: {e}")
        return False


def get_fund_holding_summary(user_id):
    """获取基金持仓摘要信息"""
    db = get_db()
    holdings = db.execute(
        '''SELECT * FROM fund_holdings 
        WHERE user_id = ? AND holding_status = 1
        ORDER BY created_at DESC''',
        (user_id,)
    ).fetchall()
    
    if not holdings:
        return None
    
    total_investment = 0
    total_value = 0
    total_profit = 0
    holding_details = []
    
    for h in holdings:
        holding_dict = dict(h)
        purchase_amount = holding_dict['purchase_amount'] or 0
        
        if holding_dict['current_price'] and holding_dict['purchase_price']:
            current_shares = holding_dict['current_shares'] or holding_dict['purchase_shares'] or 0
            current_value = holding_dict['current_price'] * current_shares
            profit = (holding_dict['current_price'] - holding_dict['purchase_price']) * current_shares
            profit_rate = ((holding_dict['current_price'] / holding_dict['purchase_price']) - 1) * 100
        else:
            current_value = purchase_amount
            profit = 0
            profit_rate = 0
        
        total_investment += purchase_amount
        total_value += current_value
        total_profit += profit
        
        holding_details.append({
            'name': holding_dict['fund_name'],
            'code': holding_dict['fund_code'],
            'current_price': holding_dict['current_price'],
            'value': current_value,
            'profit': profit,
            'profit_rate': profit_rate
        })
    
    total_profit_rate = (total_profit / total_investment * 100) if total_investment > 0 else 0
    
    return {
        'total_investment': total_investment,
        'total_value': total_value,
        'total_profit': total_profit,
        'total_profit_rate': total_profit_rate,
        'holdings': holding_details
    }


def push_fund_report():
    """推送基金报告到钉钉"""
    # 获取第一个用户的基金数据
    db = get_db()
    user = db.execute('SELECT id FROM users LIMIT 1').fetchone()
    if not user:
        logging.warning("没有用户，无法推送基金报告")
        return False
    
    user_id = user['id']
    summary = get_fund_holding_summary(user_id)
    if not summary:
        logging.warning("没有基金持仓，无法推送报告")
        return False
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    message_lines = [f"📊 基金持仓报告 @小艺\n"]
    message_lines.append(f"⏰ 推送时间: {now}")
    message_lines.append(f"💰 总投入: ¥{summary['total_investment']:.2f}")
    message_lines.append(f"📈 总市值: ¥{summary['total_value']:.2f}")
    
    profit_color = "📈" if summary['total_profit'] >= 0 else "📉"
    message_lines.append(f"{profit_color} 总收益: ¥{summary['total_profit']:.2f} ({summary['total_profit_rate']:.2f}%)\n")
    message_lines.append("📋 持仓明细:")
    
    for h in summary['holdings']:
        profit_sign = "+" if h['profit'] >= 0 else ""
        h_profit_color = "📈" if h['profit'] >= 0 else "📉"
        message_lines.append(
            f"{h_profit_color} {h['name']}\n"
            f"   估值: ¥{h['current_price'] or '-'}"
            f" | 市值: ¥{h['value']:.2f}"
            f" | 收益: {profit_sign}¥{h['profit']:.2f} ({profit_sign}{h['profit_rate']:.2f}%)"
        )
    
    content = '\n'.join(message_lines)
    return send_dingtalk_message(content)


# 基金亏损提醒配置
LOSS_THRESHOLD = 3.0  # 亏损阈值百分比


def check_fund_loss_alert():
    """检查单只基金是否达到亏损阈值，并发送钉钉提醒"""
    db = get_db()
    
    # 获取所有活跃持仓
    holdings = db.execute(
        '''SELECT * FROM fund_holdings 
        WHERE holding_status = 1 
        ORDER BY created_at DESC''',
    ).fetchall()
    
    if not holdings:
        return None
    
    alerts = []
    for h in holdings:
        holding_dict = dict(h)
        
        if not holding_dict['current_price'] or not holding_dict['purchase_price']:
            continue
        
        current_shares = holding_dict['current_shares'] or holding_dict['purchase_shares'] or 0
        current_value = holding_dict['current_price'] * current_shares
        purchase_value = holding_dict['purchase_price'] * current_shares
        profit_rate = ((holding_dict['current_price'] / holding_dict['purchase_price']) - 1) * 100
        
        # 检查是否达到亏损阈值（负收益率的绝对值 >= 阈值）
        if profit_rate <= -LOSS_THRESHOLD:
            alerts.append({
                'name': holding_dict['fund_name'],
                'code': holding_dict['fund_code'],
                'purchase_price': holding_dict['purchase_price'],
                'current_price': holding_dict['current_price'],
                'loss_rate': abs(profit_rate),
                'loss_amount': purchase_value - current_value,
                'current_value': current_value
            })
    
    return alerts if alerts else None


def push_fund_loss_alert():
    """推送基金亏损提醒到钉钉"""
    alerts = check_fund_loss_alert()
    if not alerts:
        logging.info("没有基金达到亏损阈值，无需提醒")
        return False
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    message_lines = [f"🚨 基金亏损提醒 @小艺\n"]
    message_lines.append(f"⏰ 检测时间: {now}")
    message_lines.append(f"⚠️ 以下基金亏损达到 {LOSS_THRESHOLD}%：\n")
    
    for alert in alerts:
        message_lines.append(
            f"📉 {alert['name']}\n"
            f"   成本价: ¥{alert['purchase_price']:.4f}"
            f" | 当前: ¥{alert['current_price']:.4f}"
            f" | 亏损: ¥{alert['loss_amount']:.2f} ({alert['loss_rate']:.2f}%)"
        )
    
    content = '\n'.join(message_lines)
    return send_dingtalk_message(content)


@fund_bp.route('/holdings', methods=['GET'])
def get_holdings():
    """获取用户的基金持仓列表"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    holdings = db.execute(
        '''SELECT * FROM fund_holdings 
        WHERE user_id = ? 
        ORDER BY holding_status DESC, created_at DESC''',
        (user_id,)
    ).fetchall()
    
    holdings_list = []
    for h in holdings:
        holding_dict = dict(h)
        # 计算当前收益
        if holding_dict['current_price'] and holding_dict['purchase_price']:
            profit = (holding_dict['current_price'] - holding_dict['purchase_price']) * (holding_dict['current_shares'] or holding_dict['purchase_shares'])
            profit_rate = ((holding_dict['current_price'] / holding_dict['purchase_price']) - 1) * 100
            current_value = holding_dict['current_price'] * (holding_dict['current_shares'] or holding_dict['purchase_shares'])
        else:
            profit = 0
            profit_rate = 0
            current_value = holding_dict['purchase_amount']
        
        holding_dict['profit'] = profit
        holding_dict['profit_rate'] = profit_rate
        holding_dict['current_value'] = current_value
        holdings_list.append(holding_dict)
    
    return jsonify({'holdings': holdings_list}), 200


@fund_bp.route('/holdings', methods=['POST'])
def create_holding():
    """创建新的基金持仓记录"""
    data = request.get_json()
    user_id = data.get('user_id')
    fund_name = data.get('fund_name')
    purchase_date = data.get('purchase_date')
    purchase_amount = data.get('purchase_amount')
    purchase_shares = data.get('purchase_shares')
    purchase_price = data.get('purchase_price')
    fund_code = data.get('fund_code', '')
    notes = data.get('notes', '')
    
    if not all([user_id, fund_name, purchase_date, purchase_amount, purchase_shares, purchase_price]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    try:
        cursor = db.execute(
            '''INSERT INTO fund_holdings 
            (user_id, fund_name, fund_code, purchase_date, purchase_amount, purchase_shares, purchase_price, current_price, current_shares, notes) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, fund_name, fund_code, purchase_date, purchase_amount, purchase_shares, purchase_price, purchase_price, purchase_shares, notes)
        )
        db.commit()
        
        holding_id = cursor.lastrowid
        return jsonify({'message': 'Holding created', 'id': holding_id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@fund_bp.route('/holdings/<int:holding_id>', methods=['PUT'])
def update_holding(holding_id):
    """更新基金持仓记录"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    # 检查权限
    holding = db.execute('SELECT id FROM fund_holdings WHERE id = ? AND user_id = ?', (holding_id, user_id)).fetchone()
    if not holding:
        return jsonify({'error': 'Holding not found'}), 404
    
    # 更新字段
    updates = []
    params = []
    
    allowed_fields = ['fund_name', 'fund_code', 'purchase_date', 'purchase_amount', 'purchase_shares', 'purchase_price', 'current_price', 'current_shares', 'holding_status', 'notes']
    for field in allowed_fields:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])
    
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.extend([holding_id, user_id])
        
        try:
            db.execute(
                f'UPDATE fund_holdings SET {", ".join(updates)} WHERE id = ? AND user_id = ?',
                params
            )
            db.commit()
            return jsonify({'message': 'Holding updated'}), 200
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'No updates'}), 200


@fund_bp.route('/holdings/<int:holding_id>', methods=['DELETE'])
def delete_holding(holding_id):
    """删除基金持仓记录"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    # 检查权限
    holding = db.execute('SELECT id FROM fund_holdings WHERE id = ? AND user_id = ?', (holding_id, user_id)).fetchone()
    if not holding:
        return jsonify({'error': 'Holding not found'}), 404
    
    try:
        db.execute('DELETE FROM fund_holdings WHERE id = ? AND user_id = ?', (holding_id, user_id))
        db.execute('DELETE FROM fund_returns WHERE holding_id = ?', (holding_id,))
        db.commit()
        return jsonify({'message': 'Holding deleted'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@fund_bp.route('/returns', methods=['GET'])
def get_returns():
    """获取基金收益记录"""
    user_id = request.args.get('user_id', type=int)
    holding_id = request.args.get('holding_id', type=int)
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    query = 'SELECT * FROM fund_returns WHERE user_id = ?'
    params = [user_id]
    
    if holding_id:
        query += ' AND holding_id = ?'
        params.append(holding_id)
    
    query += ' ORDER BY record_date DESC'
    
    returns = db.execute(query, params).fetchall()
    returns_list = [dict(r) for r in returns]
    
    return jsonify({'returns': returns_list}), 200


@fund_bp.route('/returns', methods=['POST'])
def create_return():
    """创建基金收益记录"""
    data = request.get_json()
    user_id = data.get('user_id')
    holding_id = data.get('holding_id')
    record_date = data.get('record_date')
    current_value = data.get('current_value')
    profit_loss = data.get('profit_loss')
    profit_loss_rate = data.get('profit_loss_rate')
    notes = data.get('notes', '')
    
    if not all([user_id, holding_id, record_date, current_value is not None, profit_loss is not None, profit_loss_rate is not None]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = get_db()
    try:
        cursor = db.execute(
            '''INSERT INTO fund_returns 
            (holding_id, user_id, record_date, current_value, profit_loss, profit_loss_rate, notes) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (holding_id, user_id, record_date, current_value, profit_loss, profit_loss_rate, notes)
        )
        db.commit()
        
        return_id = cursor.lastrowid
        return jsonify({'message': 'Return record created', 'id': return_id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@fund_bp.route('/summary', methods=['GET'])
def get_summary():
    """获取基金收益汇总"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    # 获取所有持仓
    holdings = db.execute('SELECT * FROM fund_holdings WHERE user_id = ?', (user_id,)).fetchall()
    
    total_invest = 0
    total_value = 0
    total_profit = 0
    
    for h in holdings:
        total_invest += h['purchase_amount']
        
        if h['current_price'] and h['purchase_price']:
            current_val = h['current_price'] * (h['current_shares'] or h['purchase_shares'])
            profit = (h['current_price'] - h['purchase_price']) * (h['current_shares'] or h['purchase_shares'])
        else:
            current_val = h['purchase_amount']
            profit = 0
        
        total_value += current_val
        total_profit += profit
    
    total_profit_rate = ((total_value / total_invest) - 1) * 100 if total_invest > 0 else 0
    
    return jsonify({
        'total_invest': total_invest,
        'total_value': total_value,
        'total_profit': total_profit,
        'total_profit_rate': total_profit_rate
    }), 200


@fund_bp.route('/daily-summary', methods=['GET'])
def get_daily_summary():
    """获取用户每日基金收益汇总（用于图表）"""
    user_id = request.args.get('user_id', type=int)
    days = request.args.get('days', type=int, default=30)  # 默认获取30天
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    # 获取用户的每日收益汇总
    query = '''
        SELECT 
            record_date,
            SUM(current_value) as total_value,
            SUM(profit_loss) as total_profit,
            AVG(profit_loss_rate) as avg_profit_rate
        FROM fund_returns 
        WHERE user_id = ?
        GROUP BY record_date
        ORDER BY record_date DESC
        LIMIT ?
    '''
    
    results = db.execute(query, (user_id, days)).fetchall()
    
    daily_data = []
    for row in results:
        daily_data.append({
            'date': row['record_date'],
            'total_value': row['total_value'],
            'total_profit': row['total_profit'],
            'avg_profit_rate': row['avg_profit_rate']
        })
    
    # 反转顺序，从旧到新
    daily_data.reverse()
    
    return jsonify({
        'daily_data': daily_data,
        'total_days': len(daily_data)
    }), 200


@fund_bp.route('/portfolio-history', methods=['GET'])
def get_portfolio_history():
    """获取用户组合历史（每只基金的历史收益）"""
    user_id = request.args.get('user_id', type=int)
    days = request.args.get('days', type=int, default=30)
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    
    # 获取该用户的所有持仓基金
    holdings = db.execute(
        'SELECT id, fund_name, fund_code FROM fund_holdings WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    
    portfolio_data = {}
    
    for holding in holdings:
        holding_id = holding['id']
        # 获取该基金的历史收益
        returns = db.execute(
            '''SELECT record_date, current_value, profit_loss, profit_loss_rate
            FROM fund_returns
            WHERE user_id = ? AND holding_id = ?
            ORDER BY record_date DESC
            LIMIT ?''',
            (user_id, holding_id, days)
        ).fetchall()
        
        history = []
        for row in returns:
            history.append({
                'date': row['record_date'],
                'value': row['current_value'],
                'profit': row['profit_loss'],
                'profit_rate': row['profit_loss_rate']
            })
        
        # 反转顺序
        history.reverse()
        
        portfolio_data[holding_id] = {
            'fund_name': holding['fund_name'],
            'fund_code': holding['fund_code'],
            'history': history
        }
    
    return jsonify({
        'portfolio_data': portfolio_data,
        'total_funds': len(holdings)
    }), 200


@fund_bp.route('/record-returns', methods=['POST'])
def record_returns():
    """手动触发记录当日收益"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    count = record_daily_fund_returns()
    
    return jsonify({
        'message': '收益记录完成',
        'recorded_count': count
    }), 200


@fund_bp.route('/info/<code>', methods=['GET'])
def get_fund_info(code):
    """获取基金实时信息（天天基金）"""
    try:
        # 使用天天基金接口
        url = f'http://fundgz.1234567.com.cn/js/{code}.js'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # 解析返回的JSONP
            text = response.text
            match = re.search(r'jsonpgz\((.*?)\);', text)
            if match:
                import json
                data = json.loads(match.group(1))
                return jsonify({
                    'code': data.get('fundcode'),
                    'name': data.get('name'),
                    'net_value': float(data.get('gsz', 0)),
                    'estimated_value': float(data.get('gsz', 0)),
                    'estimated_change': float(data.get('gszzl', 0)),
                    'date': data.get('gztime'),
                    'success': True
                })
        
        return jsonify({'error': '获取基金信息失败', 'success': False}), 200
    except Exception as e:
        print(f"获取基金信息异常: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@fund_bp.route('/refresh-prices', methods=['POST'])
def refresh_prices():
    """批量刷新所有基金价格"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': '用户ID必填'}), 400
        
        db = get_db()
        
        # 获取用户所有持仓的基金
        holdings = db.execute('SELECT * FROM fund_holdings WHERE user_id = ?', (user_id,)).fetchall()
        
        updated_count = 0
        for holding in holdings:
            if holding['fund_code']:
                try:
                    url = f'http://fundgz.1234567.com.cn/js/{holding["fund_code"]}.js'
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        text = response.text
                        match = re.search(r'jsonpgz\((.*?)\);', text)
                        if match:
                            import json
                            fund_data = json.loads(match.group(1))
                            net_value = float(fund_data.get('gsz', 0))
                            
                            if net_value > 0:
                                # 更新净值
                                db.execute(
                                    'UPDATE fund_holdings SET current_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                                    (net_value, holding['id'])
                                )
                                updated_count += 1
                except Exception as e:
                    print(f"更新基金 {holding['fund_code']} 失败: {e}")
                    continue
        
        db.commit()
        return jsonify({'message': f'成功更新 {updated_count} 只基金', 'count': updated_count}), 200
    except Exception as e:
        print(f"批量刷新价格异常: {e}")
        return jsonify({'error': str(e)}), 500


def auto_refresh_fund_prices():
    """自动刷新所有用户的基金净值并记录每日收益（定时任务调用）"""
    from utils.db import get_db
    import logging
    
    start_time = datetime.now()
    logging.info(f"开始执行自动刷新基金净值并记录收益任务，当前时间: {start_time}")
    
    try:
        db = get_db()
        
        # 获取所有有基金的用户
        cursor = db.execute('SELECT DISTINCT user_id FROM fund_holdings')
        user_ids = [row['user_id'] for row in cursor.fetchall()]
        
        total_updated = 0
        today = start_time.strftime('%Y-%m-%d')
        
        for user_id in user_ids:
            # 获取该用户所有有基金代码的持仓
            holdings = db.execute(
                'SELECT * FROM fund_holdings WHERE user_id = ? AND fund_code IS NOT NULL AND fund_code != ""',
                (user_id,)
            ).fetchall()
            
            for holding in holdings:
                try:
                    url = f'http://fundgz.1234567.com.cn/js/{holding["fund_code"]}.js'
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        text = response.text
                        match = re.search(r'jsonpgz\((.*?)\);', text)
                        if match:
                            import json
                            fund_data = json.loads(match.group(1))
                            net_value = float(fund_data.get('gsz', 0))
                            
                            if net_value > 0:
                                # 更新净值
                                db.execute(
                                    'UPDATE fund_holdings SET current_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                                    (net_value, holding['id'])
                                )
                                total_updated += 1
                                
                                # 计算并记录当日收益
                                current_shares = holding['current_shares'] or holding['purchase_shares'] or 0
                                current_value = net_value * current_shares
                                
                                if holding['purchase_price'] and holding['purchase_price'] > 0:
                                    purchase_value = holding['purchase_price'] * current_shares
                                    profit_loss = current_value - purchase_value
                                    profit_loss_rate = ((net_value / holding['purchase_price']) - 1) * 100
                                else:
                                    profit_loss = 0
                                    profit_loss_rate = 0
                                
                                # 检查今日是否已有记录，有则更新，无则创建
                                existing_record = db.execute(
                                    'SELECT id FROM fund_returns WHERE holding_id = ? AND user_id = ? AND record_date = ?',
                                    (holding['id'], user_id, today)
                                ).fetchone()
                                
                                if existing_record:
                                    db.execute(
                                        '''UPDATE fund_returns 
                                        SET current_value = ?, profit_loss = ?, profit_loss_rate = ?, updated_at = CURRENT_TIMESTAMP 
                                        WHERE id = ?''',
                                        (current_value, profit_loss, profit_loss_rate, existing_record['id'])
                                    )
                                else:
                                    db.execute(
                                        '''INSERT INTO fund_returns 
                                        (holding_id, user_id, record_date, current_value, profit_loss, profit_loss_rate, notes)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                        (holding['id'], user_id, today, current_value, profit_loss, profit_loss_rate, '自动生成')
                                    )
                except Exception as e:
                    logging.warning(f"更新基金 {holding['fund_code']} 失败: {e}")
                    continue
        
        db.commit()
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        message = f"自动刷新基金净值并记录收益任务完成，成功更新 {total_updated} 只基金，执行时间: {execution_time:.2f} 秒"
        logging.info(message)
        
        # 记录任务日志
        try:
            from utils.db import get_db
            db_log = get_db()
            db_log.execute(
                '''INSERT INTO scheduler_logs (job_name, status, message, start_time, end_time, execution_time)
                VALUES (?, ?, ?, ?, ?, ?)''',
                ('auto_refresh_fund_prices', 'success', message, start_time, end_time, execution_time)
            )
            db_log.commit()
        except:
            pass
            
    except Exception as e:
        logging.error(f"自动刷新基金净值并记录收益任务失败: {e}")
        try:
            db.rollback()
        except:
            pass


def record_daily_fund_returns():
    """记录所有基金当日的收益数据（单独调用）"""
    from utils.db import get_db
    import logging
    
    start_time = datetime.now()
    logging.info(f"开始执行记录基金每日收益任务，当前时间: {start_time}")
    
    try:
        db = get_db()
        today = start_time.strftime('%Y-%m-%d')
        
        # 获取所有活跃持仓
        holdings = db.execute(
            'SELECT * FROM fund_holdings WHERE holding_status = ? OR holding_status = ?',
            ('持有', '1')
        ).fetchall()
        
        recorded_count = 0
        for holding in holdings:
            if holding['current_price'] and holding['purchase_price']:
                current_shares = holding['current_shares'] or holding['purchase_shares'] or 0
                current_value = holding['current_price'] * current_shares
                purchase_value = holding['purchase_price'] * current_shares
                profit_loss = current_value - purchase_value
                profit_loss_rate = ((holding['current_price'] / holding['purchase_price']) - 1) * 100
                
                # 检查今日是否已有记录
                existing_record = db.execute(
                    'SELECT id FROM fund_returns WHERE holding_id = ? AND user_id = ? AND record_date = ?',
                    (holding['id'], holding['user_id'], today)
                ).fetchone()
                
                if existing_record:
                    db.execute(
                        '''UPDATE fund_returns 
                        SET current_value = ?, profit_loss = ?, profit_loss_rate = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?''',
                        (current_value, profit_loss, profit_loss_rate, existing_record['id'])
                    )
                else:
                    db.execute(
                        '''INSERT INTO fund_returns 
                        (holding_id, user_id, record_date, current_value, profit_loss, profit_loss_rate, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (holding['id'], holding['user_id'], today, current_value, profit_loss, profit_loss_rate, '手动记录')
                    )
                recorded_count += 1
        
        db.commit()
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        message = f"记录基金每日收益任务完成，成功记录 {recorded_count} 条，执行时间: {execution_time:.2f} 秒"
        logging.info(message)
        
        return recorded_count
            
    except Exception as e:
        logging.error(f"记录基金每日收益任务失败: {e}")
        try:
            db.rollback()
        except:
            pass
        return 0
