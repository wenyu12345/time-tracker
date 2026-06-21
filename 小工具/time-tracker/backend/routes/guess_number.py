from flask import Blueprint, request, jsonify
from utils.db import get_db
import logging

bp = Blueprint('guess_number', __name__)

@bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400

        db = get_db()
        stats = db.execute(
            'SELECT * FROM guess_number_stats WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        if not stats:
            db.execute(
                'INSERT INTO guess_number_stats (user_id, total_games, wins) VALUES (?, ?, ?)',
                (user_id, 0, 0)
            )
            db.commit()
            stats = db.execute(
                'SELECT * FROM guess_number_stats WHERE user_id = ?',
                (user_id,)
            ).fetchone()

        return jsonify(dict(stats)), 200
    except Exception as e:
        logging.error(f"获取猜数字游戏统计数据失败: {str(e)}")
        return jsonify({'error': '获取统计数据失败'}), 500

@bp.route('/stats', methods=['POST'])
def update_stats():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        is_win = data.get('is_win', False)

        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400

        db = get_db()

        stats = db.execute(
            'SELECT * FROM guess_number_stats WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        if stats:
            total_games = stats['total_games'] + 1
            wins = stats['wins'] + (1 if is_win else 0)
            db.execute(
                '''UPDATE guess_number_stats 
                   SET total_games = ?, wins = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE user_id = ?''',
                (total_games, wins, user_id)
            )
        else:
            total_games = 1
            wins = 1 if is_win else 0
            db.execute(
                '''INSERT INTO guess_number_stats (user_id, total_games, wins) 
                   VALUES (?, ?, ?)''',
                (user_id, total_games, wins)
            )

        db.commit()

        updated_stats = db.execute(
            'SELECT * FROM guess_number_stats WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        return jsonify(dict(updated_stats)), 200
    except Exception as e:
        logging.error(f"更新猜数字游戏统计数据失败: {str(e)}")
        return jsonify({'error': '更新统计数据失败'}), 500

@bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        db = get_db()

        leaderboard = db.execute(
            '''SELECT g.user_id, u.username, g.total_games, g.wins, 
                   CASE WHEN g.total_games > 0 THEN ROUND((g.wins * 100.0) / g.total_games, 2) ELSE 0 END as win_rate 
               FROM guess_number_stats g 
               JOIN users u ON g.user_id = u.id 
               ORDER BY win_rate DESC'''
        ).fetchall()

        return jsonify([dict(item) for item in leaderboard]), 200
    except Exception as e:
        logging.error(f"获取猜数字游戏排行榜失败: {str(e)}")
        return jsonify({'error': '获取排行榜失败'}), 500