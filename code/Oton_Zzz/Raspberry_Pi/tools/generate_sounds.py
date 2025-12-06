#!/usr/bin/env python3
"""
Oton-Zzz 音声ファイル事前生成スクリプト
OpenJTalkを使用して音声ファイルを生成し、assets/sounds/に保存します。
音声の先頭に無音を追加して、再生開始時の途切れを防止します。
"""

import subprocess
import os
import tempfile
import wave
import array
import shutil

# 出力ディレクトリ
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', 'assets', 'sounds')

# OpenJTalk設定
DIC_PATH = '/var/lib/mecab/dic/open-jtalk/naist-jdic'
VOICE_PATH = '/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice'

# 先頭に追加する無音の長さ（秒）- HDMIスリープ対策
SILENCE_DURATION = 2.0

# 生成する音声リスト
# (ファイル名, テキスト, 速度)
SOUNDS = [
    # === メインシステム ===
    ('startup.wav', 'おとんずー、起動しました', 1.2),
    ('tv_on.wav', '電源がオンになりました', 1.3),
    ('tv_off.wav', '電源がオフになりました', 1.3),
    ('warning.wav', '警告、5秒後にオフです', 1.3),
    ('shutdown.wav', 'おやすみなさい', 1.2),
    ('cancel.wav', 'はいはい、起きてますね。キャンセルしました。', 1.2),

    # === キャリブレーション ===
    ('calib_startup.wav', '自動キャリブレーションを起動しました', 1.2),
    ('calib_start.wav', '開始します', 1.3),
    ('calib_step1.wav', 'ステップ1', 1.3),
    ('calib_step1_done.wav', 'ステップ1、完了', 1.3),
    ('calib_step2.wav', 'ステップ2', 1.3),
    ('calib_step2_done.wav', 'ステップ2、完了', 1.3),
    ('calib_remaining_20.wav', 'あと20秒', 1.3),
    ('calib_remaining_10.wav', 'あと10秒', 1.3),
    ('calib_update.wav', '設定を更新します', 1.3),
    ('calib_save.wav', '保存します', 1.3),
    ('calib_complete.wav', 'キャリブレーション完了。設定を保存しました。', 1.2),

    # === エラー・その他 ===
    ('error.wav', 'エラーが発生しました', 1.3),
    ('test.wav', 'テスト', 1.5),
]


def prepend_silence(wav_path, silence_duration=0.5):
    """
    WAVファイルの先頭に無音を追加

    Args:
        wav_path: WAVファイルのパス
        silence_duration: 追加する無音の長さ（秒）
    """
    # 元のWAVファイルを読み込み
    with wave.open(wav_path, 'rb') as original:
        params = original.getparams()
        frames = original.readframes(original.getnframes())

    # 一時ファイルに無音+元の音声を書き込み
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name

    with wave.open(temp_path, 'wb') as new_wav:
        new_wav.setparams(params)

        # 無音を生成
        silence_samples = int(params.framerate * silence_duration)
        silence = array.array('h', [0] * silence_samples * params.nchannels)
        new_wav.writeframes(silence.tobytes())

        # 元の音声を追加
        new_wav.writeframes(frames)

    # 元のファイルを置き換え
    shutil.move(temp_path, wav_path)


def generate_sound(filename, text, speed=1.0):
    """
    OpenJTalkで音声ファイルを生成（先頭に無音を追加）

    Args:
        filename: 出力ファイル名
        text: 読み上げテキスト
        speed: 読み上げ速度（1.0が標準）
    """
    output_path = os.path.join(OUTPUT_DIR, filename)

    # テキストファイルを一時作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text)
        text_path = f.name

    try:
        # OpenJTalkで音声合成
        cmd = [
            'open_jtalk',
            '-x', DIC_PATH,
            '-m', VOICE_PATH,
            '-r', str(speed),  # 話速
            '-ow', output_path,
            text_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # 先頭に無音を追加
            prepend_silence(output_path, SILENCE_DURATION)
            print(f"✓ {filename}: 「{text}」 (+{SILENCE_DURATION}s無音)")
        else:
            print(f"✗ {filename}: エラー - {result.stderr}")

    finally:
        os.unlink(text_path)


def main():
    """メイン処理"""
    print("=" * 60)
    print("Oton-Zzz 音声ファイル生成（無音追加版）")
    print("=" * 60)
    print(f"出力先: {OUTPUT_DIR}")
    print(f"先頭無音: {SILENCE_DURATION}秒\n")

    # 出力ディレクトリ作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 音声生成
    for filename, text, speed in SOUNDS:
        generate_sound(filename, text, speed)

    print("\n" + "=" * 60)
    print(f"✓ {len(SOUNDS)}個の音声ファイルを生成しました")
    print("=" * 60)


if __name__ == '__main__':
    main()
