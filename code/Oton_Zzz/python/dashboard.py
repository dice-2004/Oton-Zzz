#!/usr/bin/env python3
"""
Oton-Zzz Webダッシュボード
Flaskを使用して睡眠ログと統計を表示
"""

from flask import Flask, render_template
from database_manager import DatabaseManager

app = Flask(__name__)
db_manager = DatabaseManager()

@app.route('/')
def index():
    """ダッシュボードのトップページ"""
    stats = db_manager.get_weekly_stats()
    logs = db_manager.get_recent_logs(20)
    return render_template('index.html', stats=stats, logs=logs)

if __name__ == '__main__':
    # 外部からアクセス可能にするには host='0.0.0.0'
    print("🚀 ダッシュボードを起動しました: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
