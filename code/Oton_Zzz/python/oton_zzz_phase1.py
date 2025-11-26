#!/usr/bin/env python3
"""
Oton-Zzz Phase 1 完全版: テレビ状態同期対応
- テレビON/OFF と Oton-Zzz ACTIVE/SLEEP を完全同期
- リモコン信号を常時監視
- テレビOFF時は睡眠検出を停止
"""

import cv2
import time
import mediapipe as mp
import sys
import os

# 新しいモジュールをインポート
from led_controller import LEDController
from voice_controller import VoiceController
from tv_state_manager import TVStateManager
from ir_sleep_detector import IRController, SleepDetector
from ir_monitor import IRMonitor
from system_state_manager import SystemStateManager, SystemState


def main():
    """メイン処理 (テレビ状態同期版)"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      Oton-Zzz v3.1 (Phase 1 - TV Sync Edition)           ║
║      テレビ状態完全同期 + LED + 音声警告                  ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # LED初期化（エラーでも続行）
    try:
        print("🔆 LEDコントローラーを初期化しています...")
        led = LEDController(green_pin=22, yellow_pin=23, red_pin=24)
        led_enabled = True
    except Exception as e:
        print(f"⚠️  LED初期化をスキップしました: {e}")
        led = None
        led_enabled = False

    # 音声初期化
    print("🔊 音声コントローラーを初期化しています...")
    voice = VoiceController()

    # テレビ状態管理
    print("📺 テレビ状態管理を初期化しています...")
    tv_state = TVStateManager()

    # システム状態管理
    print("🔄 システム状態管理を初期化しています...")
    system_state = SystemStateManager()

    # テレビの初期状態に合わせてシステム状態を設定
    if tv_state.is_on:
        system_state.set_active()
    else:
        system_state.set_sleep()

    # IR Controllerの初期化
    try:
        ir_controller = IRController(tx_device='/dev/lirc0', rx_device='/dev/lirc1')
    except Exception as e:
        print(f"✗ IR Controllerの初期化に失敗しました: {e}")
        if led_enabled:
            led.cleanup()
        return

    # IR監視マネージャーの初期化
    print("👀 IRリモコン監視を初期化しています...")
    ir_monitor = IRMonitor(rx_device='/dev/lirc1', tv_state_manager=tv_state)
    ir_monitor.start()

    # テレビのリモコン信号を登録（既に登録済みでなければ）
    if "TV" not in ir_controller.recorded_codes:
        print("\n" + "="*60)
        print("初回起動: リモコン信号の登録が必要です")
        print("="*60)
        success = ir_controller.record_ir_signal("TV", num_samples=3, timeout=10)
        if not success:
            print("✗ リモコン登録に失敗しました。プログラムを終了します。")
            ir_monitor.stop()
            ir_controller.cleanup()
            if led_enabled:
                led.cleanup()
            return
    else:
        print(f"✓ 【TV】のリモコン信号は既に登録済みです")

    print("\n" + "="*60)
    print("Oton-Zzzシステムを開始します...")
    print("="*60 + "\n")

    # 睡眠検出器の初期化
    detector = SleepDetector(
        gauge_max=5.0,                # ゲージが5.0に達したらStage1（5秒）
        gauge_decrease_rate=1.5,      # 減少速度を1.5倍に設定
        final_confirmation_time=5.0   # Stage1から5秒後にStage2へ（発表会用：合計10秒）
    )

    # 音声再生中フラグ（MediaPipe処理スキップ用）
    voice._is_speaking = False

    # MediaPipe FaceLandmarkerの初期化
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
        if led_enabled:
            led.cleanup()
        return

    # 通知フラグ
    notified_stage1 = False
    warning_spoken = False
    notified_stage2 = False

    try:
        with FaceLandmarker.create_from_options(options) as landmarker:
            voice.speak("おとんずずず、起動しました。")

            # 初期状態に応じたLED
            if led_enabled:
                if system_state.is_active():
                    led.set_normal()  # 緑LED
                else:
                    led.all_off()  # SLEEP時はLED消灯

            print("✓ Oton-Zzzシステムが起動しました")
            print("  - Qキーで終了")
            print(f"  - 現在の状態: {'ACTIVE (睡眠検出中)' if system_state.is_active() else 'SLEEP (待機中)'}\n")

            start_time = time.time()

            while True:
                # リモコン信号チェック
                ir_signal = ir_monitor.has_signal()
                if ir_signal:
                    # テレビ状態が変更された
                    tv_is_on = ir_signal['new_state']

                    if tv_is_on:
                        # テレビON → システムACTIVE
                        system_state.set_active()
                        if led_enabled:
                            led.set_normal()
                        voice.speak("テレビがつきました。睡眠検出を開始します。")

                        # 通知フラグをリセット
                        notified_stage1 = False
                        warning_spoken = False
                        notified_stage2 = False
                        detector.sleep_gauge = 0.0
                        detector.final_confirmation_start_time = None

                    else:
                        # テレビOFF → システムSLEEP
                        system_state.set_sleep()
                        if led_enabled:
                            led.all_off()
                        voice.speak("テレビが消されました。待機モードに入ります。")

                        # 通知フラグをリセット
                        notified_stage1 = False
                        warning_spoken = False
                        notified_stage2 = False
                        detector.sleep_gauge = 0.0
                        detector.final_confirmation_start_time = None

                # ACTIVE状態の場合のみ睡眠検出を実行
                if system_state.is_active():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # 音声再生中は画像処理をスキップ（バッファ蓄積防止）
                    if voice._is_speaking:
                        # 画像は表示し続けるが、検出処理はスキップ
                        frame = cv2.flip(frame, 1)
                        cv2.putText(frame, "Speaking...", (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                        cv2.imshow("Oton-Zzz Phase 1 (TV Sync)", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                        continue

                    frame = cv2.flip(frame, 1)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    timestamp_ms = int((time.time() - start_time) * 1000)
                    landmarker.detect_async(mp_image, timestamp_ms)

                    gauge_value, is_stage1, is_stage2, status = detector.process_result()

                    # --- Stage1: 警告開始 ---
                    if is_stage1 and not notified_stage1:
                        print(f"[{time.ctime()}] ⚠️  STAGE 1 DETECTED! 5秒後にOFF")
                        if led_enabled:
                            led.set_warning()  # 黄LED点滅
                        # 5秒なので簡潔な警告
                        voice.speak("寝てるね。5秒後にテレビ消すよ。")
                        notified_stage1 = True
                        warning_spoken = True

                    # --- Stage2: 電源OFF実行 ---
                    if is_stage2 and not notified_stage2:
                        if tv_state.is_on:
                            print(f"[{time.ctime()}] 😴 STAGE 2 CONFIRMED! 睡眠確定")
                            print(f"[{time.ctime()}] 📡 テレビの電源をOFFにします...")

                            if led_enabled:
                                led.set_alert()  # 赤LED
                            voice.speak_shutdown()

                            # IR監視を一時停止（自分の送信信号を受信しないように）
                            ir_monitor.pause()
                            time.sleep(0.5)

                            # テレビのIR信号を送信
                            ir_controller.send_ir_signal("TV")
                            tv_state.turn_off()  # テレビ状態をOFFに

                            # 送信信号が消えるまで待機
                            time.sleep(2.0)

                            # IR監視を再開
                            ir_monitor.resume()

                            # システムをSLEEP状態に
                            system_state.set_sleep()
                            if led_enabled:
                                led.all_off()

                            notified_stage2 = True
                        else:
                            print(f"[{time.ctime()}] 📺 テレビは既にOFFです。")
                            notified_stage2 = True

                    # --- 覚醒検出 ---
                    if not is_stage1 and (notified_stage1 or notified_stage2):
                        print(f"[{time.ctime()}] 👀 ユーザーが起きました。通知をリセットします。")

                        if notified_stage1 and not notified_stage2:
                            voice.speak_cancel()

                        if led_enabled:
                            led.set_normal()  # 緑LEDに戻す
                        notified_stage1 = False
                        warning_spoken = False
                        notified_stage2 = False

                    # --- デバッグ用ウィンドウ表示 ---
                    color = (0, 255, 0)
                    if "Confirmed" in status:
                        color = (0, 0, 255)
                    elif "Confirmation" in status:
                        color = (0, 165, 255)
                    elif "Closed" in status:
                        color = (0, 255, 255)
                    elif "No Face" in status:
                        color = (128, 128, 128)

                    cv2.putText(frame, f"Status: {status}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    cv2.putText(frame, f"Sleep Gauge: {gauge_value:.1f} / {detector.GAUGE_MAX:.1f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                    # システム状態表示
                    sys_status = "ACTIVE" if system_state.is_active() else "SLEEP"
                    sys_color = (0, 255, 0) if system_state.is_active() else (128, 128, 128)
                    cv2.putText(frame, f"System: {sys_status}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, sys_color, 2)

                    # テレビ状態表示
                    tv_status_text = "TV: ON" if tv_state.is_on else "TV: OFF"
                    tv_color = (0, 255, 0) if tv_state.is_on else (128, 128, 128)
                    cv2.putText(frame, tv_status_text, (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, tv_color, 2)

                    # 睡眠ゲージのバー表示
                    gauge_percentage = gauge_value / detector.GAUGE_MAX if detector.GAUGE_MAX > 0 else 0
                    bar_width = int(gauge_percentage * (frame.shape[1] - 20))
                    cv2.rectangle(frame, (10, 200), (frame.shape[1] - 10, 230), (255, 255, 255), 2)
                    cv2.rectangle(frame, (10, 200), (10 + bar_width, 230), color, -1)

                    cv2.imshow("Oton-Zzz Phase 1 (TV Sync)", frame)

                else:
                    # SLEEP状態：待機画面を表示
                    import numpy as np
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)

                    # 黒い画面に待機メッセージ
                    cv2.putText(frame, "SLEEP MODE", (180, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (100, 100, 100), 3)
                    cv2.putText(frame, "Waiting for TV remote...", (150, 280), cv2.FONT_HERSHEY_SIMPLEX, 1, (150, 150, 150), 2)
                    cv2.putText(frame, f"TV: {'ON' if tv_state.is_on else 'OFF'}", (250, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

                    cv2.imshow("Oton-Zzz Phase 1 (TV Sync)", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n\n⚠️  キーボード割り込みを検出しました")

    finally:
        # クリーンアップ
        cap.release()
        cv2.destroyAllWindows()
        ir_monitor.stop()
        ir_controller.cleanup()
        if led_enabled:
            led.cleanup()
        print("\n✓ プログラムを正常に終了しました")


if __name__ == '__main__':
    main()
