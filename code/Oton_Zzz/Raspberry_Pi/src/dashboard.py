#!/usr/bin/env python3
"""
Oton-Zzz Webダッシュボード
Flaskを使用して睡眠ログと統計を表示
"""

from flask import Flask, render_template
from datetime import datetime, timezone, timedelta
import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import DatabaseManager

# カレントディレクトリをプロジェクトルートに設定
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
db_manager = DatabaseManager()

@app.template_filter('to_jst')
def to_jst_filter(iso_str):
    """UTCのISOフォーマット文字列をJSTのdatetimeオブジェクトに変換"""
    if not iso_str:
        return ""
    try:
        # ISOフォーマットからdatetimeオブジェクトを作成
        dt = datetime.fromisoformat(iso_str)
        # タイムゾーン情報がない場合はUTCとみなす
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # JSTに変換 (UTC+9)
        jst = timezone(timedelta(hours=9))
        return dt.astimezone(jst)
    except Exception:
        return iso_str

@app.route('/')
def index():
    """ダッシュボードのトップページ"""
    stats = db_manager.get_weekly_stats()
    daily_stats = db_manager.get_daily_stats()
    logs = db_manager.get_recent_logs(20)
    return render_template('index.html', stats=stats, logs=logs, daily_stats=daily_stats)

if __name__ == '__main__':
    # ポート番号を環境変数から取得（デフォルト: 5000）
    import os
    import socket
    port = int(os.environ.get('DASHBOARD_PORT', 5000))

    def get_ip_address():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address
        except Exception:
            return "localhost"

    ip_address = get_ip_address()

    # 外部からアクセス可能にするには host='0.0.0.0'
    # バックグラウンド実行のためdebug=False
    print(f"🚀 ダッシュボードを起動しました: http://{ip_address}:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
