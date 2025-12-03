#!/usr/bin/env python3
"""
Oton-Zzz - 寝落ち検知テレビ自動OFF システム
メインエントリーポイント（統合版）
"""

import sys
import os
import subprocess
import argparse
import threading
import time


import socket

def get_ip_address():
    """現在のIPアドレスを取得"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception:
        return "localhost"


def run_dashboard(port=5000):
    """ダッシュボードを別スレッドで実行"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env['DASHBOARD_PORT'] = str(port)

    ip_address = get_ip_address()

    print(f"📊 ダッシュボードを起動中... (ポート: {port})")
    print(f"   ブラウザで http://{ip_address}:{port} を開いてください")

    try:
        subprocess.run(
            [sys.executable, os.path.join(script_dir, 'src', 'dashboard.py')],
            env=env,
            cwd=script_dir
        )
    except Exception as e:
        print(f"⚠️  ダッシュボードエラー: {e}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Oton-Zzz - 寝落ち検知テレビ自動OFFシステム',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 main.py                      # メインプログラム + ダッシュボードを起動
  python3 main.py --calibrate          # キャリブレーションのみ実行
  python3 main.py --test               # システムテストのみ実行
  python3 main.py --setup              # 初回セットアップのみ実行
        """
    )

    parser.add_argument(
        '--calibrate',
        action='store_true',
        help='キャリブレーションを実行'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='システムテストを実行'
    )

    parser.add_argument(
        '--setup',
        action='store_true',
        help='初回セットアップを実行'
    )

    parser.add_argument(
        '--dashboard-only',
        action='store_true',
        help='ダッシュボードのみ起動'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='ダッシュボードのポート番号（デフォルト: 5000）'
    )

    args = parser.parse_args()

    # カレントディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # srcディレクトリをパスに追加
    sys.path.append(os.path.join(script_dir, 'src'))

    print("""
╔═══════════════════════════════════════════════════════════╗
║                  Oton-Zzz システム                        ║
║          寝落ち検知テレビ自動OFFシステム                  ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # キャリブレーションのみ
    if args.calibrate:
        print("キャリブレーションを起動します...")
        print("音声の指示に従ってください\n")
        try:
            subprocess.run([sys.executable, 'src/calibration.py'])
        except KeyboardInterrupt:
            print("\n\n✓ キャリブレーションを終了しました")
        return

    # システムテストのみ
    if args.test:
        print("システムテストを実行します...\n")
        run_system_test()
        return

    # セットアップのみ
    if args.setup:
        print("セットアップを実行します...\n")
        run_setup()
        return

    # ダッシュボードのみ
    if args.dashboard_only:
        ip_address = get_ip_address()
        print(f"ダッシュボードを起動します（ポート: {args.port}）...")
        print(f"ブラウザで http://{ip_address}:{args.port} を開いてください")
        print("Ctrl+C で終了できます\n")

        env = os.environ.copy()
        env['DASHBOARD_PORT'] = str(args.port)

        try:
            subprocess.run([sys.executable, 'src/dashboard.py'], env=env)
        except KeyboardInterrupt:
            print("\n\n✓ ダッシュボードを終了しました")
        return

    # デフォルト: メインプログラム + ダッシュボードを同時起動
    print("メインプログラムとダッシュボードを起動します...")

    # 初回起動チェック: config.jsonがない場合はキャリブレーション実行
    config_file = os.path.join(script_dir, 'config', 'config.json')
    if not os.path.exists(config_file):
        print("\n初回起動を検出しました。")
        print("最適な設定のため、キャリブレーションを実行します。")
        print("="*60)

        # キャリブレーション実行
        try:
            subprocess.run([sys.executable, 'src/calibration.py'])
        except KeyboardInterrupt:
            print("\n\nキャリブレーションを中断しました")
            print("デフォルト設定でメインプログラムを起動します")

        print("\n" + "="*60)
        print("キャリブレーション完了。メインプログラムを起動します。")
        print("="*60)
        time.sleep(2)

    print("Ctrl+C で終了できます\n")

    # ダッシュボードを別スレッドで起動
    dashboard_thread = threading.Thread(
        target=run_dashboard,
        args=(args.port,),
        daemon=True
    )
    dashboard_thread.start()

    # ダッシュボードの起動を少し待つ
    time.sleep(2)

    # メインプログラムを実行
    print("\n🚀 メインプログラムを起動します...")
    print("="*60)

    try:
        subprocess.run([sys.executable, 'src/core.py'])
    except KeyboardInterrupt:
        print("\n\n✓ プログラムを終了しました")


def run_system_test():
    """システムテストを実行"""
    print("=" * 60)
    print("システムテスト")
    print("=" * 60)

    # 1. 必要なモジュールのインポートテスト
    print("\n1. モジュールインポートテスト...")
    try:
        import cv2
        import mediapipe as mp
        from src.config import ConfigManager
        from src.voice import VoiceController
        from src.detector import SleepDetector
        from src.db import DatabaseManager
        from src.led import LEDController
        print("  ✓ 全モジュールのインポート成功")
    except Exception as e:
        print(f"  ✗ モジュールインポート失敗: {e}")
        return

    # 2. 設定ファイルのテスト
    print("\n2. 設定ファイルテスト...")
    try:
        config_mgr = ConfigManager()
        params = config_mgr.get_sleep_detection_params()
        print(f"  ✓ 設定ファイル読み込み成功")
        print(f"    - まばたき閾値: {params.get('blink_threshold', 0.5)}")
        print(f"    - ゲージ最大値: {params.get('gauge_max', 5.0)}")
    except Exception as e:
        print(f"  ✗ 設定ファイル読み込み失敗: {e}")

    # 3. カメラテスト
    print("\n3. カメラテスト...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"  ✓ カメラ動作OK（解像度: {frame.shape[1]}x{frame.shape[0]}）")
            else:
                print("  ✗ カメラからフレーム取得失敗")
            cap.release()
        else:
            print("  ✗ カメラを開けませんでした")
    except Exception as e:
        print(f"  ✗ カメラテスト失敗: {e}")

    # 4. LEDテスト
    print("\n4. LEDテスト...")
    try:
        led = LEDController()
        print("  ✓ LED初期化成功")
        print("  テストパターンを実行...")
        led.power_on()
        time.sleep(1)
        led.power_off()
        time.sleep(1)
        led.warning()
        time.sleep(2)
        led.off()
        led.cleanup()
        print("  ✓ LEDテスト完了")
    except Exception as e:
        print(f"  ✗ LEDテスト失敗: {e}")

    # 5. 音声テスト
    print("\n5. 音声テスト...")
    try:
        voice = VoiceController()
        print("  ✓ 音声コントローラー初期化成功")
        print("  テスト音声を再生します...")
        voice.speak_sync("テスト")
        print("  ✓ 音声再生完了")
    except Exception as e:
        print(f"  ✗ 音声テスト失敗: {e}")

    # 6. データベーステスト
    print("\n6. データベーステスト...")
    try:
        db_mgr = DatabaseManager()
        stats = db_mgr.get_weekly_stats()
        print(f"  ✓ データベース読み込み成功")
        print(f"    - 睡眠検知回数: {stats.get('sleep_count', 0)}回")
    except Exception as e:
        print(f"  ✗ データベーステスト失敗: {e}")

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)


def run_setup():
    """初回セットアップ"""
    print("=" * 60)
    print("Oton-Zzz 初回セットアップ")
    print("=" * 60)

    print("\n設定ファイルを確認しています...")

    # 設定ファイルの初期化
    try:
        from src.config import ConfigManager
        config_mgr = ConfigManager()
        print("✓ 設定ファイルを作成しました")
    except Exception as e:
        print(f"✗ 設定ファイル作成失敗: {e}")
        return

    print("\nキャリブレーションを実行しますか？")
    print("（個人に最適化した設定を作成します）")
    response = input("実行する場合は 'y' を入力: ")

    if response.lower() == 'y':
        print("\nキャリブレーションを開始します...")
        subprocess.run([sys.executable, 'src/calibration.py'])
    else:
        print("デフォルト設定で続行します")

    print("\n" + "=" * 60)
    print("セットアップ完了")
    print("=" * 60)
    print("\n次のコマンドでシステムを起動できます:")
    print("  python3 main.py")


if __name__ == '__main__':
    main()
