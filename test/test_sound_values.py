import subprocess
import time
import pathlib
import httpx
import atexit
import wave
import io
import struct

from openai import OpenAI

SERVER_EXE = pathlib.Path(__file__).parent.parent / "aquestalk-server.exe"
SERVER_URL = "http://localhost:8080"

# サーバーを別プロセスで起動
server_process = subprocess.Popen(
    [str(SERVER_EXE)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)


def _shutdown_server():
    if server_process.poll() is None:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()


atexit.register(_shutdown_server)

for _ in range(20):
    try:
        httpx.get(SERVER_URL, timeout=0.5)
        break
    except Exception:
        time.sleep(0.5)
else:
    raise RuntimeError("aquestalk-server が起動しませんでした")

client = OpenAI(api_key="a", base_url=f"{SERVER_URL}/v1")

with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="f1",
    input="私は博麗霊夢です。よろしくお願いします。",
) as response:
    audio_data = response.read()

# 1. バイナリデータをファイルのように扱うためにBytesIOでラップ
audio_stream = io.BytesIO(audio_data)

with wave.open(audio_stream, 'rb') as wf:
    # 2. 音声の情報を取得
    n_channels = wf.getnchannels()      # チャンネル数（1:モノラル, 2:ステレオ）
    sampwidth = wf.getsampwidth()       # 1サンプルあたりのバイト数
    framerate = wf.getframerate()       # サンプリング周波数 (Hz)
    n_frames = wf.getnframes()          # 全フレーム数

    # 再生時間を計算 (全フレーム数 / サンプリング周波数)
    play_time = n_frames / framerate

    volumes = []
    interval = 0.1  # 0.1秒刻み

    # 3. 0.1秒刻みでデータをサンプリング
for i in range(int(play_time / interval) + 1):
    time_sec = i * interval
    target_frame = int(time_sec * framerate)

    if target_frame >= n_frames:
        break

    wf.setpos(target_frame)
    # 1フレーム（全チャンネル分）のバイナリを読み込み
    frame_bytes = wf.readframes(1)

    channel_values = []
    for c in range(n_channels):
        # チャンネルごとのバイトを切り出し
        sample_chunk = frame_bytes[c * sampwidth: (c + 1) * sampwidth]

        if not sample_chunk:
            continue

        # --- バイト列を数値に変換 ---
        if sampwidth == 1:
            # 8bitは通常unsigned(0-255)なので128を引いて中央を0にする
            val = int.from_bytes(sample_chunk, 'little', signed=False) - 128
        else:
            # 16bit(2byte), 24bit(3byte), 32bit(4byte) は通常signed
            val = int.from_bytes(sample_chunk, 'little', signed=True)

        channel_values.append(abs(val))

    # チャンネル平均をその時点の音量とする
    volume = sum(channel_values) / n_channels if channel_values else 0
    volumes.append(volume)

# 結果の確認
print(f"再生時間: {play_time:.2f}秒")
print(f"サンプリングされた音量数: {len(volumes)}")
print(f"最初の5件の音量データ: {volumes[:5]}")
