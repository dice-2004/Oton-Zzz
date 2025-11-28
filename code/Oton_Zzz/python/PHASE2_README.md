# 📊 Phase 2: ログ記録とWebダッシュボード

## ✅ 実装機能

1. **データベース管理 (`database_manager.py`)**
   - SQLiteを使用してイベントログを永続化
   - 記録内容: 日時, イベントタイプ (睡眠検知, TV操作), 詳細

2. **ログ記録機能**
   - `oton_zzz_headless.py` / `oton_zzz_phase1.py` に統合
   - 以下のイベントを自動記録:
     - `TV_ON`: リモコンでテレビをつけた時
     - `TV_OFF`: リモコンでテレビを消した時
     - `SLEEP_DETECTED`: 寝落ち検知で自動OFFした時

3. **Webダッシュボード (`dashboard.py`)**
   - Flask製のWebインターフェース
   - **表示内容**:
     - 今週の寝落ち回数
     - 無駄になった時間（警告〜OFFまで）
     - 推定節約額（もし朝までついていたら...）
     - 最近の活動ログ一覧
     - 節約インパクトの円グラフ

---

## 🚀 実行方法

### 1. メインシステムの実行（ログ記録開始）
通常通りシステムを実行すると、自動的にログが `oton_zzz.db` に保存されます。

```bash
source /home/hxs_jphacks/Oton-Zzz/.venv/bin/activate
python3 oton_zzz_headless.py
```

### 2. ダッシュボードの起動
別のターミナルを開いて実行してください。

```bash
source /home/hxs_jphacks/Oton-Zzz/.venv/bin/activate
python3 dashboard.py
```

### 3. ブラウザでアクセス
同じネットワーク内のPCやスマホからアクセスできます。

- URL: `http://<ラズパイのIPアドレス>:5000`
- ローカル: `http://localhost:5000`

---

## 💡 節約額の計算ロジック

- **電気代単価**: 31円/kWh（目安）
- **テレビ消費電力**: 100W（目安）
- **推定節約額**: 1回の寝落ちにつき、平均4時間テレビがつけっぱなしになっていたと仮定して計算
  - `4時間 × 0.1kW × 31円 = 約12.4円` / 回

---

## 📁 ファイル構成

```
python/
├── database_manager.py    # データベース管理クラス
├── dashboard.py           # Flask Webアプリ
├── templates/
│   └── index.html         # ダッシュボードHTML
├── oton_zzz.db            # SQLiteデータベース（自動生成）
└── ...
```
