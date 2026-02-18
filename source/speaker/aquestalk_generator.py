from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2]))

import atexit
import io
import subprocess
import time
import wave
from pathlib import Path

import httpx
from openai import OpenAI

SAMPLE_INTERVAL = 0.1  # seconds
SERVER_EXE = Path(__file__).resolve().parents[2] / "aquestalk-server.exe"
AQUESTALK_URL = "http://localhost:8080"


class AquesTalkGenerator:
    """Manages the AquesTalk server process and generates speech audio from text."""

    def __init__(self) -> None:
        self._server_process = subprocess.Popen(
            [str(SERVER_EXE)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        atexit.register(self._shutdown_server)
        self._wait_for_server()
        self._client = OpenAI(api_key="a", base_url=f"{AQUESTALK_URL}/v1")

    def _shutdown_server(self) -> None:
        if self._server_process.poll() is None:
            self._server_process.terminate()
            try:
                self._server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._server_process.kill()

    def _wait_for_server(self) -> None:
        for _ in range(20):
            try:
                httpx.get(AQUESTALK_URL, timeout=0.5)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("aquestalk-server が起動しませんでした")

    def generate_audio(self, text: str) -> bytes:
        """Generate WAV audio bytes from text via AquesTalk server."""
        with self._client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="f1",
            input=text,
        ) as response:
            return response.read()

    def extract_sound_values(self, audio_data: bytes, interval: float = SAMPLE_INTERVAL) -> list[float]:
        """Extract per-interval volume samples from WAV bytes."""
        audio_stream = io.BytesIO(audio_data)
        with wave.open(audio_stream, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            play_time = n_frames / framerate

            volumes = []
            for i in range(int(play_time / interval) + 1):
                time_sec = i * interval
                target_frame = int(time_sec * framerate)
                if target_frame >= n_frames:
                    break
                wf.setpos(target_frame)
                frame_bytes = wf.readframes(1)

                channel_values = []
                for c in range(n_channels):
                    sample_chunk = frame_bytes[c *
                                               sampwidth: (c + 1) * sampwidth]
                    if not sample_chunk:
                        continue
                    if sampwidth == 1:
                        val = int.from_bytes(
                            sample_chunk, 'little', signed=False) - 128
                    else:
                        val = int.from_bytes(
                            sample_chunk, 'little', signed=True)
                    channel_values.append(abs(val))

                volume = sum(channel_values) / \
                    n_channels if channel_values else 0
                volumes.append(volume)

        return volumes

    def normalize(self, values: list[float]) -> list[float]:
        """Normalize values to 0–1 range by dividing by the maximum."""
        max_val = max(values) if values else 0
        if max_val == 0:
            return [0.0] * len(values)
        return [v / max_val for v in values]

    def speak(self, text: str, interval: float = SAMPLE_INTERVAL) -> tuple[list[float], float]:
        """Generate audio from text and return (normalized_sound_values, sample_time)."""
        audio_data = self.generate_audio(text)
        sound_values = self.extract_sound_values(audio_data, interval)
        normalized = self.normalize(sound_values)
        return normalized, interval
