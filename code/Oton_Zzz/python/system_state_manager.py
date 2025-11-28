#!/usr/bin/env python3
"""
システム状態マネージャー
Oton-ZzzシステムのACTIVE/SLEEP状態を管理
"""

from enum import Enum
import time


class SystemState(Enum):
    """システム状態"""
    ACTIVE = "active"   # テレビON、睡眠検出実行中
    SLEEP = "sleep"     # テレビOFF、睡眠検出停止、リモコン待機中


class SystemStateManager:
    """システム全体の状態を管理するクラス"""

    def __init__(self):
        """初期化"""
        self.state = SystemState.SLEEP  # 起動時はSLEEP状態
        self.last_state_change = time.time()

    def set_active(self):
        """
        ACTIVE状態に切り替え（テレビON）

        Returns:
            bool: 状態が変更された場合True
        """
        if self.state != SystemState.ACTIVE:
            self.state = SystemState.ACTIVE
            self.last_state_change = time.time()
            print("\n🟢 システム状態: ACTIVE（睡眠検出開始）")
            return True
        return False

    def set_sleep(self):
        """
        SLEEP状態に切り替え（テレビOFF）

        Returns:
            bool: 状態が変更された場合True
        """
        if self.state != SystemState.SLEEP:
            self.state = SystemState.SLEEP
            self.last_state_change = time.time()
            print("\n💤 システム状態: SLEEP（睡眠検出停止、リモコン待機中）")
            return True
        return False

    def is_active(self):
        """
        ACTIVE状態かどうか

        Returns:
            bool: ACTIVE状態ならTrue
        """
        return self.state == SystemState.ACTIVE

    def is_sleep(self):
        """
        SLEEP状態かどうか

        Returns:
            bool: SLEEP状態ならTrue
        """
        return self.state == SystemState.SLEEP

    def get_state(self):
        """
        現在の状態を取得

        Returns:
            dict: 状態情報
        """
        return {
            'state': self.state.value,
            'is_active': self.is_active(),
            'is_sleep': self.is_sleep(),
            'last_change': self.last_state_change
        }


if __name__ == '__main__':
    """テスト用"""
    print("システム状態マネージャーテスト\n")

    manager = SystemStateManager()
    print(f"初期状態: {manager.get_state()}\n")

    print("ACTIVE に切り替え:")
    manager.set_active()
    print(f"現在の状態: {manager.get_state()}\n")

    print("SLEEP に切り替え:")
    manager.set_sleep()
    print(f"現在の状態: {manager.get_state()}\n")

    print("ACTIVE に再度切り替え:")
    manager.set_active()
    print(f"現在の状態: {manager.get_state()}\n")

    print("テスト完了")
