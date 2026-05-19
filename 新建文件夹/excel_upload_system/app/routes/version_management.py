from flask import Blueprint, jsonify, render_template
import subprocess
import os
from datetime import datetime

version_management_bp = Blueprint('version_management', __name__)

def get_git_info():
    """获取Git版本信息"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 获取当前分支
        branch_result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else 'unknown'
        
        # 获取最新提交哈希
        commit_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        commit_hash = commit_result.stdout.strip()[:8] if commit_result.returncode == 0 else 'unknown'
        full_commit_hash = commit_result.stdout.strip() if commit_result.returncode == 0 else 'unknown'
        
        # 获取最新提交消息
        message_result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        commit_message = message_result.stdout.strip() if message_result.returncode == 0 else 'unknown'
        
        # 获取最新提交日期
        date_result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%ci'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        commit_date = date_result.stdout.strip() if date_result.returncode == 0 else 'unknown'
        
        # 获取标签列表
        tags_result = subprocess.run(
            ['git', 'tag', '--sort=-v:refname'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        tags = [tag.strip() for tag in tags_result.stdout.strip().split('\n') if tag.strip()] if tags_result.returncode == 0 else []
        
        # 获取所有远程仓库
        remote_result = subprocess.run(
            ['git', 'remote', '-v'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        remotes = []
        if remote_result.returncode == 0:
            for line in remote_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remotes.append({
                            'name': parts[0],
                            'url': parts[1]
                        })
        
        # 获取提交统计
        stat_result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        total_commits = stat_result.stdout.strip() if stat_result.returncode == 0 else '0'
        
        # 获取未提交的更改
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        has_changes = bool(status_result.stdout.strip()) if status_result.returncode == 0 else False
        changes_count = len(status_result.stdout.strip().split('\n')) if has_changes else 0
        
        return {
            'success': True,
            'git': {
                'branch': current_branch,
                'commit_hash': commit_hash,
                'full_commit_hash': full_commit_hash,
                'commit_message': commit_message,
                'commit_date': commit_date,
                'tags': tags,
                'remotes': remotes,
                'total_commits': total_commits,
                'has_changes': has_changes,
                'changes_count': changes_count
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'git': None
        }

def get_git_tags():
    """获取所有Git标签"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 获取标签列表（按日期倒序）
        tags_result = subprocess.run(
            ['git', 'tag', '--sort=-v:refname'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        
        tags = []
        if tags_result.returncode == 0:
            for tag in tags_result.stdout.strip().split('\n'):
                if tag.strip():
                    # 获取每个标签的详细信息
                    tag_info_result = subprocess.run(
                        ['git', 'show', '--quiet', '--format=%H%n%ci%n%s', tag.strip()],
                        cwd=base_dir,
                        capture_output=True,
                        text=True
                    )
                    
                    if tag_info_result.returncode == 0:
                        lines = tag_info_result.stdout.strip().split('\n')
                        if len(lines) >= 3:
                            tags.append({
                                'name': tag.strip(),
                                'hash': lines[0][:8],
                                'date': lines[1],
                                'message': lines[2]
                            })
        
        return {
            'success': True,
            'tags': tags
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'tags': []
        }

def get_git_commits(limit=20):
    """获取最近的提交记录"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        commits_result = subprocess.run(
            ['git', 'log', f'--max-count={limit}', '--pretty=format:%H%n%an%n%ae%n%ci%n%s%n%b---END---'],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        
        commits = []
        if commits_result.returncode == 0:
            entries = commits_result.stdout.strip().split('---END---\n')
            for entry in entries:
                if entry.strip():
                    lines = entry.strip().split('\n')
                    if len(lines) >= 6:
                        commits.append({
                            'hash': lines[0][:8],
                            'full_hash': lines[0],
                            'author_name': lines[1],
                            'author_email': lines[2],
                            'date': lines[3],
                            'subject': lines[4],
                            'body': '\n'.join(lines[5:]) if len(lines) > 5 else ''
                        })
        
        return {
            'success': True,
            'commits': commits
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'commits': []
        }

@version_management_bp.route('/version-management')
def index():
    """版本管理页面"""
    return render_template('version_management_docs.html')

@version_management_bp.route('/api/git-info')
def git_info():
    """获取Git版本信息API"""
    return jsonify(get_git_info())

@version_management_bp.route('/api/git-tags')
def git_tags():
    """获取Git标签列表API"""
    return jsonify(get_git_tags())

@version_management_bp.route('/api/git-commits')
def git_commits():
    """获取Git提交记录API"""
    return jsonify(get_git_commits(limit=20))

@version_management_bp.route('/api/git-commits/<int:limit>')
def git_commits_with_limit(limit):
    """获取指定数量的Git提交记录API"""
    if limit < 1 or limit > 100:
        limit = 20
    return jsonify(get_git_commits(limit=limit))
