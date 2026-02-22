from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
import threading
from flask import Flask, request, jsonify

from source.voice.voice_manager import VoiceManager
from source.visualizer.visualize_manager import VisualizeManager

from configuration.communication_settings import (
    HOST_NAME,
    OUTBOUND_PORT,
)
from configuration.person_settings import (
    MATERIAL_NAME,
    MOUSE_DELAY_TIME
)

BASE_DIRECTORY = str(Path(__file__).resolve().parents[1])
SOUND_QUEUE_CHECK_INTERVAL = 0.05


class LiveYukkuriRunner:
    """アプリケーション全体を管理するトップレベルクラス。

    - VoiceManager: 音声生成・再生・音量キュー管理
    - Visualizer server (VISUALIZER_PORT): フロントエンド HTML の配信と
      mouth-animation 用音量キューの提供
    - Outbound server (OUTBOUND_PORT): 外部からテキストを受け取り
      VoiceManager 経由で音声合成・再生を行う
    """

    def __init__(self,
                 host: str = HOST_NAME,
                 outbound_port: int = OUTBOUND_PORT) -> None:
        self._host = host
        self._outbound_port = outbound_port

        self._image_directory = os.path.join(
            BASE_DIRECTORY, 'material', MATERIAL_NAME)

        # コア機能
        self._voice_manager = VoiceManager()

        # VoiceManager のキュー監視スレッド制御
        self._sound_forwarder_stop_event = threading.Event()
        self._sound_forwarder_thread: threading.Thread | None = None
        # Visualizer manager
        self.visualize_manager = VisualizeManager(
            BASE_DIRECTORY)

        # Outbound Flask app
        self.outbound_app = Flask(__name__ + '_outbound')

        self._register_outbound_routes()

    # ------------------------------------------------------------------
    # Visualizer server routes
    # ------------------------------------------------------------------

    def _start_sound_forwarder(self) -> None:
        if self._sound_forwarder_thread is not None:
            return

        def _forward_loop() -> None:
            while not self._sound_forwarder_stop_event.is_set():
                data = self._voice_manager.dequeue_sound()
                if data is not None:
                    delay = MOUSE_DELAY_TIME

                    if delay > 0.0:
                        def _enqueue_later(d=data) -> None:
                            # Remove 'delay' key when forwarding to visualizer
                            if isinstance(d, dict) and 'delay' in d:
                                payload = {k: v for k,
                                           v in d.items() if k != 'delay'}
                            else:
                                payload = d
                            self.visualize_manager.enqueue_visualizer_sound(
                                payload)

                        timer = threading.Timer(delay, _enqueue_later)
                        timer.daemon = True
                        timer.start()
                    else:
                        if isinstance(data, dict) and 'delay' in data:
                            data = {k: v for k, v in data.items() if k !=
                                    'delay'}
                        self.visualize_manager.enqueue_visualizer_sound(data)

                self._sound_forwarder_stop_event.wait(
                    SOUND_QUEUE_CHECK_INTERVAL)

        self._sound_forwarder_thread = threading.Thread(
            target=_forward_loop,
            daemon=True,
            name='sound-forwarder',
        )
        self._sound_forwarder_thread.start()

    # ------------------------------------------------------------------
    # Outbound server routes
    # ------------------------------------------------------------------

    def _register_outbound_routes(self) -> None:
        app = self.outbound_app
        voice_manager = self._voice_manager

        @app.route('/speak', methods=['POST'])
        def speak():
            data = request.get_json(force=True)
            text = data.get('text', '')
            if not text:
                return jsonify({'status': 'error', 'message': 'text is required'}), 400

            try:
                _, sound_values, sample_time = voice_manager.speak(text)
            except Exception as exc:
                return jsonify({'status': 'error', 'message': str(exc)}), 500

            return jsonify({
                'status': 'ok',
                'samples': len(sound_values),
                'sample_time': sample_time,
            })

        @app.route('/voice_output_stop_flag', methods=['POST', 'PUT'])
        def voice_output_stop_flag():
            # Accept JSON boolean, JSON object with key, or query param
            data = None
            try:
                data = request.get_json(silent=True)
            except Exception:
                data = None

            flag = None
            if isinstance(data, bool):
                flag = data
            elif isinstance(data, dict):
                if 'voice_output_stop_flag' in data:
                    flag = bool(data.get('voice_output_stop_flag'))
                elif 'value' in data:
                    flag = bool(data.get('value'))
            # fallback to query params
            if flag is None:
                val = request.args.get('value') or request.args.get('flag')
                if val is not None:
                    v = val.lower()
                    if v in ('1', 'true', 'yes', 'on'):
                        flag = True
                    elif v in ('0', 'false', 'no', 'off'):
                        flag = False

            if flag is None:
                flag = True

            try:
                voice_manager.set_voice_output_stop_flag(flag)
            except Exception as exc:
                return jsonify({'status': 'error', 'message': str(exc)}), 500

            return jsonify({'status': 'ok', 'voice_output_stop_flag': flag})

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, debug: bool = False) -> None:
        """outbound サーバーをバックグラウンドスレッドで起動後、visualizer を起動する。"""

        self._start_sound_forwarder()

        def run_outbound():
            self.outbound_app.run(
                host=self._host, port=self._outbound_port, debug=False)

        outbound_thread = threading.Thread(target=run_outbound, daemon=True)
        outbound_thread.start()

        timer = threading.Timer(1.0, self.visualize_manager.print_open_message)
        timer.daemon = True
        timer.start()

        self.visualize_manager.run(
            debug=debug,
            use_reloader=False,
        )
