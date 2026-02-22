from __future__ import annotations

import sys
import unittest
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parents[1]))

from configuration.communication_settings import OUTBOUND_PORT

SPEAK_URL = f"http://127.0.0.1:{OUTBOUND_PORT}/speak"
# TEXT = "私は博麗霊夢です。よろしくお願いします。"
TEXT = "この湖こんなに広かったかしら？　霧で見通しが悪くて困ったわ。もしかして私って方向音痴？"


class TestLiveYukkuriResponse(unittest.TestCase):
    """run.py でサーバーを起動した状態で実行するテスト。

    キャラクターの口パクアニメーション・音声出力をユーザーが目視・聴覚で確認する。
    """

    def test_speak(self) -> None:
        """テキストを OUTBOUND_PORT へ送信する。"""
        response = httpx.post(SPEAK_URL, json={"text": TEXT}, timeout=60.0)
        print(f"\nstatus: {response.status_code}")
        print(f"body  : {response.text}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
