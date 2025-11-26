#!/usr/bin/env python3
"""
Oton-Zzz Phase 1 - ヘッドレスモード（GUI不要版）
ターミナルでの動作確認用
"""

import time
import mediapipe as mp
import sys
import os
import cv2

# 必要なモジュールをインポート
from voice_controller import VoiceController
from tv_state_manager import TVStateManager
from ir_sleep_detector import IRController, SleepDetector
from ir_monitor import IRMonitor
from system_state_manager import SystemStateManager

try:
    from led_controller import LEDController
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


def main():
    """メイン処理 (ヘッドレス版)"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      Oton-Zzz v3.1 (Headless Mode)                       ║
║      ヘッドレス動作確認版                                  ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # LED初期化（エラーでも続行）
    led = None
    if LED_AVAILABLE:
        try:
            print("🔆 LEDコントローラーを初期化しています...")
            led = LEDController(green_pin=22, yellow_pin=23, red_pin=24)
        except Exception as e:
            print(f"⚠️  LED初期化をスキップしました: {e}")

    # 音声初期化
    print("🔊 音声コントローラーを初期化しています...")
    voice = VoiceController()

    # テレビ状態管理
    print("📺 テレビ状態管理を初期化しています...")
    tv_state = TVStateManager()

    # システム状態管理
    print("🔄 システム状態管理を初期化しています...")
    system_state = SystemStateManager()

    # テレビの初期状態に合わせて設定
    if tv_state.is_on:
        system_state.set_active()
    else:
        system_state.set_sleep()

    # IR Controller初期化
    try:
        ir_controller = IRController(tx_device='/dev/lirc0', rx_device='/dev/lirc1')
    except Exception as e:
        print(f"✗ IR Controllerの初期化に失敗: {e}")
        if led:
            led.cleanup()
        return

    # IR監視マネージャー初期化
    print("👀 IRリモコン監視を初期化しています...")
    ir_monitor = IRMonitor(rx_device='/dev/lirc1', tv_state_manager=tv_state)
    ir_monitor.start()

    # テレビのリモコン信号登録
    if "TV" not in ir_controller.recorded_codes:
        print("\n" + "="*60)
        print("初回起動: リモコン信号の登録が必要です")
        print("="*60)
        success = ir_controller.record_ir_signal("TV", num_samples=3, timeout=10)
        if not success:
            print("✗ リモコン登録に失敗しました")
            ir_monitor.stop()
            ir_controller.cleanup()
            if led:
                led.cleanup()
            return
    else:
        print(f"✓ 【TV】のリモコン信号は既に登録済みです")

    print("\n" + "="*60)
    print("Oton-Zzzシステムを開始します...")
    print("="*60 + "\n")

    # 睡眠検出器初期化
    detector = SleepDetector(
        gauge_max=5.0,                # ゲージが5.0に達したらStage1（5秒）
        gauge_decrease_rate=1.5,      # 減少速度を1.5倍に設定
        final_confirmation_time=5.0   # Stage1から5秒後にStage2へ（発表会用：合計10秒）
    )

    # 音声再生中フラグ（MediaPipe処理スキップ用）
    voice._is_speaking = False

    # MediaPipe initialized
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=detector.model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        num_faces=1,
        output_face_blendshapes=True,
        result_callback=detector.result_callback
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("✗ カメラを開けませんでした")
        ir_monitor.stop()
        ir_controller.cleanup()
        if led:
            led.cleanup()
        return

    # 通知フラグ
    notified_stage1 = False
    warning_spoken = False
    notified_stage2 = False

    try:
        with FaceLandmarker.create_from_options(options) as landmarker:
            voice.speak("おとんずずず、起動しました。")

            if led:
                if system_state.is_active():
                    led.set_normal()
                else:
                    led.all_off()

            print("✓ Oton-Zzzシステムが起動しました")
            print("  - Ctrl+Cで終了")
            print(f"  - 現在の状態: {'ACTIVE' if system_state.is_active() else 'SLEEP'}\n")

            start_time = time.time()
            last_status_print = time.time()

            while True:
                # リモコン信号チェック
                ir_signal = ir_monitor.has_signal()
                if ir_signal:
                    tv_is_on = ir_signal['new_state']

                    if tv_is_on:
                        system_state.set_active()
                        if led:
                            led.set_normal()
                        voice.speak("テレビがつきました。睡眠検出を開始します。")
                        notified_stage1 = False
                        warning_spoken = False
                        notified_stage2 = False
                        detector.sleep_gauge = 0.0
                        detector.final_confirmation_start_time = None
                    else:
                        system_state.set_sleep()
                        if led:
                            led.all_off()
                        voice.speak("テレビが消されました。待機モードに入ります。")
                        notified_stage1 = False
                        warning_spoken = False
                        notified_stage2 = False
                        detector.sleep_gauge = 0.0
                        detector.final_confirmation_start_time = None

                # ACTIVE状態の場合のみ睡眠検出
                if system_state.is_active():
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    # 音声再生中は画像処理をスキップ（バッファ蓄積防止）
                    if voice._is_speaking:
                        time.sleep(0.05)
                        continue

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    timestamp_ms = int((time.time() - start_time) * 1000)
                    landmarker.detect_async(mp_image, timestamp_ms)

                    gauge_value, is_stage1, is_stage2, status = detector.process_result()

                    # 5秒ごとにステータス表示
                    if time.time() - last_status_print > 5:
                        print(f"[Status] {status} | Gauge: {gauge_value:.1f}/{detector.GAUGE_MAX:.1f} | TV: {'ON' if tv_state.is_on else 'OFF'}")
                        last_status_print = time.time()

                    # Stage1: 警告開始
                    if is_stage1 and not notified_stage1:
                        print(f"\n[{time.ctime()}] ⚠️  STAGE 1 DETECTED! 5秒後にOFF")
                        if led:
                            led.set_warning()
                        # 5秒なので簡潔な警告
                        voice.speak("寝てるね。5秒後にテレビ消すよ。")
                        notified_stage1 = True
                        warning_spoken = True

                    # Stage2: 電源OFF
                    if is_stage2 and not notified_stage2:
                        if tv_state.is_on:
                            print(f"\n[{time.ctime()}] 😴 STAGE 2 CONFIRMED! 睡眠確定")
                            print(f"[{time.ctime()}] 📡 テレビの電源をOFF")

                            if led:
                                led.set_alert()
                            voice.speak_shutdown()

                            # IR監視を一時停止（自分の送信信号を受信しないように）
                            print(f"[DEBUG] IR監視を一時停止...")
                            ir_monitor.pause()
                            time.sleep(0.5)  # 少し待機

                            # IR信号送信
                            ir_controller.send_ir_signal("TV")
                            tv_state.turn_off()

                            # 送信信号が完全に消えるまで待機
                            time.sleep(2.0)

                            # IR監視を再開
                            print(f"[DEBUG] IR監視を再開")
                            ir_monitor.resume()

                            system_state.set_sleep()
                            if led:
                                led.all_off()

                            notified_stage2 = True

                    # 覚醒検出
                    if not is_stage1 and (notified_stage1 or notified_stage2):
                        print(f"\n[{time.ctime()}] 👀 ユーザーが起きました")

                        if notified_stage1 and not notified_stage2:
                            voice.speak_cancel()

                        if led:
                            led.set_normal()
                        notified_stage1 = False
                        warning_spoken = False
                        notified_stage2 = False

                else:
                    # SLEEP状態: 待機
                    if time.time() - last_status_print > 10:
                        print(f"[SLEEP] 待機中... TV: {'ON' if tv_state.is_on else 'OFF'}")
                        last_status_print = time.time()
                    time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n⚠️  終了します...")

    finally:
        cap.release()
        ir_monitor.stop()
        ir_controller.cleanup()
        if led:
            led.cleanup()
        print("\n✓ プログラムを正常に終了しました")


if __name__ == '__main__':
    main()
