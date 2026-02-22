# ライブ（リアルタイム）ゆっくりモデリング

テキストを受け取り、AquesTalk によって音声合成を行いながら、ゆっくりキャラクターをリアルタイムでアニメーション表示するシステムです。

## 概要

外部システムから HTTP POST でテキストを送信すると、AquesTalk サーバーを通じて日本語音声を合成・再生します。

音声の音量データを元に、ブラウザ上のゆっくりキャラクターの口がリアルタイムに動きます。

目は一定間隔でランダムに瞬きします。

現在のデフォルトキャラ設定は 博麗霊夢（東方 Project）です。

## 動作環境

- Windows11
- Python 3.14（動作確認済みバージョン）

## セットアップ

### 1. Python 仮想環境の構築

```bat
scripts\install_python_venv.bat
```

### 2. AquesTalk サーバーのダウンロード

```bat
scripts\download_aquestalk_server.bat
```

AquesTalk TTS API サーバー (https://github.com/Lqm1/aquestalk-server) を使用します。必ず利用規約をご確認ください。

### 3. ゆっくり霊夢の画像素材のダウンロード

```bat
scripts\download_yukkuri_reimu.bat
```

ゆっくり霊夢の画像はきつねさんの画像素材 (http://nicotalk.com/charasozai_kt.html) を使用します。必ず利用規約をご確認ください。

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

## システム構成

概要クラス図

![概要クラス図](./document/system/概要クラス図.svg)

| パス | 説明 |
| --- | --- |
| `run.py` | エントリーポイント |
| `source/live_yukkuri_runner.py` | アプリ全体の管理クラス |
| `source/visualizer/` | ブラウザ表示用 Flask サーバー・HTML |
| `source/voice/` | 音声生成・再生管理 |
| `configuration/` | ホスト名・ポート・キャラクター設定 |
| `material/` | ゆっくりの画像素材 |
| `scripts/` | セットアップ用バッチスクリプト |

## ライセンス

MIT License - 詳細は [LICENSE](./LICENSE.txt) を参照してください。
