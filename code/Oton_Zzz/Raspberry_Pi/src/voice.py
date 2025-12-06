#!/usr/bin/env python3
"""
音声コントローラー（事前読み込み版）
起動時にすべての音声ファイルをメモリに読み込み、高速再生を実現します。
"""

import os
import threading
import time

# pygameのウェルカムメッセージを非表示
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame


class VoiceController:
    """音声コントローラー（事前読み込み版）"""

    def __init__(self):
        """初期化：音声ファイルを事前読み込み"""
        self._is_speaking = False
        self._speak_lock = threading.Lock()

        # 音声ファイルディレクトリ
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.sounds_dir = os.path.join(script_dir, '..', 'assets', 'sounds')

        # pygame.mixer初期化
        pygame.mixer.init(frequency=48000, size=-16, channels=1, buffer=2048)

        # 音声キーとファイル名のマッピング
        self.sound_mapping = {
            # メインシステム
            'startup': 'startup.wav',
            'tv_on': 'tv_on.wav',
            'tv_off': 'tv_off.wav',
            'warning': 'warning.wav',
            'shutdown': 'shutdown.wav',
            'cancel': 'cancel.wav',

            # キャリブレーション
            'calib_startup': 'calib_startup.wav',
            'calib_start': 'calib_start.wav',
            'calib_step1': 'calib_step1.wav',
            'calib_step1_done': 'calib_step1_done.wav',
            'calib_step2': 'calib_step2.wav',
            'calib_step2_done': 'calib_step2_done.wav',
            'calib_remaining_20': 'calib_remaining_20.wav',
            'calib_remaining_10': 'calib_remaining_10.wav',
            'calib_update': 'calib_update.wav',
            'calib_save': 'calib_save.wav',
            'calib_complete': 'calib_complete.wav',

            # その他
            'error': 'error.wav',
            'test': 'test.wav',
        }

        # 音声ファイルを事前読み込み
        self.sounds = {}
        self._load_all_sounds()

        # オーディオデバイスをウェイクアップ（初回再生時の途切れ防止）
        self._wakeup_audio()

        print("✓ 音声コントローラーを初期化しました（事前読み込み版）")

    def _load_all_sounds(self):
        """すべての音声ファイルをメモリに読み込む"""
        print("🔊 音声ファイルを読み込み中...")
        loaded_count = 0

        for key, filename in self.sound_mapping.items():
            wav_path = os.path.join(self.sounds_dir, filename)
            if os.path.exists(wav_path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(wav_path)
                    loaded_count += 1
                except Exception as e:
                    print(f"⚠️  {filename} の読み込みに失敗: {e}")
            else:
                print(f"⚠️  {filename} が見つかりません")

        print(f"✓ {loaded_count}/{len(self.sound_mapping)}個の音声ファイルを読み込みました")

    def _wakeup_audio(self):
        """オーディオデバイスをウェイクアップ（短い無音を再生）"""
        try:
            # 短い無音サウンドを生成して再生
            import array
            # 0.5秒の無音（48kHz, 16bit, mono）
            silence_samples = int(48000 * 0.5)
            silence_data = array.array('h', [0] * silence_samples)
            silence_sound = pygame.mixer.Sound(buffer=silence_data)
            silence_sound.play()
            # 再生完了を待つ
            while pygame.mixer.get_busy():
                time.sleep(0.05)
            # デバイスが安定するまで少し待機
            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️  オーディオウェイクアップに失敗: {e}")

    def speak(self, key):
        """
        音声を再生（非同期）

        Args:
            key: 音声キー（例: 'startup', 'warning'）
        """
        threading.Thread(target=self._speak_thread, args=(key,), daemon=True).start()

    def speak_sync(self, key):
        """
        音声を再生（同期版：完了まで待機）

        Args:
            key: 音声キー
        """
        self.speak(key)
        time.sleep(0.1)
        while self._is_speaking:
            time.sleep(0.05)

    def _speak_thread(self, key):
        """音声再生の実処理（別スレッド）"""
        with self._speak_lock:
            self._is_speaking = True

            try:
                sound = self.sounds.get(key)
                if sound:
                    print(f"🔊 音声: 「{key}」")
                    sound.play()
                    # 再生完了まで待機
                    while pygame.mixer.get_busy():
                        time.sleep(0.05)
                else:
                    print(f"⚠️  音声キーが未登録: {key}")

            except Exception as e:
                print(f"✗ 音声再生エラー: {e}")

            finally:
                self._is_speaking = False

    def speak_warning(self, remaining_seconds=5):
        """警告メッセージを再生"""
        self.speak('warning')

    def speak_cancel(self):
        """キャンセルメッセージを再生"""
        self.speak('cancel')

    def speak_shutdown(self):
        """電源OFFメッセージを再生"""
        self.speak('shutdown')

    def cleanup(self):
        """クリーンアップ"""
        pygame.mixer.quit()


if __name__ == '__main__':
    """テスト用"""
    print("音声コントローラーテスト（事前読み込み版）\n")
    voice = VoiceController()

    print("\n1. 起動音テスト")
    voice.speak_sync('startup')
    time.sleep(0.3)

    print("\n2. 警告音テスト")
    voice.speak_sync('warning')
    time.sleep(0.3)

    print("\n3. キャンセル音テスト")
    voice.speak_sync('cancel')
    time.sleep(0.3)

    print("\n4. シャットダウン音テスト")
    voice.speak_sync('shutdown')
    time.sleep(0.3)

    voice.cleanup()
    print("\nテスト完了")
