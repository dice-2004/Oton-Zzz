# 🔧 Phase 1 バグ修正: IR送信後の誤検出問題

## 🐛 問題

Stage 2でIR信号を送信した後、IR監視スレッドが自分の送信した信号を受信してしまい、以下の問題が発生していました：

1. Stage 2 → IR送信でテレビOFF
2. IR監視が送信信号を検出
3. テレビ状態が OFF → ON にトグル
4. 「テレビがつきました」の音声が再生（誤動作）

---

## ✅ 解決策

**IR送信時にIR監視を一時停止する機能を実装**

### 修正内容

#### 1. `ir_monitor.py`
- `pause()` メソッド追加 - IR監視を一時停止
- `resume()` メソッド追加 - IR監視を再開
- `is_paused` フラグ追加 - 一時停止状態を管理
- `_monitor_loop()` 修正 - 一時停止中はIR信号を無視

#### 2. `oton_zzz_headless.py`
Stage 2のIR送信部分を以下のように修正：

```python
# IR監視を一時停止
ir_monitor.pause()
time.sleep(0.5)  # 少し待機

# IR信号送信
ir_controller.send_ir_signal("TV")
tv_state.turn_off()

# 送信信号が完全に消えるまで待機
time.sleep(2.0)

# IR監視を再開
ir_monitor.resume()
```

#### 3. `oton_zzz_phase1.py`
ヘッドレス版と同じ修正を適用

---

## 🎯 動作フロー（修正後）

### Stage 2実行時

```
1. 睡眠確定（Stage 2）
   😴 "睡眠確定"

2. 音声再生
   🔊 "はい、時間です。テレビ消しまーす..."

3. IR監視を一時停止 ⏸️
   ⚠️  自分の送信信号を受信しないように

4. IR送信
   📡 テレビにIR信号送信
   📺 テレビ状態: ON → OFF

5. 2秒待機 ⏱️
   送信信号が完全に消えるまで待つ

6. IR監視を再開 ▶️
   リモコン監視を継続

7. システムSLEEPへ
   💤 ACTIVE → SLEEP
```

これにより、自分の送信信号を受信することがなくなり、正しく動作するようになりました。

---

## ✅ テスト確認

修正後、以下が正常に動作することを確認してください：

1. **Stage 2でテレビOFF実行**
   - ✅ 「テレビ消しまーす」の音声のみ再生
   - ❌ 「テレビがつきました」は再生されない
   - ✅ システムがSLEEP状態に移行

2. **SLEEP状態でリモコン操作**
   - ✅ リモコンを押すと正常にテレビON検出
   - ✅ 「テレビがつきました」が再生
   - ✅ システムがACTIVE状態に移行

---

## 🚀 実行

```bash
source /home/hxs_jphacks/Oton-Zzz/.venv/bin/activate
python3 oton_zzz_headless.py
```

修正が正しく動作するか確認してください！
