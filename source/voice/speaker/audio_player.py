from __future__ import annotations

import sys
import time
import threading
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parents[3]))

import multiprocessing
import winsound
import httpx
from flask import Flask, jsonify, request

from configuration.communcation_settings import AUDIO_PLAYER_PORT, HOST_NAME

PLAY_TIMEOUT_SECONDS = 120.0


app = Flask(__name__)
_server_lock = threading.Lock()
_server_thread: threading.Thread | None = None


def _play_worker(audio_bytes: bytes, result_queue: multiprocessing.Queue) -> None:
    """別プロセスで WAV データを再生するワーカー関数。

    再生結果を *result_queue* に True(成功) / False(失敗) で通知する。
    """
    try:
        winsound.PlaySound(audio_bytes, winsound.SND_MEMORY)
        result_queue.put(True)
    except Exception:
        try:
            result_queue.put(False)
        except Exception:
            pass


@app.route('/health', methods=['GET'])
def health() -> tuple[dict[str, str], int]:
    return {'status': 'ok'}, 200


@app.route('/play', methods=['POST'])
def play_audio() -> tuple[dict[str, bool | str], int]:
    audio_bytes = request.get_data()
    if not audio_bytes:
        return {'status': 'error', 'message': 'No audio data provided'}, 400

    result_queue: multiprocessing.Queue = multiprocessing.Queue()
    proc = multiprocessing.Process(
        target=_play_worker, args=(audio_bytes, result_queue), daemon=True
    )
    proc.start()
    proc.join()

    try:
        played = bool(result_queue.get_nowait())
    except Exception:
        played = False

    return {'status': 'success', 'played': played}, 200


def _is_server_alive() -> bool:
    try:
        response = httpx.get(
            f'http://127.0.0.1:{AUDIO_PLAYER_PORT}/health', timeout=0.5)
        return response.status_code == 200
    except Exception:
        return False


def _run_audio_server() -> None:
    app.run(
        host=HOST_NAME,
        port=AUDIO_PLAYER_PORT,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


def ensure_audio_server_running() -> None:
    global _server_thread

    if _is_server_alive():
        return

    with _server_lock:
        if _is_server_alive():
            return

        if _server_thread is None or not _server_thread.is_alive():
            _server_thread = threading.Thread(
                target=_run_audio_server,
                daemon=True,
                name='audio-player-server',
            )
            _server_thread.start()

    for _ in range(40):
        if _is_server_alive():
            return
        time.sleep(0.1)

    raise RuntimeError('audio player server failed to start')


class AudioPlayer:
    """Flask の再生サーバーへ音声データを送信して再生するクラス。"""

    def __init__(self) -> None:
        ensure_audio_server_running()
        self._play_url = f'http://127.0.0.1:{AUDIO_PLAYER_PORT}/play'

    def play(self, audio_bytes: bytes) -> bool:
        """WAV データを再生サーバーへ送信して再生する。

        Returns:
            True: 再生成功  False: 再生失敗
        """
        response = httpx.post(
            self._play_url,
            content=audio_bytes,
            timeout=PLAY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        data = response.json()
        return bool(data.get('played', False))


if __name__ == '__main__':
    _run_audio_server()
