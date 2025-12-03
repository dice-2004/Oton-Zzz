#!/usr/bin/env python3
"""
データベースマネージャー
睡眠ログとテレビ操作履歴をSQLiteで管理
"""

import sqlite3
import os
from datetime import datetime, timedelta


class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self, db_path='data/oton_zzz.db'):
        """
        初期化

        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        self._init_db()

        # 電気代計算用定数 (1kWhあたり31円、テレビ100Wと仮定)
        self.COST_PER_KWH = 31.0
        self.TV_WATTAGE = 100.0
        self.COST_PER_HOUR = (self.TV_WATTAGE / 1000.0) * self.COST_PER_KWH

    def _init_db(self):
        """データベースとテーブルの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # ログテーブル作成
        # event_type: 'SLEEP_DETECTED', 'TV_OFF', 'TV_ON', 'CANCELLED'
        # duration: 経過時間（秒）- SLEEP_DETECTEDの場合はStage1からOFFまでの時間
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            duration REAL DEFAULT 0,
            note TEXT
        )
        ''')

        conn.commit()
        conn.close()

    def log_event(self, event_type, duration=0, note=""):
        """
        イベントを記録

        Args:
            event_type: イベントの種類
            duration: 経過時間（秒）
            note: 備考
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute('''
        INSERT INTO logs (timestamp, event_type, duration, note)
        VALUES (?, ?, ?, ?)
        ''', (timestamp, event_type, duration, note))

        conn.commit()
        conn.close()
        print(f"📝 ログ記録: {event_type} ({duration}s) - {note}")

    def get_weekly_stats(self):
        """
        過去7日間の統計を取得

        Returns:
            dict: 統計データ
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 7日前の日時
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

        # 寝落ち回数（自動OFF回数）
        cursor.execute('''
        SELECT COUNT(*), SUM(duration) FROM logs
        WHERE event_type = 'SLEEP_DETECTED' AND timestamp > ?
        ''', (seven_days_ago,))

        result = cursor.fetchone()
        sleep_count = result[0] if result[0] else 0
        wasted_seconds = result[1] if result[1] else 0

        # 節約できた時間（推定）
        # 1回の寝落ちにつき、朝まで（平均4時間）テレビがついていたと仮定して計算
        # これは「もしOton-Zzzがなかったら」の推定値
        estimated_saved_hours = sleep_count * 4.0
        estimated_saved_money = estimated_saved_hours * self.COST_PER_HOUR

        # 実際に無駄になった電気代（Stage1〜OFFまでの時間）
        wasted_hours = wasted_seconds / 3600.0
        wasted_money = wasted_hours * self.COST_PER_HOUR

        conn.close()

        return {
            'sleep_count': sleep_count,
            'wasted_seconds': wasted_seconds,
            'wasted_money': round(wasted_money, 2),
            'estimated_saved_hours': estimated_saved_hours,
            'estimated_saved_money': round(estimated_saved_money, 2)
        }

    def get_daily_stats(self, days=7):
        """
        過去N日間の日別統計を取得
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = []
        today = datetime.now().date()

        for i in range(days):
            target_date = today - timedelta(days=i)
            date_str = target_date.isoformat()
            next_date_str = (target_date + timedelta(days=1)).isoformat()

            cursor.execute('''
            SELECT COUNT(*), SUM(duration) FROM logs
            WHERE event_type = 'SLEEP_DETECTED'
            AND timestamp >= ? AND timestamp < ?
            ''', (date_str, next_date_str))

            result = cursor.fetchone()
            count = result[0] if result[0] else 0
            duration = result[1] if result[1] else 0

            stats.append({
                'date': target_date.strftime('%m/%d'),
                'count': count,
                'duration': duration
            })

        conn.close()
        return list(reversed(stats))

    def get_recent_logs(self, limit=10):
        """最新のログを取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
        SELECT * FROM logs ORDER BY id DESC LIMIT ?
        ''', (limit,))

        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs


if __name__ == '__main__':
    """テスト用"""
    db = DatabaseManager()

    print("ログ記録テスト...")
    db.log_event('TV_ON', note="リモコン操作")
    db.log_event('SLEEP_DETECTED', duration=60, note="自動OFF")
    db.log_event('TV_OFF', note="リモコン操作")

    print("\n統計取得テスト:")
    stats = db.get_weekly_stats()
    print(f"今週の寝落ち回数: {stats['sleep_count']}回")
    print(f"無駄になった時間: {stats['wasted_seconds']}秒")
    print(f"無駄になった電気代: {stats['wasted_money']}円")
    print(f"推定節約額: {stats['estimated_saved_money']}円")

    print("\n最新ログ:")
    for log in db.get_recent_logs(3):
        print(f"{log['timestamp']}: {log['event_type']}")
