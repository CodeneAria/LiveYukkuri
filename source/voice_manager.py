from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
import threading
from pathlib import Path
from flask import Flask, render_template, send_from_directory, request, jsonify
import httpx

from source.speaker.aquestalk_generator import AquesTalkGenerator

HOST_NAME = "0.0.0.0"
OUTBOUND_PORT = 50200
VISUALIZER_PORT = 50201


class VoiceManager:
    """Flask-based visualizer and mouth-animation queue manager.

    Runs two servers:
    - Visualizer server (VISUALIZER_PORT): serves the HTML frontend and manages the
      mouth-animation sound queue consumed by `templates/index.html`.
    - Outbound server (OUTBOUND_PORT): receives text via REST API, synthesises speech
      with AquesTalkGenerator, and forwards the resulting sound values to the
      visualizer server.
    """

    def __init__(self, host: str = HOST_NAME,
                 visualizer_port: int = VISUALIZER_PORT,
                 outbound_port: int = OUTBOUND_PORT) -> None:
        self.host = host
        self.visualizer_port = visualizer_port
        self.outbound_port = outbound_port

        # Project base dir (parent of `source/`)
        self.BASE_DIR = str(Path(__file__).resolve().parents[1])
        # Image directory containing `れいむ` folder
        self.IMAGE_DIR = os.path.join(self.BASE_DIR, 'material', 'れいむ')

        # Visualizer Flask app; point template_folder to project templates directory
        templates_path = os.path.join(self.BASE_DIR, 'templates')
        self.visualizer_app = Flask(__name__, template_folder=templates_path)

        # Outbound Flask app for external speech requests
        self.outbound_app = Flask(__name__ + '_outbound')

        # Queue and lock for mouth animation data
        self._sound_queue: list[dict] = []
        self._sound_queue_lock = threading.Lock()

        # AquesTalk speech synthesiser (starts aquestalk-server.exe)
        self._generator = AquesTalkGenerator()

        # Register routes for both apps
        self._register_visualizer_routes()
        self._register_outbound_routes()

    # ------------------------------------------------------------------
    # Visualizer server routes
    # ------------------------------------------------------------------

    def _register_visualizer_routes(self) -> None:
        app = self.visualizer_app

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/images/<path:folder>/<path:filename>')
        def serve_image(folder, filename):
            image_path = os.path.join(self.IMAGE_DIR, folder)
            return send_from_directory(image_path, filename)

        @app.route('/play_sound', methods=['POST'])
        def play_sound():
            data = request.get_json(force=True)
            sound_values = data.get('sound_values', [])
            sample_time = data.get('sample_time', 0.1)
            with self._sound_queue_lock:
                self._sound_queue.append({'sound_values': sound_values,
                                          'sample_time': sample_time})
            return jsonify({'status': 'ok'})

        @app.route('/sound_queue', methods=['GET'])
        def get_sound_queue():
            with self._sound_queue_lock:
                if self._sound_queue:
                    data = self._sound_queue.pop(0)
                    return jsonify({'status': 'ok', 'data': data})
            return jsonify({'status': 'empty'})

    # ------------------------------------------------------------------
    # Outbound server routes
    # ------------------------------------------------------------------

    def _register_outbound_routes(self) -> None:
        app = self.outbound_app

        @app.route('/speak', methods=['POST'])
        def speak():
            data = request.get_json(force=True)
            text = data.get('text', '')
            if not text:
                return jsonify({'status': 'error', 'message': 'text is required'}), 400

            try:
                sound_values, sample_time = self._generator.speak(text)
            except Exception as exc:
                return jsonify({'status': 'error', 'message': str(exc)}), 500

            # Forward normalized sound values to the visualizer server
            visualizer_url = f'http://127.0.0.1:{self.visualizer_port}/play_sound'
            try:
                httpx.post(
                    visualizer_url,
                    json={'sound_values': sound_values,
                          'sample_time': sample_time},
                    timeout=5.0,
                )
            except Exception as exc:
                return jsonify({'status': 'error',
                                'message': f'Failed to send to visualizer: {exc}'}), 500

            return jsonify({'status': 'ok',
                            'samples': len(sound_values),
                            'sample_time': sample_time})

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, debug: bool = False) -> None:
        """Start the outbound server in a background thread, then run the visualizer."""

        def run_outbound():
            self.outbound_app.run(
                host=self.host, port=self.outbound_port, debug=False)

        outbound_thread = threading.Thread(target=run_outbound, daemon=True)
        outbound_thread.start()

        def _print_open_message():
            print(
                f'\nOpen: http://127.0.0.1:{self.visualizer_port}', flush=True)

        timer = threading.Timer(1.0, _print_open_message)
        timer.daemon = True
        timer.start()

        self.visualizer_app.run(debug=debug, host=self.host, port=self.visualizer_port,
                                use_reloader=False)
