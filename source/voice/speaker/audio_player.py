from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parents[3]))

import multiprocessing
import winsound


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


class AudioPlayer:
    """winsound を用いて WAV 音声データを別プロセスで再生するクラス。"""

    def play(self, audio_bytes: bytes) -> bool:
        """WAV データを別プロセスで再生し、完了を待つ。

        Returns:
            True: 再生成功  False: 再生失敗
        """
        result_queue: multiprocessing.Queue = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=_play_worker, args=(audio_bytes, result_queue), daemon=True
        )
        proc.start()
        proc.join()

        try:
            return bool(result_queue.get_nowait())
        except Exception:
            return False

    def play_async(self, audio_bytes: bytes) -> multiprocessing.Process:
        """WAV データの再生を別プロセスで開始し、即座に返す(非ブロッキング)。

        Returns:
            起動した Process オブジェクト。終了を待つ場合は proc.join() を呼ぶ。
        """
        result_queue: multiprocessing.Queue = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=_play_worker, args=(audio_bytes, result_queue), daemon=True
        )
        proc.start()
        return proc
