# 🎉 Oton-Zzz Phase 1 完全版 - テレビ状態同期対応

## ✅ 実装した機能

### **新機能: テレビ状態完全同期**
- 📡 **リモコン信号常時監視** - バックグラウンドでIR信号を監視
- 🔄 **状態自動同期** - テレビON/OFFとシステムACTIVE/SLEEPを連動
- 💤 **スリープモード** - テレビOFF時は睡眠検出を停止、リモコン待機
- 🟢 **アクティブモード** - テレビON時に睡眠検出を自動再開

### **Phase 1 基本機能**
- 🟢🟡🔴 **LED状態表示** (GPIO 22, 23, 24) ※オプション
- 🔊 **音声警告システム** (OpenJTalk)
- ⏰ **1分警告 + 30秒再警告**
- 📺 **テレビ状態管理**

---

## 🔄 動作フロー（完全版）

### シナリオ1: 通常の睡眠検出フロー

```
1. テレビON（リモコン操作）
   📺 テレビ: OFF → ON
   🟢 システム: SLEEP → ACTIVE
   🔊 音声: "テレビがつきました。睡眠検出を開始します。"

2. 視聴中...
   👀 カメラで顔検出
   📊 Sleep Gauge監視中

3. 目を閉じる（4秒継続）
   ⚠️  Stage 1検出
   🟡 黄LED点滅
   🔊 音声: "お父さーん、あと60秒でテレビ消しますよー..."

4. 30秒経過
   ⚠️  残り30秒
   🔊 音声: 再警告

5. 60秒経過（まだ寝ている）
   😴 Stage 2確定
   🔴 赤LED点灯
   🔊 音声: "はい、時間です。テレビ消しまーす..."
   📡 IR送信 → テレビOFF
   📺 テレビ: ON → OFF
   💤 システム: ACTIVE → SLEEP
   ```

### シナリオ2: 警告中に起きた場合

```
1-3. (上記と同じ)

4. ユーザーが目を開ける
   👀 覚醒検出
   🟢 緑LED点灯
   🔊 音声: "おっ、起きてたんだ。じゃあテレビつけといてあげる。"
   📺 テレビ: ON（そのまま）
   🟢 システム: ACTIVE（継続）
```

### シナリオ3: 視聴中にリモコンでテレビをOFF

```
1. テレビON、視聴中
   🟢 システム: ACTIVE

2. リモコンでテレビOFF
   📡 IR信号検出
   📺 テレビ: ON → OFF
   💤 システム: ACTIVE → SLEEP
   🔊 音声: "テレビが消されました。待機モードに入ります。"
   💡 LED: すべて消灯
   😴 カメラ: 検出停止、待機モード
```

### シナリオ4: スリープ中にテレビをON

```
1. システムSLEEP状態
   💤 待機中...

2. リモコンでテレビON
   📡 IR信号検出
   📺 テレビ: OFF → ON
   🟢 システム: SLEEP → ACTIVE
   🔊 音声: "テレビがつきました。睡眠検出を開始します。"
   🟢 緑LED点灯
   👀 カメラ: 検出再開
```

---

## 🚀 実行方法

```bash
cd /home/hxs_jphacks/Oton-Zzz
source .venv/bin/activate
cd code/Oton_Zzz/python
python3 oton_zzz_phase1.py
```

### 初回起動時
リモコン信号の登録が必要です（3回ボタンを押す）。
2回目以降は自動的にスキップされます。

---

## 📊 システム状態

### ACTIVE状態（テレビON）
- ✅ 睡眠検出: 実行中
- ✅ カメラ: 動作中
- ✅ Sleep Gauge: 監視中
- ✅ LED: 緑（正常）/ 黄（警告）/ 赤（実行）
- ✅ 音声: 有効

### SLEEP状態（テレビOFF）
- ❌ 睡眠検出: 停止
- ❌ カメラ: 待機モード
- ❌ Sleep Gauge: リセット
- ❌ LED: すべて消灯
- ✅ IRリモコン監視: 継続（バックグラウンド）
- ✅ 音声: 状態変更時のみ

---

## 🧪 テスト方法

### 1. IR監視マネージャーのテスト
```bash
python3 ir_monitor.py
```
リモコンボタンを押して、状態変更が検出されるか確認

### 2. システム状態マネージャーのテスト
```bash
python3 system_state_manager.py
```
ACTIVE/SLEEP切り替えの動作確認

### 3. 統合テスト
```bash
python3 oton_zzz_phase1.py
```

**テストシナリオ:**
1. プログラム起動（SLEEP状態で開始）
2. リモコンボタンを押す → テレビON → ACTIVE
3. 目を閉じて4秒 → Stage 1警告
4. 目を開ける → キャンセル
5. リモコンボタンを押す → テレビOFF → SLEEP
6. リモコンボタンを押す → テレビON → ACTIVE（再開）

---

## 🎛️ パラメータ調整

`oton_zzz_phase1.py` の95行目あたり:

```python
detector = SleepDetector(
    gauge_max=4.0,                # Stage1までの時間（秒）
    gauge_decrease_rate=1.5,      # 覚醒時のゲージ減少速度
    final_confirmation_time=60.0  # 警告時間（秒）
)
```

**警告時間を30秒に短縮:**
```python
final_confirmation_time=30.0
```

**より敏感に:**
```python
gauge_max=2.0,                # 2秒でStage1
final_confirmation_time=20.0  # 20秒警告
```

---

## 📁 新規作成ファイル

1. **`ir_monitor.py`** - IRリモコン信号を常時監視
2. **`system_state_manager.py`** - システムACTIVE/SLEEP状態管理
3. **`oton_zzz_phase1.py`** - Phase 1統合プログラム（更新版）

---

## 🐛 トラブルシューティング

### リモコン信号が検出されない

1. **IR受信機の確認:**
   ```bash
   ls -la /dev/lirc*
   # /dev/lirc1 が存在するか確認
   ```

2. **手動テスト:**
   ```bash
   ir-ctl -d /dev/lirc1 -r -1
   # リモコンボタンを押して信号が表示されるか
   ```

3. **デバイスの機能確認:**
   ```bash
   ir-ctl -d /dev/lirc1 --features
   # "Device can receive raw IR" が表示されるか
   ```

### 状態が切り替わらない

`ir_monitor.py`を単独で実行してテスト:
```bash
python3 ir_monitor.py
# リモコンを押して状態変化を確認
```

### 音声が再生されない

Bluetoothスピーカーの接続を確認:
```bash
bluetoothctl devices
bluetoothctl info XX:XX:XX:XX:XX:XX
```

---

## 🎉 完成！

これで、テレビとOton-Zzzの状態が完全に同期し、以下の動作が実現しました：

✅ **テレビON** → システムACTIVE（睡眠検出開始）
✅ **テレビOFF** → システムSLEEP（睡眠検出停止、リモコン待機）
✅ **自動OFF後** → システムSLEEP（待機）
✅ **リモコンで復帰** → システムACTIVE（検出再開）

準備ができたら、**Phase 2（ログ + Webダッシュボード）** に進みましょう！
