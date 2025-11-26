#!/usr/bin/env python3
"""
音声合成コントローラー (OpenJTalk)
日本語テキストを音声で読み上げ
"""

import subprocess
import os
import tempfile
import random
import threading


class VoiceController:
    """音声合成コントローラー"""

    def __init__(self, bluetooth_device=None):
        """
        初期化

        Args:
            bluetooth_device: Bluetoothスピーカーのデバイス名（Noneの場合はデフォルト出力）
        """
        self.bluetooth_device = bluetooth_device
        self._is_speaking = False  # 音声再生中フラグ
        self._speak_lock = threading.Lock()  # スレッドセーフ用ロック

        # OpenJTalkのパス確認
        self.check_openjtalk()

    def check_openjtalk(self):
        """OpenJTalkがインストールされているか確認"""
        try:
            result = subprocess.run(['which', 'open_jtalk'],
                                  capture_output=True, text=True, check=True)
            print(f"✓ OpenJTalkが見つかりました: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            raise Exception("OpenJTalkがインストールされていません。\n"
                          "以下のコマンドでインストールしてください:\n"
                          "sudo apt install open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001")

    def speak(self, text, speed=1.0):
        """
        テキストを音声で読み上げ（非同期）

        Args:
            text: 読み上げるテキスト（日本語）
            speed: 読み上げ速度
        """
        # 既に再生中の場合は、新しいスレッドで再生（排他制御は_speak_thread内で行う）
        threading.Thread(target=self._speak_thread, args=(text, speed), daemon=True).start()

    def _speak_thread(self, text, speed):
        """音声合成・再生の実処理（別スレッドで実行）"""
        # ロックを取得して、重ならないようにする
        with self._speak_lock:
            self._is_speaking = True
            print(f"🔊 音声: 「{text}」")

            try:
                # 一時ファイルを作成
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as text_file:
                    text_file.write(text)
                    text_path = text_file.name

                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                    wav_path = wav_file.name

                # OpenJTalkで音声合成
                # 辞書と音声モデルのパス
                dic_path = '/var/lib/mecab/dic/open-jtalk/naist-jdic'
                voice_path = '/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice'

                # 速度パラメータ
                rate = int(speed * 100)  # speed 1.0 → rate 100

                cmd = [
                    'open_jtalk',
                    '-x', dic_path,
                    '-m', voice_path,
                    '-r', str(rate / 100.0),  # 話速（0.5〜2.0）
                    '-ow', wav_path,
                    text_path
                ]

                subprocess.run(cmd, check=True, capture_output=True)

                # WAVファイルを再生
                self._play_audio(wav_path)

            except Exception as e:
                print(f"✗ 音声合成エラー: {e}")

            finally:
                # 一時ファイルを削除
                try:
                    os.unlink(text_path)
                    os.unlink(wav_path)
                except:
                    pass

                self._is_speaking = False

    def _play_audio(self, wav_path):
        """WAVファイルを再生"""
        try:
            if self.bluetooth_device:
                # Bluetoothデバイスに出力（将来的な実装）
                # 現在は通常のオーディオ出力
                pass

            # aplayで再生
            subprocess.run(['aplay', '-q', wav_path], check=True)

        except subprocess.CalledProcessError:
            print("✗ オーディオ再生に失敗しました")

    def speak_warning(self, remaining_seconds=60):
        """
        警告メッセージを読み上げ（ランダムで面白い文言）

        Args:
            remaining_seconds: 残り時間（秒）
        """
        messages = [
            f"お父さーん、あと{remaining_seconds}秒でテレビ消しますよー。起きてるー？",
            f"おい、そこの中年。あと{remaining_seconds}秒で電源オフだぞ。",
            f"父上、そろそろ寝室へお戻りください。{remaining_seconds}秒後に消灯します。",
            f"パパ！寝落ちしてない？あと{remaining_seconds}秒で消すからね！",
            f"起きろー！{remaining_seconds}秒以内に反応しないとテレビ消すぞー！",
            f"おとーさん、いびきかいてるよ。{remaining_seconds}秒後に消すね。",
            f"これより{remaining_seconds}秒後、テレビを強制終了します。異議は認めません。",
            f"あと{remaining_seconds}秒。起きてなかったら電気代節約のためテレビ消すよ。",
        ]

        message = random.choice(messages)
        self.speak(message, speed=1.1)

    def speak_cancel(self):
        """キャンセルメッセージ"""
        messages = [
            "おっ、起きてたんだ。じゃあテレビつけといてあげる。",
            "了解。引き続きご視聴ください。",
            "お、動いた。テレビはそのままにしとくね。",
            "はいはい、起きてますね。キャンセルしました。",
            "ちゃんと見てたのね。失礼しました。",
        ]

        message = random.choice(messages)
        self.speak(message)

    def speak_shutdown(self):
        """電源OFF実行メッセージ"""
        messages = [
            "はい、時間です。テレビ消しまーす。おやすみなさい。",
            "完全に寝てるね。電源オフにします。",
            "お疲れ様でした。テレビを消灯します。",
            "寝落ち確定。テレビ切りまーす。",
            "それでは、お休みなさいませ。",
        ]

        message = random.choice(messages)
        self.speak(message)


class BluetoothPairingHelper:
    """Bluetoothペアリング支援"""

    @staticmethod
    def scan_devices():
        """Bluetoothデバイスをスキャン"""
        print("\n🔍 Bluetoothデバイスをスキャンしています...")
        try:
            # bluetoothctlでスキャン
            result = subprocess.run(
                ['bluetoothctl', 'devices'],
                capture_output=True,
                text=True,
                timeout=5
            )

            devices = []
            for line in result.stdout.split('\n'):
                if line.startswith('Device'):
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[1]
                        name = ' '.join(parts[2:])
                        devices.append({'mac': mac, 'name': name})

            return devices

        except Exception as e:
            print(f"✗ スキャンエラー: {e}")
            return []

    @staticmethod
    def pair_device(mac_address):
        """デバイスとペアリング"""
        print(f"\n🔗 デバイス {mac_address} とペアリングしています...")
        try:
            # ペアリング
            subprocess.run(['bluetoothctl', 'pair', mac_address], timeout=30)
            # 信頼
            subprocess.run(['bluetoothctl', 'trust', mac_address], timeout=10)
            # 接続
            subprocess.run(['bluetoothctl', 'connect', mac_address], timeout=20)

            print(f"✓ ペアリング成功!")
            return True

        except Exception as e:
            print(f"✗ ペアリング失敗: {e}")
            return False


if __name__ == '__main__':
    """テスト用"""
    print("音声合成コントローラーテスト")
    voice = VoiceController()

    print("\n1. 通常の音声テスト")
    voice.speak("こんにちは。音声合成のテストです。")

    print("\n2. 警告メッセージテスト")
    voice.speak_warning(60)

    print("\n3. キャンセルメッセージテスト")
    voice.speak_cancel()

    print("\n4. 電源OFFメッセージテスト")
    voice.speak_shutdown()

    print("\nテスト完了")
