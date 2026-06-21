from flask import Blueprint, request, jsonify
from utils.db import get_db
from datetime import datetime
import logging

sudoku_bp = Blueprint('sudoku', __name__)

def get_current_time():
    from config import BEIJING_TIMEZONE
    return datetime.now(BEIJING_TIMEZONE).isoformat()

@sudoku_bp.route('/scores/<int:user_id>', methods=['GET'])
def get_sudoku_scores(user_id):
    try:
        db = get_db()
        score_data = db.execute(
            'SELECT * FROM sudoku_scores WHERE user_id = ?', 
            (user_id,)
        ).fetchone()

        if score_data:
            return jsonify(dict(score_data)), 200
        else:
            return jsonify({
                'user_id': user_id,
                'level': 1,
                'exp': 0,
                'wins': 0,
                'total_games': 0
            }), 200
    except Exception as e:
        logging.error(f"获取数独积分失败: {str(e)}")
        return jsonify({'error': '获取积分失败'}), 500

@sudoku_bp.route('/scores', methods=['POST'])
def update_sudoku_scores():
    try:
        data = request.get_json()
        
        required_fields = ['user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        user_id = data['user_id']
        level = data.get('level', 1)
        exp = data.get('exp', 0)
        wins = data.get('wins', 0)
        total_games = data.get('total_games', 0)

        db = get_db()
        
        existing = db.execute(
            'SELECT id FROM sudoku_scores WHERE user_id = ?', 
            (user_id,)
        ).fetchone()

        current_time = get_current_time()

        if existing:
            db.execute('''
                UPDATE sudoku_scores 
                SET level = ?, exp = ?, wins = ?, total_games = ?, updated_at = ?
                WHERE user_id = ?
            ''', (level, exp, wins, total_games, current_time, user_id))
        else:
            db.execute('''
                INSERT INTO sudoku_scores (user_id, level, exp, wins, total_games, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, level, exp, wins, total_games, current_time, current_time))

        db.commit()
        return jsonify({'message': '数独积分更新成功'}), 200
    except Exception as e:
        logging.error(f"更新数独积分失败: {str(e)}")
        return jsonify({'error': '更新积分失败'}), 500

@sudoku_bp.route('/leaderboard', methods=['GET'])
def get_sudoku_leaderboard():
    try:
        db = get_db()
        
        leaderboard = db.execute('''
            SELECT u.username, s.level, s.exp 
            FROM sudoku_scores s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.level DESC, s.exp DESC
            LIMIT 10
        ''').fetchall()

        result = [dict(row) for row in leaderboard]
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"获取数独排行榜失败: {str(e)}")
        return jsonify({'error': '获取排行榜失败'}), 500
