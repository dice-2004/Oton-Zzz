#!/usr/bin/env python3
"""
LED制御モジュール（2色LED対応版 - lgpio使用）
緑LED: 電源ON
赤LED: 電源OFF
両方点滅: 警告
"""

import time
import threading

# GPIO制御を試みる（Raspberry Pi 5対応）
try:
    import lgpio
    GPIO_AVAILABLE = True
    GPIO_LIB = 'lgpio'
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
        GPIO_LIB = 'RPi.GPIO'
    except ImportError:
        GPIO_AVAILABLE = False
        print("⚠️  GPIOライブラリが利用できません。LEDはシミュレーションモードで動作します")


class LEDController:
    """2色LED制御クラス"""

    # GPIO設定（17,18は赤外線で使用中のため避ける）
    LED_GREEN = 22  # 緑LED（電源ON）
    LED_RED = 23    # 赤LED（電源OFF）

    def __init__(self):
        """初期化"""
        self.green_state = False
        self.red_state = False
        self.blinking = False
        self.blink_thread = None
        self.chip = None

        if GPIO_AVAILABLE:
            if GPIO_LIB == 'lgpio':
                # lgpioを使用（Raspberry Pi 5）
                self.chip = lgpio.gpiochip_open(4)  # gpiochip4 for Raspberry Pi 5
                lgpio.gpio_claim_output(self.chip, self.LED_GREEN)
                lgpio.gpio_claim_output(self.chip, self.LED_RED)

                # 初期状態: 両方OFF
                lgpio.gpio_write(self.chip, self.LED_GREEN, 0)
                lgpio.gpio_write(self.chip, self.LED_RED, 0)

                print(f"✓ LED制御を初期化しました（2色: 緑=GPIO22, 赤=GPIO23, {GPIO_LIB}）")
            else:
                # RPi.GPIOを使用（Raspberry Pi 4以前）
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self.LED_GREEN, GPIO.OUT)
                GPIO.setup(self.LED_RED, GPIO.OUT)

                # 初期状態: 両方OFF
                GPIO.output(self.LED_GREEN, GPIO.LOW)
                GPIO.output(self.LED_RED, GPIO.LOW)

                print(f"✓ LED制御を初期化しました（2色: 緑=GPIO22, 赤=GPIO23, {GPIO_LIB}）")
        else:
            print("⚠️  LEDはシミュレーションモードで動作します")

    def _gpio_write(self, pin, value):
        """GPIO出力（ライブラリによる分岐）"""
        if not GPIO_AVAILABLE:
            return

        if GPIO_LIB == 'lgpio':
            lgpio.gpio_write(self.chip, pin, value)
        else:
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)

    def power_on(self):
        """電源ON状態: 緑LED点灯"""
        self.stop_blinking()

        self.green_state = True
        self.red_state = False

        self._gpio_write(self.LED_GREEN, 1)
        self._gpio_write(self.LED_RED, 0)

        print("💡 LED: 緑点灯（電源ON）")

    def power_off(self):
        """電源OFF状態: 赤LED点灯"""
        self.stop_blinking()

        self.green_state = False
        self.red_state = True

        self._gpio_write(self.LED_GREEN, 0)
        self._gpio_write(self.LED_RED, 1)

        print("💡 LED: 赤点灯（電源OFF）")

    def warning(self):
        """警告状態: 緑・赤両方点滅"""
        self.start_blinking()
        print("💡 LED: 緑・赤点滅（警告）")

    def off(self):
        """全消灯"""
        self.stop_blinking()

        self.green_state = False
        self.red_state = False

        self._gpio_write(self.LED_GREEN, 0)
        self._gpio_write(self.LED_RED, 0)

        print("💡 LED: 全消灯")

    def start_blinking(self):
        """点滅開始"""
        if self.blinking:
            return

        self.blinking = True
        self.blink_thread = threading.Thread(target=self._blink_loop, daemon=True)
        self.blink_thread.start()

    def stop_blinking(self):
        """点滅停止"""
        self.blinking = False
        if self.blink_thread:
            self.blink_thread.join(timeout=1.0)
            self.blink_thread = None

    def _blink_loop(self):
        """点滅ループ（別スレッド）"""
        while self.blinking:
            # 緑・赤を同時に点灯
            self._gpio_write(self.LED_GREEN, 1)
            self._gpio_write(self.LED_RED, 1)
            time.sleep(0.3)

            # 緑・赤を同時に消灯
            self._gpio_write(self.LED_GREEN, 0)
            self._gpio_write(self.LED_RED, 0)
            time.sleep(0.3)

    def cleanup(self):
        """クリーンアップ"""
        self.stop_blinking()

        if GPIO_AVAILABLE:
            if GPIO_LIB == 'lgpio':
                lgpio.gpio_write(self.chip, self.LED_GREEN, 0)
                lgpio.gpio_write(self.chip, self.LED_RED, 0)
                lgpio.gpiochip_close(self.chip)
            else:
                GPIO.output(self.LED_GREEN, GPIO.LOW)
                GPIO.output(self.LED_RED, GPIO.LOW)
                GPIO.cleanup([self.LED_GREEN, self.LED_RED])

            print("✓ LEDをクリーンアップしました")


# テスト用
if __name__ == '__main__':
    led = LEDController()

    print("\nLEDテストを開始します...")

    print("\n1. 電源ON（緑点灯）")
    led.power_on()
    time.sleep(2)

    print("\n2. 電源OFF（赤点灯）")
    led.power_off()
    time.sleep(2)

    print("\n3. 警告（緑・赤点滅）")
    led.warning()
    time.sleep(3)

    print("\n4. 全消灯")
    led.off()
    time.sleep(1)

    led.cleanup()
    print("\nテスト完了")
