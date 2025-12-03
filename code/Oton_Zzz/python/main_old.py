
import cv2
import time
import mediapipe as mp

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../utils"))
# from serial_comm import Serialize_controler

class SleepDetector:
    """
    「睡眠ゲージ」方式を使った睡眠検出クラス
    """

    def __init__(
        self,
        blink_threshold=0.5,
        gauge_max=4.0,
        gauge_increase_rate=1.0,
        gauge_decrease_rate=1.5,
        final_confirmation_time=3.0,
        model_path='./face_landmarker_v2_with_blendshapes.task'
    ):
        """
        初期化

        Args:
            blink_threshold: 目が閉じていると判定するBlendshapeの閾値
            gauge_max: 睡眠ゲージの最大値。この値に達すると睡眠(Stage1)と判定
            gauge_increase_rate: ゲージの増加速度（ポイント/秒）
            gauge_decrease_rate: ゲージの減少速度（ポイント/秒）
            final_confirmation_time: Stage1検知後、Stage2まで待つ秒数
            model_path: Face Landmarkerモデルのパス
        """
        self.model_path = model_path

        # --- 判定パラメータ ---
        self.BLINK_THRESHOLD = blink_threshold
        self.GAUGE_MAX = gauge_max
        self.GAUGE_INCREASE_RATE = gauge_increase_rate
        self.GAUGE_DECREASE_RATE = gauge_decrease_rate
        self.FINAL_CONFIRMATION_TIME = final_confirmation_time

        # --- 状態管理変数 ---
        self.sleep_gauge = 0.0
        self.last_update_time = time.time()
        self.final_confirmation_start_time = None

        # --- MediaPipe結果保存用 ---
        self.latest_result = None

    def result_callback(self, result: mp.tasks.vision.FaceLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        self.latest_result = result

    def get_eye_blink_values(self):
        if (self.latest_result is None or not self.latest_result.face_blendshapes):
            return 0.0, 0.0, 0.0

        blendshapes = self.latest_result.face_blendshapes[0]
        left_blink = next((s.score for s in blendshapes if s.category_name == 'eyeBlinkLeft'), 0.0)
        right_blink = next((s.score for s in blendshapes if s.category_name == 'eyeBlinkRight'), 0.0)
        avg_blink = (left_blink + right_blink) / 2.0
        return left_blink, right_blink, avg_blink

    def process_result(self):
        """
        最新の検出結果を処理して睡眠状態を判定

        Returns:
            tuple: (gauge_value, is_stage1_sleep, is_stage2_sleep, status)
        """
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        status = "Awake"
        is_stage1_sleep = False
        is_stage2_sleep = False

        face_detected = self.latest_result is not None and self.latest_result.face_landmarks

        eyes_are_closed = False
        if face_detected:
            _, _, avg_blink = self.get_eye_blink_values()
            if avg_blink >= self.BLINK_THRESHOLD:
                eyes_are_closed = True

        if face_detected and eyes_are_closed:
            # --- 目が閉じている場合：ゲージを増加 ---
            self.sleep_gauge += self.GAUGE_INCREASE_RATE * delta_time
            status = "Eyes Closed"
        else:
            # --- 目が開いている、または顔が検出されない場合：ゲージを減少 ---
            self.sleep_gauge -= self.GAUGE_DECREASE_RATE * delta_time
            if face_detected:
                status = "Eyes Open"
            else:
                status = "No Face"

        # ゲージの値を 0 と GAUGE_MAX の間に制限
        self.sleep_gauge = max(0.0, min(self.sleep_gauge, self.GAUGE_MAX))

        # --- Stage1 / Stage2 の判定 ---
        is_stage1_sleep = (self.sleep_gauge >= self.GAUGE_MAX)

        if is_stage1_sleep:
            if self.final_confirmation_start_time is None:
                self.final_confirmation_start_time = current_time

            final_elapsed = current_time - self.final_confirmation_start_time
            if final_elapsed >= self.FINAL_CONFIRMATION_TIME:
                is_stage2_sleep = True
                status = "Confirmed Sleep (Stage 2)"
            else:
                status = f"Final Confirmation ({final_elapsed:.1f}s)"
        else:
            # ゲージが最大値から減ったら、最終確認タイマーをリセット
            self.final_confirmation_start_time = None

        return self.sleep_gauge, is_stage1_sleep, is_stage2_sleep, status


def main():
    """メイン処理"""
    # シリアル通信の初期化
    # ser = Serialize_controler(port="COM8")

    # 睡眠検出器の初期化
    detector = SleepDetector(
        gauge_max=4.0,                # ゲージが4.0に達したらStage1
        gauge_decrease_rate=1.5,      # 減少速度を1.5倍に設定
        final_confirmation_time=3.0   # Stage1から3秒後にStage2へ
    )

    # MediaPipe FaceLandmarkerの初期化
    # (変更なし)
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
        print("Error: Could not open camera")
        return

    # 通知フラグ
    notified_stage1 = False
    notified_stage2 = False

    with FaceLandmarker.create_from_options(options) as landmarker:
        print("Oton-Zzz Detector with Sleep Gauge is running...")

        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((time.time() - start_time) * 1000)
            landmarker.detect_async(mp_image, timestamp_ms)

            gauge_value, is_stage1, is_stage2, status = detector.process_result()

            # 顔未検出時は即OFFを送信（status が "No Face"）
            if status == "No Face":
                print(f"[{time.ctime()}] No face detected. Sending OFF to M5Stick...")
                # ser.send_to_m5("OFF")
                time.sleep(1.0)  # 少し待機してから次へ
            else:
                # --- M5Stickへの2段階通知処理 ---
                if is_stage1 and not notified_stage1:
                    print(f"[{time.ctime()}] STAGE 1 DETECTED! Sending pre-signal to M5Stick...")
                    notified_stage1 = True
                    # ser.send_to_m5("ALERT")

                if is_stage2 and not notified_stage2:
                    print(f"[{time.ctime()}] STAGE 2 CONFIRMED! Sending final signal to M5Stick...")
                    notified_stage2 = True
                    # ser.send_to_m5("OFF")

                if not is_stage1 and (notified_stage1 or notified_stage2):
                    print(f"[{time.ctime()}] User woke up. Resetting all notifications.")
                    notified_stage1 = False
                    notified_stage2 = False
                    # ser.send_to_m5("AWAKE")

            # --- デバッグ用ウィンドウ表示 ---
            color = (0, 255, 0)
            if "Confirmed" in status: color = (0, 0, 255)
            elif "Confirmation" in status: color = (0, 165, 255)
            elif "Closed" in status: color = (0, 255, 255)
            elif "No Face" in status: color = (128, 128, 128)

            cv2.putText(frame, f"Status: {status}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(frame, f"Sleep Gauge: {gauge_value:.1f} / {detector.GAUGE_MAX:.1f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # 睡眠ゲージのバー表示
            gauge_percentage = gauge_value / detector.GAUGE_MAX if detector.GAUGE_MAX > 0 else 0
            bar_width = int(gauge_percentage * (frame.shape[1] - 20))
            cv2.rectangle(frame, (10, 120), (frame.shape[1] - 10, 150), (255, 255, 255), 2)
            cv2.rectangle(frame, (10, 120), (10 + bar_width, 150), color, -1)

            # --- M5Stick通知状況（改行・色分け表示） ---
            stage1_status_text = "Sent" if notified_stage1 else "Ready"
            stage1_color = (0, 165, 255) if notified_stage1 else (0, 255, 0) # Sent: オレンジ, Ready: 緑
            cv2.putText(frame, f"Stage 1 Signal: {stage1_status_text}", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, stage1_color, 2)

            stage2_status_text = "Sent" if notified_stage2 else "Waiting"
            stage2_color = (0, 0, 255) if notified_stage2 else (128, 128, 128) # Sent: 赤, Waiting: 灰
            cv2.putText(frame, f"Stage 2 Signal: {stage2_status_text}", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, stage2_color, 2)


            cv2.imshow("Oton-Zzz Debug Monitor", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()
    print("\nProgram terminated.")


if __name__ == '__main__':
    main()
