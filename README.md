# ライブ（リアルタイム）ゆっくりモデリング

テキストを受け取り、AquesTalk によって音声合成を行いながら、ゆっくりキャラクターをリアルタイムでアニメーション表示するシステムです。

## 概要

- 外部システムから HTTP POST でテキストを送信すると、AquesTalk サーバーを通じて日本語音声を合成・再生します。
- 音声の音量データを元に、ブラウザ上のゆっくりキャラクターの口がリアルタイムに動きます。
- 目は一定間隔でランダムに瞬きします。

## システム構成

```
外部システム
    │
    │ POST /speak（テキスト送信）
    ▼
Outbound サーバー（ポート 50200）
    │
    │ 音声合成・再生（AquesTalk）
    ▼
VoiceManager
    │
    │ 音量データをキューに転送
    ▼
Visualizer サーバー（ポート 50201）
    │
    │ SSE（Server-Sent Events）で配信
    ▼
ブラウザ（http://127.0.0.1:50201）
    └── ゆっくりキャラクターのリアルタイムアニメーション
```

## ディレクトリ構成

| パス | 説明 |
|---|---|
| `run.py` | エントリーポイント |
| `source/live_yukkuri_runner.py` | アプリ全体の管理クラス |
| `source/visualizer/` | ブラウザ表示用 Flask サーバー・HTML |
| `source/voice/` | 音声生成・再生管理 |
| `configuration/` | ホスト名・ポート・キャラクター設定 |
| `material/れいむ/` | ゆっくり霊夢の画像素材 |
| `scripts/` | セットアップ用バッチスクリプト |

## セットアップ

### 1. Python 仮想環境の構築

```bat
scripts\install_python_venv.bat
```

### 2. AquesTalk サーバーのダウンロード

```bat
scripts\download_aquestalk_server.bat
```

### 3. ゆっくり霊夢の画像素材のダウンロード

```bat
scripts\download_yukkuri_reimu.bat
```

## 起動方法

```bat
venv_python\Scripts\activate.bat
python run.py
```

起動後、ブラウザで `http://127.0.0.1:50201` を開くとゆっくりキャラクターが表示されます。

## API

### テキスト読み上げ

```
POST http://127.0.0.1:50200/speak
Content-Type: application/json

{"text": "読み上げるテキスト"}
```

### 音声出力の停止フラグ

```
POST http://127.0.0.1:50200/voice_output_stop_flag
Content-Type: application/json

{"voice_output_stop_flag": true}
```

## 設定

| ファイル | 項目 | 説明 |
|---|---|---|
| `configuration/communication_settings.py` | `OUTBOUND_PORT` | 外部テキスト受信ポート（既定: 50200） |
| `configuration/communication_settings.py` | `VISUALIZER_PORT` | ブラウザ表示ポート（既定: 50201） |
| `configuration/person_settings.py` | `MATERIAL_NAME` | 使用するキャラクター素材名（既定: れいむ） |
| `configuration/person_settings.py` | `VOICE_SPEED` | 読み上げ速度（既定: 1.2） |
| `configuration/person_settings.py` | `MOUSE_DELAY_TIME` | 口アニメーションの遅延時間（既定: 0.5 秒） |

## 動作環境

- Windows
- Python 3.x
- AquesTalk サーバー（別途セットアップ必要）
