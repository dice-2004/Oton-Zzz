#!/usr/bin/env python3
"""
簡易IR送信テストツール
登録済みのNECコードを送信してテストします
"""

import subprocess
import sys

def test_ir_send(nec_code="0x20DF10EF"):
    """
    IR送信のテスト

    Args:
        nec_code: NECフォーマットのスキャンコード
    """
    print("=" * 60)
    print("IR送信テスト")
    print("=" * 60)
    print(f"\nNECコード: {nec_code} を送信します...\n")

    try:
        result = subprocess.run(
            ['ir-ctl', '-d', '/dev/lirc0', '-S', f'nec:{nec_code}'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print("✓ 送信成功！")
            print("  テレビなどの機器が反応したか確認してください。")
            return True
        else:
            print(f"✗ 送信失敗")
            if result.stderr:
                print(f"  エラー: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ エラー: {e}")
        return False

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        nec_code = sys.argv[1]
    else:
        nec_code = "0x20DF10EF"  # デフォルト（LGテレビの電源ボタン）
        print(f"使用方法: python3 {sys.argv[0]} <NECコード>")
        print(f"デフォルトコードを使用します: {nec_code}\n")

    if test_ir_send(nec_code):
        print("\n✓ テストに合格しました")
    else:
        print("\n✗ テストに失敗しました")
        sys.exit(1)
