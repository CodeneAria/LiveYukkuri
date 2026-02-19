"""VoiceManager の単体テスト。

テスト内容:
1. VoiceManager.speak() に文字列を渡す
2. 音声 WAV バイト列が返ること
3. 正規化済み音量値リストが返ること（長さ > 0、全値 0.0〜1.0）
4. sample_time が正値であること
5. dequeue_sound() でキューから音量データを取得できること

注意: aquestalk-server.exe が起動している必要があります。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from source.voice.voice_manager import VoiceManager


class TestVoiceManager(unittest.TestCase):
    """VoiceManager の speak() および dequeue_sound() のテスト。"""

    _vm: VoiceManager

    @classmethod
    def setUpClass(cls) -> None:
        cls._vm = VoiceManager()

    # ------------------------------------------------------------------
    # テストケース
    # ------------------------------------------------------------------

    def test_speak_returns_audio_bytes(self) -> None:
        """speak() が非空の WAV バイト列を返すこと。"""
        audio_data, _, _ = self._vm.speak("テスト")
        self.assertIsInstance(audio_data, bytes)
        self.assertGreater(len(audio_data), 0, "audio_bytes が空です")

    def test_speak_returns_sample_count(self) -> None:
        """speak() が長さ > 0 の sound_values を返すこと。"""
        _, sound_values, _ = self._vm.speak("こんにちは")
        self.assertIsInstance(sound_values, list)
        self.assertGreater(len(sound_values), 0, "sound_values が空です")

    def test_speak_returns_sample_time(self) -> None:
        """speak() が sample_time > 0 を返すこと。"""
        _, _, sample_time = self._vm.speak("サンプルタイム確認")
        self.assertGreater(
            sample_time, 0, f"sample_time が 0 以下: {sample_time}")

    def test_sound_values_scaled(self) -> None:
        """音量値がすべて 0.0〜1.0 の範囲に正規化されていること。"""
        _, sound_values, _ = self._vm.speak("正規化テスト")
        self.assertGreater(len(sound_values), 0)
        for v in sound_values:
            self.assertGreaterEqual(v, 0.0, f"負の値が含まれています: {v}")
            self.assertLessEqual(v, 1.0, f"1.0 超の値が含まれています: {v}")

    def test_sound_queue_enqueued_after_speak(self) -> None:
        """speak() 後、dequeue_sound() で音量データを取得できること。"""
        # 既存のキューをクリア
        while self._vm.dequeue_sound() is not None:
            pass

        self._vm.speak("音量キューテスト")

        data = self._vm.dequeue_sound()
        self.assertIsNotNone(data, "dequeue_sound() が None を返しました")
        sound_values = data.get("sound_values", [])  # type: ignore[union-attr]
        self.assertGreater(len(sound_values), 0, "sound_values が空です")

    def test_dequeue_empty_returns_none(self) -> None:
        """キューが空のとき dequeue_sound() は None を返すこと。"""
        # キューをクリア
        while self._vm.dequeue_sound() is not None:
            pass
        result = self._vm.dequeue_sound()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
