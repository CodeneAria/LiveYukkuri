from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import Iterator

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parents[3]))

from source.voice.speaker.aquestalk_generator import AquesTalkGenerator, SAMPLE_INTERVAL


class VoiceGenerator:
    """AquesTalkGenerator を利用してテキストから音声データと音量値を生成するクラス。"""

    def __init__(self) -> None:
        self._generator = AquesTalkGenerator()

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """句点・疑問符・感嘆符で文を分割し、区切り記号を保持して返す。"""
        if not text:
            return []

        normalized = text.strip()
        if not normalized:
            return []

        parts = re.findall(r'[^。？！!?]+[。？！!?]?', normalized)
        return [part.strip() for part in parts if part.strip()]

    def generate_sequential(self, text: str, interval: float = SAMPLE_INTERVAL
                            ) -> Iterator[tuple[bytes, list[float], float]]:
        """テキストを文単位に分割し、順番に音声 WAV データと音量値を生成する。"""
        sentences = self._split_sentences(text)
        for sentence in sentences:
            audio_data = self._generator.generate_audio(sentence)
            sound_values = self._generator.extract_sound_values(
                audio_data, interval)
            scaled = self._generator.scale(sound_values)
            yield audio_data, scaled, interval

    def generate(self, text: str, interval: float = SAMPLE_INTERVAL
                 ) -> tuple[bytes, list[float], float]:
        """テキストから音声 WAV データおよび正規化済み音量値を生成する。

        Args:
            text: 読み上げテキスト
            interval: 音量サンプリング間隔(秒)

        Returns:
            (audio_bytes, scaled_sound_values, sample_time)
        """
        all_sound_values: list[float] = []
        last_audio_data: bytes | None = None

        for audio_data, scaled, sample_time in self.generate_sequential(text, interval):
            last_audio_data = audio_data
            all_sound_values.extend(scaled)

        if last_audio_data is None:
            raise ValueError('text is empty')

        return last_audio_data, all_sound_values, sample_time
