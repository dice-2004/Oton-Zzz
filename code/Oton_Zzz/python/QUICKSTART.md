# Oton-Zzz IR Sleep Detector クイックスタートガイド

## 🚀 最速セットアップ手順

### 準備完了チェック ✅

以下がすでに完了しています：
- ✅ `/boot/firmware/config.txt` にIR設定済み
- ✅ `/dev/lirc0` デバイスが存在
- ✅ `ir-ctl` コマンドが利用可能
- ✅ IR送信機能が動作確認済み

### 実行手順

#### 1. 仮想環境に入る
```bash
cd /home/hxs_jphacks/Oton-Zzz
source .venv/bin/activate
cd code/Oton_Zzz/python
```

#### 2. プログラムを実行（初回）
```bash
python3 ir_sleep_detector.py
```

#### 3. リモコン登録

初回起動時、以下のように表示されます：

```
⚠️  IR受信機能が利用できません
============================================================
このデバイスは送信専用のようです。

【手動登録モード】
M5StickCなどで事前に解析したNECコードを入力してください。
例: 0x20DF10EF

【TV】のNECコードを入力 (Enterでスキップ):
```

**ここで、M5StickC等で事前に解析したテレビのNECコードを入力してください。**

例:
```
0x20DF10EF
```

または、16進数なら `0x` なしでもOK：
```
20DF10EF
```

#### 4. 睡眠検出開始

登録が完了すると、自動的に睡眠検出が開始されます：

```
============================================================
睡眠検出を開始します...
============================================================

✓ 睡眠検出システムが起動しました
  - Qキーで終了
```

## 📡 動作フロー

1. **目を閉じる** → Sleep Gaugeが上昇
2. **約4秒間閉じ続ける** → Stage 1検出
   ```
   ⚠️  STAGE 1 DETECTED! 睡眠の可能性...
   ```
3. **さらに3秒間閉じ続ける** → Stage 2確定 → **IR信号送信！**
   ```
   😴 STAGE 2 CONFIRMED! 睡眠確定
   📡 テレビにIR信号を送信します...
   📡 【TV】にIR信号を送信中... ✓ 送信完了
   ```

## 🔧 テストツール

### IR送信テスト
```bash
# デフォルトコード（0x20DF10EF）で送信テスト
python3 test_ir_send.py

# 特定のNECコードでテスト
python3 test_ir_send.py 0xYOURCODE
```

## 💾 再登録方法

別のリモコンコードに変更したい場合：

```bash
# 設定ファイルを削除
rm ir_codes.json

# 再実行すると、再度登録画面が表示される
python3 ir_sleep_detector.py
```

## 📂 関連ファイル

| ファイル名 | 説明 |
|-----------|------|
| `ir_sleep_detector.py` | メインプログラム（IR送信 + 睡眠検出） |
| `main.py` | オリジナルの睡眠検出プログラム（IR機能なし） |
| `ir_codes.json` | 登録されたIRコード（自動生成） |
| `test_ir_send.py` | IR送信テストツール |
| `test_ir_receive.py` | IR受信テストツール（診断用） |
| `IR_SETUP_README.md` | 詳細なセットアップガイド |

## 🎯 M5StickCでのNECコード取得方法

M5StickCをお持ちの場合、以下の手順でNECコードを取得できます：

1. M5StickCにIR受信スケッチを書き込む
2. テレビリモコンの電源ボタンを押す
3. シリアルモニタに表示されるNECコードをメモ
   ```
   Protocol: NEC
   Address: 0x20
   Command: 0xDF
   Full code: 0x20DF10EF  ← これを使用
   ```
4. ラズパイのプログラム起動時にこのコードを入力

## ⚙️ パラメータ調整

`ir_sleep_detector.py` の430行目あたり：

```python
detector = SleepDetector(
    gauge_max=4.0,                # Stage1までの時間（秒）
    gauge_decrease_rate=1.5,      # 覚醒時のゲージ減少速度
    final_confirmation_time=3.0   # Stage1→Stage2の待機時間（秒）
)
```

**より敏感に反応させたい場合**:
```python
detector = SleepDetector(
    gauge_max=2.0,                # 2秒で Stage1
    final_confirmation_time=2.0   # さらに2秒で Stage2
)
```

## 🐛 トラブルシューティング

### Q: NECコードを入力したのにテレビが反応しない

**A**: 以下を確認してください：
1. IR送信LEDがGPIO17に正しく接続されているか
2. IR LEDの極性（長い方が+）
3. NECコードが正しいか（M5StickCで再確認）
4. テストツールで手動送信を試す：
   ```bash
   python3 test_ir_send.py 0xYOURCODE
   ```

### Q: カメラが起動しない

**A**:
```bash
# カメラデバイスを確認
ls /dev/video*

# 権限確認
groups
# 'video' グループに所属していない場合
sudo usermod -a -G video $USER
# ログアウト→ログインして反映
```

### Q: Sleep Gaugeが上がらない

**A**: MediaPipeのBlendshape検出がうまくいっていない可能性があります：
1. カメラにしっかり顔を映す
2. 照明を明るくする
3. `blink_threshold` パラメータを調整（0.5 → 0.3など）

## 🎉 完成！

これで、目を閉じるとテレビの電源が自動的にOFFになるシステムの完成です！

終了するには **Q** キーまたは **Ctrl+C** を押してください。
