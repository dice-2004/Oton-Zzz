#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           Oton-Zzz セットアップスクリプト                 ║"
echo "║    寝落ち検知テレビ自動OFFシステム                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# カレントディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "1. 必要なパッケージをインストールします..."
echo ""

# Pythonパッケージのインストール
echo "Python パッケージをインストール中..."
pip3 install --upgrade pip
pip3 install opencv-python mediapipe flask lgpio

# システムパッケージ（OpenJtalk）のインストール確認
echo ""
echo "2. システムパッケージを確認します..."
if ! command -v open_jtalk &> /dev/null; then
    echo "OpenJTalkがインストールされていません"
    echo "以下のコマンドでインストールしてください:"
    echo "  sudo apt update"
    echo "  sudo apt install -y open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001"
else
    echo "✓ OpenJTalk インストール済み"
fi

# MediaPipeモデルのダウンロード確認
echo ""
echo "3. MediaPipeモデルを確認します..."
MODEL_PATH="models/face_landmarker_v2_with_blendshapes.task"
if [ ! -f "$MODEL_PATH" ]; then
    echo "モデルファイルが見つかりません"
    echo "models/ ディレクトリにMediaPipeモデルを配置してください"
else
    echo "✓ モデルファイル: $MODEL_PATH"
fi

# 設定ファイルの初期化
echo ""
echo "4. 設定ファイルを初期化します..."
python3 main.py --setup

# 実行権限の付与
echo ""
echo "5. 実行権限を設定します..."
chmod +x main.py
chmod +x src/calibration.py
chmod +x src/core.py
chmod +x src/dashboard.py

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║               セットアップ完了！                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "使い方:"
echo "  python3 main.py                      # メインプログラム + ダッシュボードを起動"
echo "  python3 main.py --calibrate          # キャリブレーションのみ実行"
echo "  python3 main.py --test               # システムテストのみ実行"
echo ""
echo "systemdで自動起動する場合:"
echo "  sudo cp oton-zzz.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable oton-zzz.service"
echo "  sudo systemctl start oton-zzz.service"
echo ""
