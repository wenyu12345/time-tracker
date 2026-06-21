from flask import Blueprint, jsonify, request
from utils.db import get_db
from datetime import datetime
from config import BEIJING_TIMEZONE
import logging

wooden_fish_bp = Blueprint('wooden_fish', __name__)

@wooden_fish_bp.route('/tap', methods=['POST'])
def record_tap():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        tap_count = data.get('count', 1)

        if not user_id:
            return jsonify({'error': '用户ID不能为空'}), 400

        now = datetime.now(BEIJING_TIMEZONE)
        current_date = now.strftime('%Y-%m-%d')

        db = get_db()

        existing_record = db.execute(
            '''SELECT id, tap_count 
            FROM wooden_fish_taps 
            WHERE user_id = ? AND tap_date = ?''',
            (user_id, current_date)
        ).fetchone()

        if existing_record:
            new_count = existing_record['tap_count'] + tap_count
            db.execute(
                '''UPDATE wooden_fish_taps 
                SET tap_count = ?, updated_at = ? 
                WHERE id = ?''',
                (new_count, now, existing_record['id'])
            )
            db.commit()
            return jsonify({'message': '敲击次数更新成功', 'count': new_count}), 200
        else:
            db.execute(
                '''INSERT INTO wooden_fish_taps 
                (user_id, tap_count, tap_date, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?)''',
                (user_id, tap_count, current_date, now, now)
            )
            db.commit()
            return jsonify({'message': '敲击次数记录成功', 'count': tap_count}), 201
    except Exception as e:
        logging.error(f"记录敲击次数失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@wooden_fish_bp.route('/daily-count/<int:user_id>', methods=['GET'])
def get_daily_count(user_id):
    try:
        now = datetime.now(BEIJING_TIMEZONE)
        current_date = now.strftime('%Y-%m-%d')

        db = get_db()

        record = db.execute(
            '''SELECT tap_count 
            FROM wooden_fish_taps 
            WHERE user_id = ? AND tap_date = ?''',
            (user_id, current_date)
        ).fetchone()

        count = record['tap_count'] if record else 0
        return jsonify({'count': count}), 200
    except Exception as e:
        logging.error(f"获取当日敲击次数失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@wooden_fish_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        now = datetime.now(BEIJING_TIMEZONE)
        current_date = now.strftime('%Y-%m-%d')

        db = get_db()

        leaderboard = db.execute(
            '''SELECT u.username, wft.tap_count 
            FROM wooden_fish_taps wft 
            JOIN users u ON wft.user_id = u.id 
            WHERE wft.tap_date = ? 
            ORDER BY wft.tap_count DESC 
            LIMIT 10''',
            (current_date,)
        ).fetchall()

        leaderboard_list = [
            {
                'username': record['username'],
                'count': record['tap_count']
            }
            for record in leaderboard
        ]

        return jsonify({'leaderboard': leaderboard_list}), 200
    except Exception as e:
        logging.error(f"获取排行榜数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@wooden_fish_bp.route('/leaderboard/total', methods=['GET'])
def get_total_leaderboard():
    try:
        db = get_db()

        leaderboard = db.execute(
            '''SELECT u.username, SUM(wft.tap_count) as total_count 
            FROM wooden_fish_taps wft 
            JOIN users u ON wft.user_id = u.id 
            GROUP BY u.id, u.username 
            ORDER BY total_count DESC 
            LIMIT 10'''
        ).fetchall()

        leaderboard_list = [
            {
                'username': record['username'],
                'count': record['total_count']
            }
            for record in leaderboard
        ]

        return jsonify({'leaderboard': leaderboard_list}), 200
    except Exception as e:
        logging.error(f"获取总排行榜数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500