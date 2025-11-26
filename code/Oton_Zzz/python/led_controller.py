#!/usr/bin/env python3
"""
LEDコントローラー
システムの状態をLEDで表示
"""

from gpiozero import LED
import time
import threading


class LEDController:
    """LED状態表示コントローラー"""

    def __init__(self, green_pin=22, yellow_pin=23, red_pin=24):
        """
        初期化

        Args:
            green_pin: 緑LED (正常動作)
            yellow_pin: 黄LED (警告中)
            red_pin: 赤LED (IR送信)
        """
        self.green_led = LED(green_pin)
        self.yellow_led = LED(yellow_pin)
        self.red_led = LED(red_pin)

        self.blink_thread = None
        self.stop_blink = False

        # 起動時は緑LEDを点灯
        self.set_normal()

    def all_off(self):
        """すべてのLEDを消灯"""
        self.stop_blink = True
        if self.blink_thread:
            self.blink_thread.join()

        self.green_led.off()
        self.yellow_led.off()
        self.red_led.off()

    def set_normal(self):
        """正常動作状態 (緑LED点灯)"""
        self.all_off()
        self.green_led.on()

    def set_warning(self):
        """警告状態 (黄LED点滅)"""
        self.all_off()
        self.stop_blink = False
        self.blink_thread = threading.Thread(target=self._blink_yellow, daemon=True)
        self.blink_thread.start()

    def set_alert(self):
        """アラート状態 (赤LED点灯)"""
        self.all_off()
        self.red_led.on()

    def set_pairing(self):
        """Bluetoothペアリング中 (青風に全LED点滅)"""
        self.all_off()
        self.stop_blink = False
        self.blink_thread = threading.Thread(target=self._blink_pairing, daemon=True)
        self.blink_thread.start()

    def _blink_yellow(self):
        """黄LED点滅"""
        while not self.stop_blink:
            self.yellow_led.on()
            time.sleep(0.5)
            self.yellow_led.off()
            time.sleep(0.5)

    def _blink_pairing(self):
        """ペアリング中の点滅パターン"""
        while not self.stop_blink:
            # 緑→黄→赤の順に点滅
            self.green_led.on()
            time.sleep(0.2)
            self.green_led.off()

            self.yellow_led.on()
            time.sleep(0.2)
            self.yellow_led.off()

            self.red_led.on()
            time.sleep(0.2)
            self.red_led.off()

            time.sleep(0.2)

    def cleanup(self):
        """リソースのクリーンアップ"""
        self.all_off()
        self.green_led.close()
        self.yellow_led.close()
        self.red_led.close()


if __name__ == '__main__':
    """テスト用"""
    print("LEDコントローラーテスト")
    led = LEDController()

    try:
        print("正常動作（緑LED）")
        led.set_normal()
        time.sleep(3)

        print("警告中（黄LED点滅）")
        led.set_warning()
        time.sleep(3)

        print("アラート（赤LED）")
        led.set_alert()
        time.sleep(3)

        print("ペアリング中（全LED点滅）")
        led.set_pairing()
        time.sleep(5)

    finally:
        led.cleanup()
        print("テスト完了")
