#!/usr/bin/env python3
"""
IR受信テストスクリプト
リモコンボタンを押して、正しく受信できるかテストします
"""

import subprocess
import sys

def test_ir_receive():
    """IR受信のテスト"""
    print("=" * 60)
    print("IR受信テスト")
    print("=" * 60)
    print("\nリモコンのボタンを押してください（10秒以内）...\n")

    try:
        result = subprocess.run(
            ['ir-ctl', '-d', '/dev/lirc0', '-r', '-1', '-t', '10000'],
            capture_output=True,
            text=True,
            timeout=12
        )

        if result.returncode == 0 and result.stdout.strip():
            print("✓ 受信成功！\n")
            print("受信データ:")
            print("-" * 60)
            print(result.stdout)
            print("-" * 60)

            # NECフォーマットかチェック
            if 'pulse 9000' in result.stdout and 'space 4500' in result.stdout:
                print("\n✓ NECフォーマットの信号を検出しました")
            else:
                print("\n⚠️  NEC以外のフォーマットの可能性があります")

            return True
        else:
            print("✗ タイムアウト: リモコン信号が受信できませんでした")
            if result.stderr:
                print(f"エラー: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ タイムアウト")
        return False
    except FileNotFoundError:
        print("✗ ir-ctlコマンドが見つかりません")
        print("  以下のコマンドでインストールしてください:")
        print("  sudo apt install v4l-utils")
        return False
    except PermissionError:
        print("✗ /dev/lirc0 へのアクセス権限がありません")
        print("  ユーザーがvideoグループに所属しているか確認してください:")
        print("  groups")
        return False
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False

def test_device_exists():
    """デバイスファイルの存在確認"""
    import os
    print("=" * 60)
    print("デバイスファイル確認")
    print("=" * 60)

    if os.path.exists('/dev/lirc0'):
        print("✓ /dev/lirc0 が存在します")
        # 権限確認
        result = subprocess.run(['ls', '-la', '/dev/lirc0'], capture_output=True, text=True)
        print(result.stdout)
        return True
    else:
        print("✗ /dev/lirc0 が見つかりません")
        print("\n以下を確認してください:")
        print("1. /boot/firmware/config.txt に以下の設定があるか:")
        print("   dtoverlay=gpio-ir-tx,gpio_pin=17")
        print("   dtoverlay=gpio-ir-rx,gpio_pin=18")
        print("2. 再起動してカーネルドライバを有効化:")
        print("   sudo reboot")
        return False

if __name__ == '__main__':
    print("\n🔧 IR受信機能テストツール\n")

    # Step 1: デバイスファイル確認
    if not test_device_exists():
        sys.exit(1)

    print()

    # Step 2: IR受信テスト
    if test_ir_receive():
        print("\n✓ すべてのテストに合格しました！")
        print("  ir_sleep_detector.py を実行できます。")
    else:
        print("\n✗ テストに失敗しました。上記のエラーを確認してください。")
        sys.exit(1)
