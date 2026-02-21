from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))

import threading

from source.voice.speaker.voice_generator import VoiceGenerator
from source.voice.speaker.audio_player import AudioPlayer


class VoiceManager:
    """音声生成・再生・音量キュー管理クラス。

    - VoiceGenerator を用いてテキストから WAV データと音量値を生成する。
    - AudioPlayer を別プロセスで起動して再生する。
    - 生成した音量値を内部キューで管理し、外部から取得できる。
    """

    def __init__(self) -> None:
        self._voice_generator = VoiceGenerator()
        self._audio_player = AudioPlayer()

        self._sound_queue: list[dict] = []
        self._sound_queue_lock = threading.Lock()

    def speak(self, text: str) -> tuple[bytes, list[float], float]:
        """テキストから音声を生成・再生し、結果を返す。

        Args:
            text: 読み上げテキスト

        Returns:
            (audio_bytes, scaled_sound_values, sample_time)
        """
        all_sound_values: list[float] = []
        last_audio_data: bytes | None = None
        last_sample_time = 0.0

        for audio_data, sound_values, sample_time in self._voice_generator.generate_sequential(text):
            # 音声再生を別プロセスで開始
            play_proc = self._audio_player.play_async(audio_data)

            # 音量値を文ごとにキューへ追加
            self.enqueue_sound(sound_values, sample_time)

            # 再生完了を待機
            play_proc.join()

            last_audio_data = audio_data
            last_sample_time = sample_time
            all_sound_values.extend(sound_values)

        if last_audio_data is None:
            raise ValueError('text is empty')

        return last_audio_data, all_sound_values, last_sample_time

    def enqueue_sound(self, sound_values: list[float], sample_time: float) -> None:
        """音量データをキューに追加する。"""
        with self._sound_queue_lock:
            self._sound_queue.append({
                'sound_values': sound_values,
                'sample_time': sample_time,
            })

    def dequeue_sound(self) -> dict | None:
        """キューから音量データを 1 件取り出す。キューが空の場合は None を返す。"""
        with self._sound_queue_lock:
            if self._sound_queue:
                return self._sound_queue.pop(0)
        return None
