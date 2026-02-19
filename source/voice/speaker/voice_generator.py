from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parents[3]))

from source.voice.speaker.aquestalk_generator import AquesTalkGenerator, SAMPLE_INTERVAL


class VoiceGenerator:
    """AquesTalkGenerator を利用してテキストから音声データと音量値を生成するクラス。"""

    def __init__(self) -> None:
        self._generator = AquesTalkGenerator()

    def generate(self, text: str, interval: float = SAMPLE_INTERVAL
                 ) -> tuple[bytes, list[float], float]:
        """テキストから音声 WAV データおよび正規化済み音量値を生成する。

        Args:
            text: 読み上げテキスト
            interval: 音量サンプリング間隔(秒)

        Returns:
            (audio_bytes, scaled_sound_values, sample_time)
        """
        audio_data = self._generator.generate_audio(text)
        sound_values = self._generator.extract_sound_values(
            audio_data, interval)
        scaled = self._generator.scale(sound_values)
        return audio_data, scaled, interval
