from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))

import threading
import queue

from source.voice.speaker.voice_generator import VoiceGenerator
from source.voice.speaker.audio_player import AudioPlayer

from configuration.person_settings import (
    TEXT_FOR_SPEAK_REPLACEMENTS,
)


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
        # When True, ongoing and future voice output should stop
        self._voice_output_stop_flag = False

    def speak(self, text: str) -> tuple[bytes, list[float], float]:
        """テキストから音声を生成・再生し、結果を返す。

        Args:
            text: 読み上げテキスト

        Returns:
            (audio_bytes, scaled_sound_values, sample_time)
        """
        chunks: queue.Queue[tuple[bytes, list[float], float]
                            | None] = queue.Queue()
        stop_event = threading.Event()
        errors: list[Exception] = []

        all_sound_values: list[float] = []
        last_audio_data: bytes | None = None
        last_sample_time = 0.0

        text_replaced = self._replace_text_for_speak(text)

        def _producer() -> None:
            try:
                for chunk in self._voice_generator.generate_sequential(text_replaced):
                    if stop_event.is_set():
                        break
                    chunks.put(chunk)
            except Exception as exc:
                errors.append(exc)
                stop_event.set()
            finally:
                chunks.put(None)

        def _consumer() -> None:
            nonlocal last_audio_data, last_sample_time
            try:
                while True:
                    item = chunks.get()
                    if item is None:
                        break

                    audio_data, sound_values, sample_time = item

                    # 文ごとの口パクデータを追加（必要なら遅延を挿入）
                    self.enqueue_sound(
                        sound_values, sample_time)

                    if getattr(self, '_voice_output_stop_flag', False):
                        stop_event.set()
                        break

                    played = self._audio_player.play(audio_data)
                    if not played:
                        raise RuntimeError('audio playback failed')

                    last_audio_data = audio_data
                    last_sample_time = sample_time
                    all_sound_values.extend(sound_values)
            except Exception as exc:
                errors.append(exc)
                stop_event.set()

        producer_thread = threading.Thread(target=_producer, daemon=True)
        consumer_thread = threading.Thread(target=_consumer, daemon=True)
        producer_thread.start()
        consumer_thread.start()
        producer_thread.join()
        consumer_thread.join()

        if errors:
            raise errors[0]

        if last_audio_data is None:
            raise ValueError('text is empty')

        return last_audio_data, all_sound_values, last_sample_time

    def enqueue_sound(
        self,
        sound_values: list[float],
        sample_time: float,
    ) -> None:
        """音量データをキューに追加する。
        """
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

    def set_voice_output_stop_flag(self, flag: bool) -> None:
        """外部から音声出力停止フラグを設定する。

        Args:
            flag: True にすると現在再生中の音声を停止させる方向へ動作する。
        """
        flag = bool(flag)
        # When requesting stop, clear pending visualizer sound queue
        # and attempt to stop currently playing audio immediately.
        if flag:
            self._voice_output_stop_flag = True
            # clear queued sound_values
            with self._sound_queue_lock:
                self._sound_queue.clear()

            self._audio_player.stop()

            # reset the flag after stopping
            self._voice_output_stop_flag = False
        else:
            self._voice_output_stop_flag = False

    def _replace_text_for_speak(
        self,
        text: str
    ) -> str:
        for target, replacement in TEXT_FOR_SPEAK_REPLACEMENTS.items():
            text = text.replace(target, replacement)
        return text
