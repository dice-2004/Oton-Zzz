# Oton-Zzz (おとん・ずずず)

**寝落ち検知テレビ自動OFFシステム**

カメラでユーザーの睡眠状態を監視し、寝落ちを検知すると自動的にテレビを消すシステムです。
Raspberry Pi 5 と赤外線(IR)制御を使用して実装されています。

## 🌟 主な機能

- **😴 睡眠検知**: MediaPipeを使用した高精度な閉眼検知
- **📺 テレビ制御**: 寝落ち確定時にIR信号でテレビをOFF
- **🔄 状態同期**: リモコン操作を監視し、テレビのON/OFFとシステムの状態を同期
- **📊 ダッシュボード**: 寝落ち回数や節約効果をWebブラウザで確認可能
- **🔊 音声案内**: OpenJTalkによる親しみやすい音声フィードバック

## 🚀 クイックスタート

詳細なセットアップ手順は [docs/QUICKSTART.md](docs/QUICKSTART.md) を参照してください。

```bash
# 実行
cd /home/hxs_jphacks/Oton-Zzz/code/Oton_Zzz/Raspberry_Pi
python3 main.py
```

## 📂 ディレクトリ構成

- `main.py`: エントリーポイント
- `src/`: ソースコード
  - `core.py`: コアロジック
  - `detector.py`: 睡眠検知
  - `dashboard.py`: Webダッシュボード
  - `db.py`: データベース管理
- `config/`: 設定ファイル
- `data/`: データベースファイル
- `docs/`: ドキュメント

## 📖 ドキュメント

- [クイックスタートガイド](docs/QUICKSTART.md)
- [機能一覧](docs/FEATURES.md)
- [セットアップガイド (IR)](docs/IR_SETUP_README.md)
- [キャリブレーション](docs/CALIBRATION.md)
- [デモ設定](docs/DEMO_CONFIG.md)
