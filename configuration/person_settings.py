from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# person settings
MATERIAL_NAME = "れいむ"
MOUSE_DELAY_TIME = 0.4

# aquestalk settings
SAMPLE_INTERVAL = 0.1  # seconds
VOICE_SCALE_FACTOR = 1.5
SERVER_EXE = Path(__file__).resolve().parents[1] / "aquestalk-server.exe"
AQUESTALK_URL = "http://localhost:8080"
