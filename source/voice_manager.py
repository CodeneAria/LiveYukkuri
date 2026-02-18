from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
import threading
from pathlib import Path
from flask import Flask, render_template, send_from_directory, request, jsonify


class VoiceManager:
    """Flask-based visualizer and mouth-animation queue manager.

    This encapsulates the Flask app, image serving and a simple sound queue
    used by the frontend (`templates/index.html`).
    """

    def __init__(self, host: str = "0.0.0.0", visualizer_port: int = 50201):
        self.host = host
        self.port = visualizer_port

        # Project base dir (parent of `source/`)
        self.BASE_DIR = str(Path(__file__).resolve().parents[1])
        # Image directory containing `れいむ` folder
        self.IMAGE_DIR = os.path.join(self.BASE_DIR, 'material', 'れいむ')

        # Flask app; point template_folder to project templates directory
        templates_path = os.path.join(self.BASE_DIR, 'templates')
        self.app = Flask(__name__, template_folder=templates_path)

        # Queue and lock for mouth animation data
        self._sound_queue: list[dict] = []
        self._sound_queue_lock = threading.Lock()

        # Register routes
        self._register_routes()

    def _register_routes(self) -> None:
        app = self.app

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

    def run(self, debug: bool = True) -> None:
        self.app.run(debug=debug, host=self.host, port=self.port)
