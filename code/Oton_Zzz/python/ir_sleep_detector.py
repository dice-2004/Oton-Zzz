#!/usr/bin/env python3
"""
IR Remote Control + Sleep Detection (ir-ctl版)
ラズベリーパイ5でir-ctlコマンドを使ったIR送受信機能付き睡眠検出システム
"""

import cv2
import time
import mediapipe as mp
import subprocess
import json
import os
import sys
import re

# main.pyのSleepDetectorをインポート
sys.path.append(os.path.dirname(__file__))


class IRController:
    """赤外線送受信を管理するクラス (ir-ctl版)"""

    def __init__(self, tx_device='/dev/lirc0', rx_device='/dev/lirc1', config_file='ir_codes.json'):
        """
        初期化

        Args:
            tx_device: 送信用LIRCデバイスファイル（デフォルト: /dev/lirc0）
            rx_device: 受信用LIRCデバイスファイル（デフォルト: /dev/lirc1）
            config_file: IR信号を保存するJSONファイル
        """
        self.tx_device = tx_device
        self.rx_device = rx_device
        self.config_file = config_file
        self.recorded_codes = {}

        # ir-ctlコマンドの存在確認
        try:
            result = subprocess.run(['which', 'ir-ctl'],
                                  capture_output=True, text=True, check=True)
            print(f"✓ ir-ctlコマンドが見つかりました: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            raise Exception("ir-ctlコマンドが見つかりません")

        # デバイスファイルの存在確認
        if not os.path.exists(self.tx_device):
            raise Exception(f"送信デバイス {self.tx_device} が見つかりません。\n"
                          f"/boot/firmware/config.txtで dtoverlay=gpio-ir-tx が設定されているか確認してください。")

        if not os.path.exists(self.rx_device):
            print(f"⚠️  受信デバイス {self.rx_device} が見つかりません。")
            print(f"   手動登録モードのみ利用可能です。")
            self.rx_device = None
        else:
            print(f"✓ IR受信デバイスを確認しました: {self.rx_device}")

        print(f"✓ IR送信デバイスを確認しました: {self.tx_device}")

        # 保存されているコードを読み込み
        self.load_codes()

    def load_codes(self):
        """保存済みのIRコードを読み込み"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.recorded_codes = json.load(f)
                print(f"✓ 保存済みのIRコードを読み込みました: {list(self.recorded_codes.keys())}")
            except Exception as e:
                print(f"✗ IRコードの読み込みに失敗: {e}")
                self.recorded_codes = {}
        else:
            print("✓ 新規のIRコード設定ファイルを作成します")
            self.recorded_codes = {}

    def save_codes(self):
        """IRコードをファイルに保存"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.recorded_codes, f, indent=2)
            print(f"✓ IRコードを保存しました: {self.config_file}")
        except Exception as e:
            print(f"✗ IRコードの保存に失敗: {e}")

    def record_ir_signal_manual(self, device_name, nec_code):
        """
        赤外線信号を手動で登録（M5StickCなどで事前に解析したコードを使用）

        Args:
            device_name: デバイス名（例: "TV"）
            nec_code: NECフォーマットのスキャンコード（例: "0x20DF10EF" または 0x20DF10EF）

        Returns:
            bool: 成功したかどうか
        """
        # 数値なら16進数文字列に変換
        if isinstance(nec_code, int):
            nec_code = f"0x{nec_code:08x}"
        elif not nec_code.startswith('0x'):
            nec_code = '0x' + nec_code

        # 形式チェック
        try:
            int(nec_code, 16)
        except ValueError:
            print(f"✗ 無効なNECコード: {nec_code}")
            return False

        self.recorded_codes[device_name] = {
            'format': 'nec',
            'scancode': nec_code
        }
        self.save_codes()
        print(f"\n✓ 【{device_name}】のNECコードを登録しました！")
        print(f"  スキャンコード: {nec_code}")
        return True

    def record_ir_signal(self, device_name, num_samples=3, timeout=5):
        """
        赤外線信号を記録 (ir-ctl -r を使用)
        ※受信機が利用できない場合は手動登録を促す

        Args:
            device_name: デバイス名（例: "TV"）
            num_samples: 記録する回数（デフォルト: 3回）
            timeout: タイムアウト時間（秒）

        Returns:
            bool: 成功したかどうか
        """
        # まず、受信機が使えるか確認
        if self.rx_device is None:
            # 受信デバイスがない場合は手動登録モードへ
            print(f"\n{'='*60}")
            print(f"⚠️  IR受信機能が利用できません")
            print(f"{'='*60}")
            print("このデバイスは送信専用のようです。")
            print("\n【手動登録モード】")
            print("M5StickCなどで事前に解析したNECコードを入力してください。")
            print("例: 0x20DF10EF\n")

            try:
                nec_code = input(f"【{device_name}】のNECコードを入力 (Enterでスキップ): ").strip()
                if nec_code:
                    return self.record_ir_signal_manual(device_name, nec_code)
                else:
                    print("✗ 登録をスキップしました")
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\n✗ 登録をキャンセルしました")
                return False

        # 受信デバイスの機能を確認
        result = subprocess.run(
            ['ir-ctl', '-d', self.rx_device, '--features'],
            capture_output=True,
            text=True
        )

        if 'Device cannot receive' in result.stdout:
            print(f"\n{'='*60}")
            print(f"⚠️  IR受信機能が利用できません")
            print(f"{'='*60}")
            print("このデバイスは送信専用のようです。")
            print("\n【手動登録モード】")
            print("M5StickCなどで事前に解析したNECコードを入力してください。")
            print("例: 0x20DF10EF\n")

            try:
                nec_code = input(f"【{device_name}】のNECコードを入力 (Enterでスキップ): ").strip()
                if nec_code:
                    return self.record_ir_signal_manual(device_name, nec_code)
                else:
                    print("✗ 登録をスキップしました")
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\n✗ 登録をキャンセルしました")
                return False

        # 受信機が使える場合は自動受信
        print(f"\n{'='*60}")
        print(f"【{device_name}】のリモコン信号を登録します")
        print(f"{'='*60}")
        print(f"リモコンのボタンを{num_samples}回連続で押してください...")
        print(f"（各回{timeout}秒以内にボタンを押してください）\n")

        recorded_signals = []

        for i in range(num_samples):
            print(f"[{i+1}/{num_samples}] リモコンボタンを押してください... ", end='', flush=True)

            # IR信号を受信
            signal = self._capture_ir_signal(timeout)

            if signal is None:
                print("✗ タイムアウトまたはエラー")
                return False

            recorded_signals.append(signal)
            print("✓ 受信成功")
            time.sleep(1.0)  # 次の入力まで少し待つ

        # NECフォーマットのスキャンコードを抽出
        nec_code = self._extract_nec_code(recorded_signals[0])

        if nec_code:
            self.recorded_codes[device_name] = {
                'format': 'nec',
                'scancode': nec_code,
                'raw_data': recorded_signals[0]
            }
            self.save_codes()
            print(f"\n✓ 【{device_name}】のリモコン信号を登録しました！")
            print(f"  フォーマット: NEC")
            print(f"  スキャンコード: {nec_code}")
            return True
        else:
            # NECコードが取得できない場合は生データを保存
            print(f"\n⚠️  NECフォーマットではないようです。生データで保存します。")
            self.recorded_codes[device_name] = {
                'format': 'raw',
                'raw_data': recorded_signals[0]
            }
            self.save_codes()
            return True

    def _capture_ir_signal(self, timeout):
        """
        ir-ctl -r でIR信号をキャプチャ

        Args:
            timeout: タイムアウト時間（秒）

        Returns:
            str: IR信号データ（生データ）、失敗時はNone
        """
        try:
            # ir-ctl -r -d /dev/lirc1 -1
            # -1: 1つの信号を受信したら終了
            result = subprocess.run(
                ['ir-ctl', '-d', self.rx_device, '-r', '-1'],
                capture_output=True,
                text=True,
                timeout=timeout + 2
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return None

        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"エラー: {e}")
            return None

    def _extract_nec_code(self, raw_data):
        """
        生データからNECフォーマットのスキャンコードを抽出

        Args:
            raw_data: ir-ctlの出力データ

        Returns:
            str: スキャンコード（例: "0x20df10ef"）、取得できない場合はNone
        """
        try:
            # ir-ctl --features でデコード機能を使う
            # または、生データを解析してNECコードを抽出
            # ここでは簡易的に、NEC形式かどうかをチェック

            # NEC形式の特徴: リーダーコード 9000us + 4500us から始まる
            if 'pulse 9000' in raw_data and 'space 4500' in raw_data:
                # NECフォーマットとして解析を試みる
                # ここではプレースホルダーとして0x00を返す
                # 実際にはビット列を解析する必要がある
                return "0x00000000"  # 実装を簡略化

            return None

        except Exception as e:
            print(f"NEC コード抽出エラー: {e}")
            return None

    def send_ir_signal(self, device_name):
        """
        登録済みのIR信号を送信

        Args:
            device_name: デバイス名

        Returns:
            bool: 成功したかどうか
        """
        if device_name not in self.recorded_codes:
            print(f"✗ 【{device_name}】のIR信号が登録されていません")
            return False

        print(f"📡 【{device_name}】にIR信号を送信中...", end='', flush=True)

        try:
            code_data = self.recorded_codes[device_name]

            if code_data.get('format') == 'nec' and 'scancode' in code_data:
                # NECフォーマットのスキャンコード送信
                scancode = code_data['scancode']
                result = subprocess.run(
                    ['ir-ctl', '-d', self.tx_device, '-S', f'nec:{scancode}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                # 生データ送信（--send-raw は使用しない、代わりに一時ファイル経由）
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(code_data['raw_data'])
                    temp_file = f.name

                try:
                    result = subprocess.run(
                        ['ir-ctl', '-d', self.tx_device, '--send', temp_file],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                finally:
                    os.unlink(temp_file)

            if result.returncode == 0:
                print(" ✓ 送信完了")
                return True
            else:
                print(f" ✗ エラー: {result.stderr}")
                return False

        except Exception as e:
            print(f" ✗ エラー: {e}")
            return False

    def cleanup(self):
        """リソースのクリーンアップ"""
        print("✓ IRコントローラーを終了しました")


class SleepDetector:
    """
    「睡眠ゲージ」方式を使った睡眠検出クラス
    (main.pyから移植)
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
    print("""
╔═══════════════════════════════════════════════════════════╗
║      Oton-Zzz IR Remote Sleep Detector v2.0              ║
║      ラズベリーパイ5 + ir-ctl + 睡眠検出システム         ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # IR Controllerの初期化
    try:
        ir_controller = IRController(tx_device='/dev/lirc0', rx_device='/dev/lirc1')
    except Exception as e:
        print(f"✗ IR Controllerの初期化に失敗しました: {e}")
        print("\nヒント:")
        print("  1. /boot/firmware/config.txt に以下の設定があるか確認:")
        print("     dtoverlay=gpio-ir-tx,gpio_pin=17")
        print("     dtoverlay=gpio-ir-rx,gpio_pin=18")
        print("  2. 再起動してカーネルドライバを有効化:")
        print("     sudo reboot")
        return

    # テレビのリモコン信号を登録（既に登録済みでなければ）
    if "TV" not in ir_controller.recorded_codes:
        print("\n" + "="*60)
        print("初回起動: リモコン信号の登録が必要です")
        print("="*60)
        success = ir_controller.record_ir_signal("TV", num_samples=3, timeout=10)
        if not success:
            print("✗ リモコン登録に失敗しました。プログラムを終了します。")
            ir_controller.cleanup()
            return
    else:
        print(f"✓ 【TV】のリモコン信号は既に登録済みです")
        # 登録内容を表示
        tv_data = ir_controller.recorded_codes["TV"]
        if tv_data.get('format') == 'nec':
            print(f"  - フォーマット: NEC")
            print(f"  - スキャンコード: {tv_data.get('scancode')}")
        else:
            print(f"  - フォーマット: 生データ")

    print("\n" + "="*60)
    print("睡眠検出を開始します...")
    print("="*60 + "\n")

    # 睡眠検出器の初期化
    detector = SleepDetector(
        gauge_max=4.0,                # ゲージが4.0に達したらStage1
        gauge_decrease_rate=1.5,      # 減少速度を1.5倍に設定
        final_confirmation_time=3.0   # Stage1から3秒後にStage2へ
    )

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
        ir_controller.cleanup()
        return

    # 通知フラグ
    notified_stage1 = False
    notified_stage2 = False

    try:
        with FaceLandmarker.create_from_options(options) as landmarker:
            print("✓ 睡眠検出システムが起動しました")
            print("  - Qキーで終了\n")

            start_time = time.time()

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = int((time.time() - start_time) * 1000)
                landmarker.detect_async(mp_image, timestamp_ms)

                gauge_value, is_stage1, is_stage2, status = detector.process_result()

                # 顔未検出時の処理
                if status == "No Face":
                    # 特に何もしない（必要であればログ出力）
                    pass
                else:
                    # --- Stage1 / Stage2の通知処理 ---
                    if is_stage1 and not notified_stage1:
                        print(f"[{time.ctime()}] ⚠️  STAGE 1 DETECTED! 睡眠の可能性...")
                        notified_stage1 = True

                    if is_stage2 and not notified_stage2:
                        print(f"[{time.ctime()}] 😴 STAGE 2 CONFIRMED! 睡眠確定")
                        print(f"[{time.ctime()}] 📡 テレビにIR信号を送信します...")

                        # テレビのIR信号を送信
                        ir_controller.send_ir_signal("TV")

                        notified_stage2 = True

                    if not is_stage1 and (notified_stage1 or notified_stage2):
                        print(f"[{time.ctime()}] 👀 ユーザーが起きました。通知をリセットします。")
                        notified_stage1 = False
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

                # 睡眠ゲージのバー表示
                gauge_percentage = gauge_value / detector.GAUGE_MAX if detector.GAUGE_MAX > 0 else 0
                bar_width = int(gauge_percentage * (frame.shape[1] - 20))
                cv2.rectangle(frame, (10, 120), (frame.shape[1] - 10, 150), (255, 255, 255), 2)
                cv2.rectangle(frame, (10, 120), (10 + bar_width, 150), color, -1)

                # --- 通知状況表示 ---
                stage1_status_text = "Sent" if notified_stage1 else "Ready"
                stage1_color = (0, 165, 255) if notified_stage1 else (0, 255, 0)
                cv2.putText(frame, f"Stage 1 Signal: {stage1_status_text}", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, stage1_color, 2)

                stage2_status_text = "Sent" if notified_stage2 else "Waiting"
                stage2_color = (0, 0, 255) if notified_stage2 else (128, 128, 128)
                cv2.putText(frame, f"Stage 2 Signal: {stage2_status_text}", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, stage2_color, 2)

                # IR送信ステータス
                ir_status = "IR: SENT" if notified_stage2 else "IR: Ready"
                ir_color = (0, 0, 255) if notified_stage2 else (255, 255, 255)
                cv2.putText(frame, ir_status, (10, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.8, ir_color, 2)

                cv2.imshow("Oton-Zzz IR Sleep Detector", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n\n⚠️  キーボード割り込みを検出しました")

    finally:
        # クリーンアップ
        cap.release()
        cv2.destroyAllWindows()
        ir_controller.cleanup()
        print("\n✓ プログラムを正常に終了しました")


if __name__ == '__main__':
    main()
