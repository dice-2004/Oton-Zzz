#!/usr/bin/env python3
"""
IRリモコン信号監視マネージャー
常時バックグラウンドでリモコン信号を監視し、テレビ状態を同期
"""

import subprocess
import threading
import time
from queue import Queue


class IRMonitor:
    """IRリモコン信号を常時監視するクラス"""

    def __init__(self, rx_device='/dev/lirc1', tv_state_manager=None):
        """
        初期化

        Args:
            rx_device: 受信用LIRCデバイス
            tv_state_manager: TVStateManagerのインスタンス
        """
        self.rx_device = rx_device
        self.tv_state_manager = tv_state_manager
        self.is_running = False
        self.is_paused = False  # NEW: 一時停止フラグ
        self.monitor_thread = None
        self.signal_queue = Queue()

    def start(self):
        """監視を開始"""
        if self.is_running:
            print("⚠️  IR監視は既に実行中です")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("✓ IR監視を開始しました")

    def stop(self):
        """監視を停止"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("✓ IR監視を停止しました")

    def pause(self):
        """監視を一時停止（IR送信時に使用）"""
        self.is_paused = True

    def resume(self):
        """監視を再開"""
        self.is_paused = False

    def _monitor_loop(self):
        """バックグラウンドでIR信号を監視するループ"""
        print(f"🔍 IR監視スレッド開始 (デバイス: {self.rx_device})")

        while self.is_running:
            # 一時停止中はスキップ
            if self.is_paused:
                time.sleep(0.1)
                continue

            try:
                # IR信号を受信（タイムアウト付き）
                result = subprocess.run(
                    ['ir-ctl', '-d', self.rx_device, '-r', '-1'],
                    capture_output=True,
                    text=True,
                    timeout=1.0  # 1秒タイムアウト
                )

                if result.returncode == 0 and result.stdout.strip():
                    # IR信号を受信した（一時停止中でない場合のみ処理）
                    if not self.is_paused:
                        raw_signal = result.stdout.strip()
                        self._handle_ir_signal(raw_signal)

            except subprocess.TimeoutExpired:
                # タイムアウトは正常（信号がない）
                continue
            except Exception as e:
                # エラーが発生しても監視を継続
                time.sleep(0.5)

    def _handle_ir_signal(self, raw_signal):
        """
        受信したIR信号を処理

        Args:
            raw_signal: 生のIR信号データ
        """
        print(f"\n📡 リモコン信号を受信しました")

        # テレビ状態をトグル
        if self.tv_state_manager:
            new_state = self.tv_state_manager.toggle()
            status = "ON" if new_state else "OFF"
            print(f"📺 テレビ状態を切り替えました: {status}")

            # シグナルキューに状態変更を通知
            self.signal_queue.put({
                'type': 'tv_toggle',
                'new_state': new_state,
                'timestamp': time.time()
            })

        # 少し待機（連続押しを防ぐ）
        time.sleep(0.5)

    def has_signal(self):
        """
        新しいIR信号があるかチェック

        Returns:
            dict or None: 信号情報、なければNone
        """
        if not self.signal_queue.empty():
            return self.signal_queue.get()
        return None


if __name__ == '__main__':
    """テスト用"""
    from tv_state_manager import TVStateManager

    print("IR監視マネージャーテスト")
    print("リモコンボタンを押してください（Ctrl+Cで終了）\n")

    tv_state = TVStateManager()
    monitor = IRMonitor(rx_device='/dev/lirc1', tv_state_manager=tv_state)

    try:
        monitor.start()

        while True:
            # シグナルをチェック
            signal = monitor.has_signal()
            if signal:
                print(f"✓ 状態変更検出: {signal}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n終了します...")
    finally:
        monitor.stop()
