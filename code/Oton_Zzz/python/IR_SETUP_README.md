# Oton-Zzz IR Remote Sleep Detector セットアップガイド (ir-ctl版)

## 概要
このシステムは、ラズベリーパイ5で**ir-ctlコマンド**とMediaPipeを使用した睡眠検出システムです。
目を閉じた状態を検出し、Stage2（確定睡眠）の段階でテレビ等の赤外線リモコン信号を送信します。

**LIRCサービス（lircd）は不要**。カーネルドライバ + Pythonのみで動作します。

## ハードウェア構成
- **ラズベリーパイ5**
- **IR送信機**: GPIO17に接続
- **IR受信機**: GPIO18に接続
- **Webカメラ**: 顔検出用

## セットアップ手順

### 1. カーネルドライバの有効化

`/boot/firmware/config.txt`に以下の設定を追記してください：

```bash
sudo nano /boot/firmware/config.txt
```

ファイルの末尾に追加：
```
dtoverlay=gpio-ir-tx,gpio_pin=17
dtoverlay=gpio-ir-rx,gpio_pin=18
```

保存後、ラズベリーパイを再起動：
```bash
sudo reboot
```

### 2. デバイスファイルの確認

再起動後、以下のコマンドで `/dev/lirc0` が存在することを確認：

```bash
ls -la /dev/lirc*
```

出力例：
```
crw-rw---- 1 root video 251, 0 Nov 19 10:23 /dev/lirc0
```

### 3. ir-ctlコマンドの確認

標準でインストールされているはずですが、念のため確認：

```bash
which ir-ctl
```

出力例：
```
/usr/bin/ir-ctl
```

もしインストールされていない場合：
```bash
sudo apt update
sudo apt install v4l-utils
```

### 4. 仮想環境に入る

```bash
cd /home/hxs_jphacks/Oton-Zzz
source .venv/bin/activate
```

### 5. プログラムの実行

```bash
cd /home/hxs_jphacks/Oton-Zzz/code/Oton_Zzz/python
python3 ir_sleep_detector.py
```

## 初回起動時の動作

### リモコン登録プロセス

初回起動時、テレビのリモコン信号を登録する必要があります。

1. プログラムが起動すると、以下のようなプロンプトが表示されます：
   ```
   ============================================================
   初回起動: リモコン信号の登録が必要です
   ============================================================
   【TV】のリモコン信号を登録します
   ============================================================
   リモコンのボタンを3回連続で押してください...
   （各回10秒以内にボタンを押してください）
   ```

2. **テレビリモコンの電源ボタン**（または送信したいボタン）を、IR受信機（GPIO18）に向けて**3回連続**で押してください

3. 各回で以下のように表示されます：
   ```
   [1/3] リモコンボタンを押してください... ✓ 受信成功
   [2/3] リモコンボタンを押してください... ✓ 受信成功
   [3/3] リモコンボタンを押してください... ✓ 受信成功

   ✓ 【TV】のリモコン信号を登録しました！
   フォーマット: NEC (または 生データ)
   ```

4. 登録された信号は `ir_codes.json` ファイルに保存され、次回起動時から登録作業は不要になります

## 動作フロー

### Stage 1: 睡眠の可能性検出
- 目を閉じた状態が約4秒続くと検出
- コンソールに警告メッセージを表示：
  ```
  [日時] ⚠️  STAGE 1 DETECTED! 睡眠の可能性...
  ```

### Stage 2: 睡眠確定 → IR信号送信
- Stage1から3秒間目を閉じ続けた場合に確定
- 自動的にテレビのIR信号を送信（GPIO17から）
- コンソールに送信完了メッセージを表示：
  ```
  [日時] 😴 STAGE 2 CONFIRMED! 睡眠確定
  [日時] 📡 テレビにIR信号を送信します...
  📡 【TV】にIR信号を送信中... ✓ 送信完了
  ```

### 覚醒検出
- 目を開けると自動的に通知フラグがリセットされます：
  ```
  [日時] 👀 ユーザーが起きました。通知をリセットします。
  ```

## 画面表示内容

プログラム実行中、OpenCVウィンドウに以下の情報が表示されます：

- **Status**: 現在の状態
  - `Eyes Open`: 目を開けている
  - `Eyes Closed`: 目を閉じている
  - `Final Confirmation (X.Xs)`: Stage1確定、Stage2まであとX秒
  - `Confirmed Sleep (Stage 2)`: Stage2確定
  - `No Face`: 顔が検出されない

- **Sleep Gauge**: 睡眠ゲージ（0.0〜4.0）
- **睡眠ゲージバー**: 視覚的なゲージ表示
- **Stage 1 Signal**: Stage1通知の状態（Ready / Sent）
- **Stage 2 Signal**: Stage2通知の状態（Waiting / Sent）
- **IR**: IR信号送信の状態（IR: Ready / IR: SENT）

## 終了方法

キーボードの **Q** キーを押すか、**Ctrl+C** で終了できます。

## トラブルシューティング

### エラー: "デバイス /dev/lirc0 が見つかりません"

**原因**: カーネルドライバが有効化されていません

**解決策**:
1. `/boot/firmware/config.txt` に以下を追記:
   ```
   dtoverlay=gpio-ir-tx,gpio_pin=17
   dtoverlay=gpio-ir-rx,gpio_pin=18
   ```
2. 再起動:
   ```bash
   sudo reboot
   ```

### エラー: "タイムアウトまたはエラー"（リモコン登録時）

**原因**: IR受信機が信号を受信できていません

**解決策**:
1. IR受信機がGPIO18に正しく接続されているか確認
2. リモコンをIR受信機に近づけて（5〜10cm程度）、しっかりボタンを押す
3. リモコンの電池残量を確認
4. 別のボタンを試す（電源ボタンなど）

**デバッグ方法**:
```bash
# 手動でIR受信をテスト
ir-ctl -d /dev/lirc0 -r -1

# リモコンボタンを押すと、以下のような出力が表示されるはず：
# pulse 9000
# space 4500
# pulse 560
# ...
```

### IR信号が送信されない

**原因**:
- GPIO17の配線が正しくない
- IR LEDの極性が逆
- 登録された信号が正しくない

**解決策**:
1. IR送信機の配線を確認（GPIO17、GND、VCC）
2. IR LEDの極性を確認（長い方が+）
3. `ir_codes.json` を削除して再登録:
   ```bash
   rm ir_codes.json
   python3 ir_sleep_detector.py
   ```

**手動テスト（NECフォーマットの場合）**:
```bash
# 手動でNECコードを送信してテスト
ir-ctl -d /dev/lirc0 -S nec:0x20df10ef

# または生データを送信
ir-ctl -d /dev/lirc0 --send=ir_test.txt
```

### カメラが開けない場合

**原因**: カメラが使用中、または接続されていません

**解決策**:
```bash
# カメラデバイスを確認
ls /dev/video*

# 他のアプリケーションでカメラが使用されていないか確認
sudo lsof /dev/video0

# カメラの権限確認
groups $USER
# 'video' グループに所属していない場合は追加
sudo usermod -a -G video $USER
```

## ファイル構成

```
/home/hxs_jphacks/Oton-Zzz/code/Oton_Zzz/python/
├── ir_sleep_detector.py              # メインスクリプト (ir-ctl版)
├── main.py                           # オリジナルの睡眠検出スクリプト
├── ir_codes.json                     # IR信号データ（自動生成）
├── face_landmarker_v2_with_blendshapes.task  # MediaPipeモデル
└── IR_SETUP_README.md                # このファイル
```

## パラメータ調整

`ir_sleep_detector.py` の以下の部分で動作を調整できます：

```python
detector = SleepDetector(
    gauge_max=4.0,                # Stage1までの時間（秒）※目を閉じ続ける時間
    gauge_decrease_rate=1.5,      # 目を開けたときのゲージ減少速度
    final_confirmation_time=3.0   # Stage1→Stage2の待機時間（秒）
)
```

**例**: より早く反応させたい場合
```python
detector = SleepDetector(
    gauge_max=2.0,                # 2秒で Stage1
    final_confirmation_time=2.0   # さらに2秒で Stage2
)
```

## 再登録方法

リモコン信号を登録し直したい場合：

```bash
# ir_codes.jsonを削除
rm ir_codes.json

# プログラムを再実行すると、再度登録プロセスが開始されます
python3 ir_sleep_detector.py
```

## 技術詳細

### ir-ctlコマンドについて

このシステムは以下のように動作します：

1. **受信**: `ir-ctl -d /dev/lirc0 -r -1`
   - GPIO18で赤外線信号を受信
   - パルス/スペースの生データを取得

2. **送信**: `ir-ctl -d /dev/lirc0 -S nec:0xXXXXXXXX`
   - NECフォーマットのスキャンコードを送信
   - または生データファイルから送信

3. **カーネルドライバ**: `gpio-ir-tx` / `gpio-ir-rx`
   - 38kHzの搬送波生成はハードウェアで処理
   - Pythonでは波形を制御するだけなので安定動作

### LIRCサービスとの違い

- **LIRCサービス不要**: `lircd` デーモンを起動する必要なし
- **設定ファイル不要**: `lircd.conf` などの複雑な設定ファイルを作成する必要なし
- **シンプル**: Pythonから`subprocess`で`ir-ctl`を叩くだけ

## 複数デバイスの登録（今後の拡張）

現在はテレビのみですが、コードを修正することで複数デバイスに対応可能です。

例: エアコンと照明を追加
```python
# リモコン登録
ir_controller.record_ir_signal("AC", num_samples=3)
ir_controller.record_ir_signal("LIGHT", num_samples=3)

# Stage2で一斉送信
ir_controller.send_ir_signal("TV")
ir_controller.send_ir_signal("AC")
ir_controller.send_ir_signal("LIGHT")
```

## 参考リンク

- [ir-ctl マニュアル](https://www.mankier.com/1/ir-ctl)
- [Linux Infrared Remote Control (LIRC)](https://www.lirc.org/)
- [Raspberry Pi IR GPIO設定](https://www.raspberrypi.com/documentation/computers/configuration.html#gpio-infrared)
