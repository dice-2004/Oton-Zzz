#!/usr/bin/env python3
"""
テレビ状態管理
テレビのON/OFF状態を追跡
"""

import json
import os
from datetime import datetime


class TVStateManager:
    """テレビ状態管理クラス"""

    def __init__(self, state_file='tv_state.json'):
        """
        初期化

        Args:
            state_file: 状態保存ファイル
        """
        self.state_file = state_file
        self.is_on = False
        self.last_toggle_time = None

        # 保存された状態を読み込み
        self.load_state()

    def load_state(self):
        """保存された状態を読み込み"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.is_on = data.get('is_on', False)
                    self.last_toggle_time = data.get('last_toggle_time')
                print(f"✓ テレビ状態を読み込みました: {'ON' if self.is_on else 'OFF'}")
            except Exception as e:
                print(f"✗ 状態ファイルの読み込みエラー: {e}")
                self.is_on = False
        else:
            print("✓ 新規のテレビ状態ファイルを作成します")
            self.is_on = False

    def save_state(self):
        """現在の状態を保存"""
        try:
            data = {
                'is_on': self.is_on,
                'last_toggle_time': self.last_toggle_time
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"✗ 状態ファイルの保存エラー: {e}")

    def toggle(self):
        """
        テレビの状態を切り替え（ON ⇔ OFF）

        Returns:
            bool: 切り替え後の状態（True=ON, False=OFF）
        """
        self.is_on = not self.is_on
        self.last_toggle_time = datetime.now().isoformat()
        self.save_state()

        status = "ON" if self.is_on else "OFF"
        print(f"📺 テレビ状態を切り替えました: {status}")

        return self.is_on

    def turn_off(self):
        """
        テレビをOFFにする

        Returns:
            bool: 実際にOFFにした場合True、既にOFFだった場合False
        """
        if self.is_on:
            self.is_on = False
            self.last_toggle_time = datetime.now().isoformat()
            self.save_state()
            print("📺 テレビをOFFにしました")
            return True
        else:
            print("📺 テレビは既にOFFです")
            return False

    def turn_on(self):
        """
        テレビをONにする

        Returns:
            bool: 実際にONにした場合True、既にONだった場合False
        """
        if not self.is_on:
            self.is_on = True
            self.last_toggle_time = datetime.now().isoformat()
            self.save_state()
            print("📺 テレビをONにしました")
            return True
        else:
            print("📺 テレビは既にONです")
            return False

    def get_status(self):
        """
        現在のテレビ状態を取得

        Returns:
            dict: {'is_on': bool, 'last_toggle_time': str}
        """
        return {
            'is_on': self.is_on,
            'last_toggle_time': self.last_toggle_time,
            'status': 'ON' if self.is_on else 'OFF'
        }


if __name__ == '__main__':
    """テスト用"""
    print("テレビ状態管理テスト")
    tv = TVStateManager()

    print(f"\n現在の状態: {tv.get_status()}")

    print("\nトグルテスト:")
    for i in range(3):
        tv.toggle()
        print(f"  状態: {tv.get_status()['status']}")

    print("\nOFF強制テスト:")
    tv.turn_off()
    tv.turn_off()  # 既にOFFの場合

    print("\nON強制テスト:")
    tv.turn_on()
    tv.turn_on()  # 既にONの場合

    print("\nテスト完了")
