#!/usr/bin/env python3
"""
Oton-Zzz キャリブレーションツール (ヘッドレス対応)
睡眠検出パラメータを対話的に調整
ディスプレイなしでも使用可能
"""

import cv2
import time
import mediapipe as mp
import argparse
import json
from config_manager import ConfigManager
from ir_sleep_detector import SleepDetector
from voice_controller import VoiceController


def run_test_detection_headless(detector, voice, duration_seconds=30):
    """
    ヘッドレスモードでテスト検出を実行（画面出力なし）

    Args:
        detector: SleepDetectorインスタンス
        voice: VoiceControllerインスタンス
        duration_seconds: テスト実行時間（秒）
    """
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
        voice.speak("カメラを開けませんでした")
        return

    print(f"\n📹 {duration_seconds}秒間テスト検出を実行します...")
    voice.speak(f"{duration_seconds}秒間、テストを開始します。カメラを見てください。")
    print("=" * 60)

    # 統計データ
    blink_scores = []
    gauge_values = []
    stage1_count = 0
    stage2_count = 0

    try:
        with FaceLandmarker.create_from_options(options) as landmarker:
            start_time = time.time()
            test_start = time.time()
            last_voice_time = 0

            while True:
                elapsed = time.time() - test_start
                if elapsed >= duration_seconds:
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = int((time.time() - start_time) * 1000)
                landmarker.detect_async(mp_image, timestamp_ms)

                gauge_value, is_stage1, is_stage2, status = detector.process_result()

                # まばたきスコアを取得
                left, right, avg = detector.get_eye_blink_values()

                # 統計データ収集
                if avg > 0:
                    blink_scores.append(avg)
                gauge_values.append(gauge_value)

                if is_stage1:
                    stage1_count += 1
                if is_stage2:
                    stage2_count += 1

                # 5秒ごとに進捗を音声通知
                if elapsed - last_voice_time >= 5.0:
                    voice.speak(f"経過{int(elapsed)}秒。まばたきスコア平均{avg:.2f}")
                    last_voice_time = elapsed

                # コンソールに詳細情報を出力
                print(f"\r経過: {elapsed:.1f}s | Blink: {avg:.2f} | Gauge: {gauge_value:.1f}/{detector.GAUGE_MAX:.1f} | {status}", end='')

                time.sleep(0.05)  # CPU負荷軽減

    except KeyboardInterrupt:
        print("\n⚠️  テストを中断しました")
        voice.speak("テストを中断しました")

    finally:
        cap.release()
        print("\n" + "=" * 60)
        print("✓ テスト完了\n")

        # 統計情報を表示
        if blink_scores:
            print("【統計情報】")
            print(f"  まばたきスコア:")
            print(f"    - 平均: {sum(blink_scores)/len(blink_scores):.3f}")
            print(f"    - 最大: {max(blink_scores):.3f}")
            print(f"    - 最小: {min(blink_scores):.3f}")
            print(f"  睡眠ゲージ:")
            print(f"    - 平均: {sum(gauge_values)/len(gauge_values):.2f}")
            print(f"    - 最大: {max(gauge_values):.2f}")
            print(f"  Stage1検知回数: {stage1_count}")
            print(f"  Stage2検知回数: {stage2_count}")
            print("=" * 60)

            voice.speak(f"テスト完了。まばたきスコア平均は{sum(blink_scores)/len(blink_scores):.2f}でした。")


def run_test_detection_with_display(detector, duration_seconds=30):
    """
    ディスプレイありでテスト検出を実行（従来の方法）

    Args:
        detector: SleepDetectorインスタンス
        duration_seconds: テスト実行時間（秒）
    """
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
        return

    print(f"\n📹 {duration_seconds}秒間テスト検出を実行します...")
    print("=" * 60)

    try:
        with FaceLandmarker.create_from_options(options) as landmarker:
            start_time = time.time()
            test_start = time.time()

            while True:
                elapsed = time.time() - test_start
                if elapsed >= duration_seconds:
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = int((time.time() - start_time) * 1000)
                landmarker.detect_async(mp_image, timestamp_ms)

                gauge_value, is_stage1, is_stage2, status = detector.process_result()

                # まばたきスコアを取得
                left, right, avg = detector.get_eye_blink_values()

                # 画面表示
                color = (0, 255, 0)
                if "Confirmed" in status:
                    color = (0, 0, 255)
                elif "Confirmation" in status:
                    color = (0, 165, 255)
                elif "Closed" in status:
                    color = (0, 255, 255)

                cv2.putText(frame, f"Status: {status}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.putText(frame, f"Blink Score: L={left:.2f} R={right:.2f} Avg={avg:.2f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Threshold: {detector.BLINK_THRESHOLD:.2f}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.putText(frame, f"Gauge: {gauge_value:.1f} / {detector.GAUGE_MAX:.1f}", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.putText(frame, f"Time: {elapsed:.1f}s / {duration_seconds}s", (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

                # ゲージバー
                gauge_percentage = gauge_value / detector.GAUGE_MAX if detector.GAUGE_MAX > 0 else 0
                bar_width = int(gauge_percentage * (frame.shape[1] - 20))
                cv2.rectangle(frame, (10, 230), (frame.shape[1] - 10, 260), (255, 255, 255), 2)
                cv2.rectangle(frame, (10, 230), (10 + bar_width, 260), color, -1)

                cv2.imshow("Calibration Test", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n⚠️  テストを中断しました")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("=" * 60)
        print("✓ テスト完了")


def main():
    """キャリブレーションメイン処理"""
    parser = argparse.ArgumentParser(description='Oton-Zzz キャリブレーションツール')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモード（ディスプレイなし）')
    args = parser.parse_args()

    print("""
╔═══════════════════════════════════════════════════════════╗
║      Oton-Zzz キャリブレーションツール v2.0              ║
║      睡眠検出パラメータの調整                            ║
╚═══════════════════════════════════════════════════════════╝
    """)

    if args.headless:
        print("🖥️  ヘッドレスモードで起動します")
        # 音声コントローラーを初期化
        try:
            voice = VoiceController()
            voice.speak("おとんZZZ、キャリブレーションツールを起動しました")
        except Exception as e:
            print(f"⚠️  音声コントローラーの初期化に失敗: {e}")
            voice = None
    else:
        print("🖥️  通常モード（ディスプレイあり）で起動します")
        voice = None

    # 設定マネージャーを初期化
    config_mgr = ConfigManager()
    config_mgr.print_params()

    while True:
        print("\n【メニュー】")
        print("1. 現在の設定でテスト実行 (30秒)")
        print("2. まばたき閾値 (BLINK_THRESHOLD) を変更")
        print("3. 睡眠ゲージ最大値 (GAUGE_MAX) を変更")
        print("4. ゲージ増加速度 (GAUGE_INCREASE_RATE) を変更")
        print("5. ゲージ減少速度 (GAUGE_DECREASE_RATE) を変更")
        print("6. 最終確認時間 (FINAL_CONFIRMATION_TIME) を変更")
        print("7. 設定を表示")
        print("8. 設定を保存して終了")
        print("9. 保存せずに終了")

        choice = input("\n選択してください (1-9): ").strip()

        if choice == '1':
            # テスト実行
            params = config_mgr.get_sleep_detection_params()
            detector = SleepDetector(
                blink_threshold=params.get('blink_threshold', 0.5),
                gauge_max=params.get('gauge_max', 5.0),
                gauge_increase_rate=params.get('gauge_increase_rate', 1.0),
                gauge_decrease_rate=params.get('gauge_decrease_rate', 1.5),
                final_confirmation_time=params.get('final_confirmation_time', 5.0)
            )

            if args.headless:
                run_test_detection_headless(detector, voice, duration_seconds=30)
            else:
                run_test_detection_with_display(detector, duration_seconds=30)

        elif choice == '2':
            print("\n【まばたき閾値の調整】")
            print("目を閉じたと判定する閾値です。")
            print("値が小さいほど「閉じた」と判定されやすくなります。")
            print("推奨範囲: 0.4 〜 0.6")
            try:
                value = float(input("新しい値を入力 (現在: {}): ".format(config_mgr.get_sleep_detection_params().get('blink_threshold', 0.5))))
                config_mgr.update_sleep_detection_params(blink_threshold=value)
                if voice:
                    voice.speak(f"まばたき閾値を{value}に変更しました")
            except ValueError:
                print("✗ 無効な値です")

        elif choice == '3':
            print("\n【睡眠ゲージ最大値の調整】")
            print("目を閉じ続けてこの値に達すると睡眠Stage1と判定されます。")
            print("推奨範囲: 3.0 〜 7.0 (秒数相当)")
            try:
                value = float(input("新しい値を入力 (現在: {}): ".format(config_mgr.get_sleep_detection_params().get('gauge_max', 5.0))))
                config_mgr.update_sleep_detection_params(gauge_max=value)
                if voice:
                    voice.speak(f"ゲージ最大値を{value}に変更しました")
            except ValueError:
                print("✗ 無効な値です")

        elif choice == '4':
            print("\n【ゲージ増加速度の調整】")
            print("目を閉じているときのゲージ増加速度です。")
            print("推奨範囲: 0.8 〜 1.5 (ポイント/秒)")
            try:
                value = float(input("新しい値を入力 (現在: {}): ".format(config_mgr.get_sleep_detection_params().get('gauge_increase_rate', 1.0))))
                config_mgr.update_sleep_detection_params(gauge_increase_rate=value)
                if voice:
                    voice.speak(f"ゲージ増加速度を{value}に変更しました")
            except ValueError:
                print("✗ 無効な値です")

        elif choice == '5':
            print("\n【ゲージ減少速度の調整】")
            print("目を開いているときのゲージ減少速度です。")
            print("推奨範囲: 1.0 〜 2.0 (ポイント/秒)")
            try:
                value = float(input("新しい値を入力 (現在: {}): ".format(config_mgr.get_sleep_detection_params().get('gauge_decrease_rate', 1.5))))
                config_mgr.update_sleep_detection_params(gauge_decrease_rate=value)
                if voice:
                    voice.speak(f"ゲージ減少速度を{value}に変更しました")
            except ValueError:
                print("✗ 無効な値です")

        elif choice == '6':
            print("\n【最終確認時間の調整】")
            print("Stage1検知後、Stage2（実際にテレビを消す）までの待機時間です。")
            print("推奨範囲: 3.0 〜 10.0 (秒)")
            try:
                value = float(input("新しい値を入力 (現在: {}): ".format(config_mgr.get_sleep_detection_params().get('final_confirmation_time', 5.0))))
                config_mgr.update_sleep_detection_params(final_confirmation_time=value)
                if voice:
                    voice.speak(f"最終確認時間を{value}秒に変更しました")
            except ValueError:
                print("✗ 無効な値です")

        elif choice == '7':
            config_mgr.print_params()

        elif choice == '8':
            print("\n設定を保存しています...")
            if config_mgr.save():
                print("✓ 設定を保存しました。終了します。")
                if voice:
                    voice.speak("設定を保存しました。終了します")
                break
            else:
                print("✗ 保存に失敗しました")

        elif choice == '9':
            print("\n保存せずに終了します。")
            if voice:
                voice.speak("保存せずに終了します")
            break

        else:
            print("✗ 無効な選択です")


if __name__ == '__main__':
    main()
