import subprocess
import time
import pathlib
import httpx
import atexit
import winsound

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

winsound.PlaySound(audio_data, winsound.SND_MEMORY)
