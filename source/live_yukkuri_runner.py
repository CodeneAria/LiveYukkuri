from __future__ import annotations

import sys
import os
import threading
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from flask import Flask, render_template, send_from_directory, request, jsonify

from source.voice.voice_manager import VoiceManager

from configuration.communication_settings import (
    HOST_NAME,
    OUTBOUND_PORT,
    VISUALIZER_PORT
)

BASE_DIRECTORY = str(Path(__file__).resolve().parents[1])


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
                 visualizer_port: int = VISUALIZER_PORT,
                 outbound_port: int = OUTBOUND_PORT) -> None:
        self._host = host
        self._visualizer_port = visualizer_port
        self._outbound_port = outbound_port

        self._image_dir = os.path.join(BASE_DIRECTORY, 'material', 'れいむ')

        # コア機能
        self._voice_manager = VoiceManager()

        # Visualizer Flask app
        templates_path = os.path.join(BASE_DIRECTORY, 'source', 'templates')
        self.visualizer_app = Flask(__name__, template_folder=templates_path)

        # Outbound Flask app
        self.outbound_app = Flask(__name__ + '_outbound')

        self._register_visualizer_routes()
        self._register_outbound_routes()

    # ------------------------------------------------------------------
    # Visualizer server routes
    # ------------------------------------------------------------------

    def _register_visualizer_routes(self) -> None:
        app = self.visualizer_app
        vm = self._voice_manager
        image_dir = self._image_dir

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/images/<path:folder>/<path:filename>')
        def serve_image(folder, filename):
            image_path = os.path.join(image_dir, folder)
            return send_from_directory(image_path, filename)

        @app.route('/sound_queue', methods=['GET'])
        def get_sound_queue():
            data = vm.dequeue_sound()
            if data is not None:
                return jsonify({'status': 'ok', 'data': data})
            return jsonify({'status': 'empty'})

    # ------------------------------------------------------------------
    # Outbound server routes
    # ------------------------------------------------------------------

    def _register_outbound_routes(self) -> None:
        app = self.outbound_app
        vm = self._voice_manager

        @app.route('/speak', methods=['POST'])
        def speak():
            data = request.get_json(force=True)
            text = data.get('text', '')
            if not text:
                return jsonify({'status': 'error', 'message': 'text is required'}), 400

            try:
                _, sound_values, sample_time = vm.speak(text)
            except Exception as exc:
                return jsonify({'status': 'error', 'message': str(exc)}), 500

            return jsonify({
                'status': 'ok',
                'samples': len(sound_values),
                'sample_time': sample_time,
            })

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, debug: bool = False) -> None:
        """outbound サーバーをバックグラウンドスレッドで起動後、visualizer を起動する。"""

        def run_outbound():
            self.outbound_app.run(
                host=self._host, port=self._outbound_port, debug=False)

        outbound_thread = threading.Thread(target=run_outbound, daemon=True)
        outbound_thread.start()

        def _print_open_message():
            print(
                f'\nOpen: http://127.0.0.1:{self._visualizer_port}', flush=True)

        timer = threading.Timer(1.0, _print_open_message)
        timer.daemon = True
        timer.start()

        self.visualizer_app.run(
            debug=debug,
            host=self._host,
            port=self._visualizer_port,
            use_reloader=False,
        )
