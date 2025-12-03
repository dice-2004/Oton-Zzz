#!/usr/bin/env python3
"""
Oton-Zzz 完全自動キャリブレーション（最適化版）
カメラを最初に1回開いて使い回し、音声再生中もフレーム取得を継続
"""

import cv2
import time
import mediapipe as mp
import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager
from detector import SleepDetector
from voice import VoiceController


class AutoCalibration:
    """完全自動キャリブレーション"""

    def __init__(self):
        """初期化"""
        self.config_mgr = ConfigManager()
        self.voice = VoiceController()
        self.cap = None

        # カメラを開く
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("✗ カメラを開けませんでした")
            raise Exception("カメラが開けません")

        # カメラを実際に起動させるため、ダミーフレームを取得
        print("カメラを起動しています...")
        for i in range(10):
            ret, frame = self.cap.read()
            if ret:
                break
            time.sleep(0.1)

        if not ret:
            print("✗ カメラからフレームを取得できませんでした")
            raise Exception("カメラが正常に動作していません")

        print("✓ カメラを起動しました（LEDが緑に点灯）")

        # 音声は非同期で再生（処理を止めない）
        self.voice.speak("起動しました")

        # 音声再生完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)

        # デバイス安定化のため待機
        time.sleep(1.0)

    def run_test(self, duration_seconds=30, test_name="テスト"):
        """
        テスト実行（カメラは既に開いている前提）

        Returns:
            list: まばたきスコアのリスト
        """
        BaseOptions = mp.tasks.BaseOptions
        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        params = self.config_mgr.get_sleep_detection_params()
        detector = SleepDetector(
            blink_threshold=params.get('blink_threshold', 0.5),
            gauge_max=params.get('gauge_max', 5.0),
            gauge_increase_rate=params.get('gauge_increase_rate', 1.0),
            gauge_decrease_rate=params.get('gauge_decrease_rate', 1.5),
            final_confirmation_time=params.get('final_confirmation_time', 5.0)
        )

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=detector.model_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            num_faces=1,
            output_face_blendshapes=True,
            result_callback=detector.result_callback
        )

        # 統計データ
        blink_scores = []
        gauge_values = []

        try:
            with FaceLandmarker.create_from_options(options) as landmarker:
                start_time = time.time()
                test_start = time.time()
                last_voice_time = 0

                while True:
                    elapsed = time.time() - test_start
                    if elapsed >= duration_seconds:
                        break

                    ret, frame = self.cap.read()
                    if not ret:
                        break

                    frame = cv2.flip(frame, 1)

                    # 音声再生中はMediaPipe処理をスキップ（フレーム表示は継続）
                    if self.voice._is_speaking:
                        cv2.putText(frame, "Voice Speaking... (Detection Paused)", (10, 400),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        cv2.imshow("Auto Calibration", frame)
                        cv2.waitKey(1)
                        time.sleep(0.05)
                        continue

                    # MediaPipe処理
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

                    # 10秒ごとに進捗を音声通知（非同期）
                    if elapsed - last_voice_time >= 10.0:
                        remaining = duration_seconds - elapsed
                        self.voice.speak(f"あと{int(remaining)}秒")
                        last_voice_time = elapsed

                    # ========== OpenCVディスプレイ表示（情報表示のみ） ==========
                    color = (0, 255, 0)
                    if "Confirmed" in status:
                        color = (0, 0, 255)
                    elif "Confirmation" in status:
                        color = (0, 165, 255)
                    elif "Closed" in status:
                        color = (0, 255, 255)
                    elif "No Face" in status:
                        color = (128, 128, 128)

                    # テスト名と進捗を表示
                    cv2.putText(frame, f"Test: {test_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    cv2.putText(frame, f"Status: {status}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    cv2.putText(frame, f"Blink: L={left:.2f} R={right:.2f} Avg={avg:.2f}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, f"Threshold: {detector.BLINK_THRESHOLD:.2f}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    cv2.putText(frame, f"Gauge: {gauge_value:.1f} / {detector.GAUGE_MAX:.1f}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    cv2.putText(frame, f"Time: {elapsed:.1f}s / {duration_seconds}s", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

                    # ゲージバー
                    gauge_percentage = gauge_value / detector.GAUGE_MAX if detector.GAUGE_MAX > 0 else 0
                    bar_width = int(gauge_percentage * (frame.shape[1] - 20))
                    cv2.rectangle(frame, (10, 240), (frame.shape[1] - 10, 270), (255, 255, 255), 2)
                    cv2.rectangle(frame, (10, 240), (10 + bar_width, 270), color, -1)

                    # 進捗バー
                    progress = elapsed / duration_seconds
                    progress_width = int(progress * (frame.shape[1] - 20))
                    cv2.rectangle(frame, (10, 290), (frame.shape[1] - 10, 310), (100, 100, 100), 2)
                    cv2.rectangle(frame, (10, 290), (10 + progress_width, 310), (0, 255, 0), -1)

                    # 自動実行の注意書き
                    cv2.putText(frame, "AUTO CALIBRATION - No operation required", (10, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

                    cv2.imshow("Auto Calibration", frame)
                    # ========================================================

                    cv2.waitKey(1)
                    time.sleep(0.05)

        except KeyboardInterrupt:
            self.voice.speak("中断しました")
            return []

        return blink_scores

    def run_auto_calibration(self):
        """完全自動キャリブレーションフロー"""
        self.voice.speak("開始します")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)
        time.sleep(2)

        # ステップ1: 普通にテレビを見ている状態で測定（30秒）
        self.voice.speak("ステップ1")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)
        time.sleep(3)

        blink_scores_normal = self.run_test(duration_seconds=30, test_name="Step 1: Normal Viewing")

        if not blink_scores_normal:
            self.voice.speak("失敗しました")
            return

        avg_normal = sum(blink_scores_normal) / len(blink_scores_normal)
        print(f"\nステップ1完了: まばたきスコア平均 = {avg_normal:.3f}")
        self.voice.speak("完了")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)
        time.sleep(2)

        # ステップ2: 目を閉じた状態で測定（10秒）
        self.voice.speak("ステップ2")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)
        time.sleep(3)

        blink_scores_closed = self.run_test(duration_seconds=10, test_name="Step 2: Eyes Closed")

        if not blink_scores_closed:
            self.voice.speak("測定に失敗しました。ステップ1の結果のみで設定します")
            avg_closed = 1.0  # デフォルト値
        else:
            avg_closed = sum(blink_scores_closed) / len(blink_scores_closed)
            print(f"\nステップ2完了: まばたきスコア平均 = {avg_closed:.3f}")
            self.voice.speak("完了")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)
        time.sleep(2)

        # 最適な閾値を計算
        # 開いている時の平均と閉じている時の平均の中間値を推奨
        recommended_threshold = (avg_normal + avg_closed) / 2.0

        # 安全マージンを加える（中間値の80%）
        recommended_threshold *= 0.8

        # 推奨範囲内に収める
        recommended_threshold = max(0.3, min(0.7, recommended_threshold))

        print(f"\n推奨閾値: {recommended_threshold:.3f}")
        print(f"  開眼時平均: {avg_normal:.3f}")
        print(f"  閉眼時平均: {avg_closed:.3f}")

        # 設定を更新
        current_threshold = self.config_mgr.get_sleep_detection_params().get('blink_threshold', 0.5)

        print(f"\n現在の閾値: {current_threshold:.3f}")
        print(f"新しい閾値: {recommended_threshold:.3f}")

        self.voice.speak("設定更新")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)

        self.config_mgr.update_sleep_detection_params(blink_threshold=recommended_threshold)

        # 設定を保存
        self.voice.speak("保存します")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)

        self.config_mgr.save()

        # 完了
        self.voice.speak("完了しました")

        # 音声完了を待つ
        while self.voice._is_speaking:
            time.sleep(0.1)

        print("\n" + "="*60)
        print("✓ キャリブレーション完了")
        print("="*60)

    def cleanup(self):
        """クリーンアップ"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()


def main():
    """メイン処理"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║   Oton-Zzz 完全自動キャリブレーション v3.0               ║
║   カメラ1回起動・音声非同期処理                          ║
╚═══════════════════════════════════════════════════════════╝
    """)

    calibration = None
    try:
        calibration = AutoCalibration()
        calibration.run_auto_calibration()

    except KeyboardInterrupt:
        print("\n⚠️  中断しました")
    except Exception as e:
        print(f"✗ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if calibration:
            calibration.cleanup()


if __name__ == '__main__':
    main()
