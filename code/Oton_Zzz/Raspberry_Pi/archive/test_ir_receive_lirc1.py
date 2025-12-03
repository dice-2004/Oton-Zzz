#!/usr/bin/env python3
"""
IR受信テスト（/dev/lirc1用）
リモコンボタンを押して、正しく受信できるかテストします
"""

import subprocess
import sys

def test_ir_receive_lirc1():
    """IR受信のテスト（/dev/lirc1）"""
    print("=" * 60)
    print("IR受信テスト (/dev/lirc1)")
    print("=" * 60)
    print("\n📡 リモコンのボタンを押してください（10秒以内）...\n")

    try:
        result = subprocess.run(
            ['ir-ctl', '-d', '/dev/lirc1', '-r', '-1'],
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
            if 'pulse 9000' in result.stdout or 'pulse 8' in result.stdout:
                print("\n✓ IR信号を検出しました（NECフォーマットの可能性）")
            else:
                print("\n⚠️  IR信号を検出しました（フォーマット不明）")

            return True
        else:
            print("✗ タイムアウト: リモコン信号が受信できませんでした")
            if result.stderr:
                print(f"エラー: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ タイムアウト")
        return False
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False

if __name__ == '__main__':
    print("\n🔧 IR受信機能テストツール (lirc1)\n")

    if test_ir_receive_lirc1():
        print("\n✓ 受信テストに合格しました！")
        print("  これで自動登録が可能です。")
    else:
        print("\n✗ テストに失敗しました。")
        sys.exit(1)
