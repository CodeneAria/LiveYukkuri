from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from flask import Flask, render_template, send_from_directory, Response, stream_with_context

from configuration.communication_settings import (
    HOST_NAME,
    VISUALIZER_PORT
)


class VisualizeManager:
    def __init__(self, base_directory: str, material_name: str) -> None:
        self._base_directory = base_directory
        self._image_directory = os.path.join(
            base_directory, 'material', material_name)

        templates_path = os.path.join(
            base_directory, 'source', 'visualizer', 'templates')
        self.app = Flask(__name__, template_folder=templates_path)

        # queue for delivering sound events to SSE endpoint
        self._visualizer_sound_queue: list[dict] = []
        self._visualizer_sound_queue_lock = threading.Lock()
        self._visualizer_sound_queue_condition = threading.Condition(
            self._visualizer_sound_queue_lock)

        self._register_routes()

    def _register_routes(self) -> None:
        app = self.app
        image_dir = self._image_directory

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/images/<path:folder>/<path:filename>')
        def serve_image(folder, filename):
            image_path = os.path.join(image_dir, folder)
            return send_from_directory(image_path, filename)

        @app.route('/sound_events', methods=['GET'])
        def sound_events():
            @stream_with_context
            def generate():
                while True:
                    data = self.wait_and_dequeue_visualizer_sound(timeout=15.0)
                    if data is None:
                        yield ': keep-alive\n\n'
                        continue

                    payload = json.dumps(data, ensure_ascii=False)
                    yield f'data: {payload}\n\n'

            response = Response(generate(), mimetype='text/event-stream')
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['X-Accel-Buffering'] = 'no'
            return response

    def enqueue_visualizer_sound(self, data: dict) -> None:
        with self._visualizer_sound_queue_condition:
            self._visualizer_sound_queue.append(data)
            self._visualizer_sound_queue_condition.notify()

    def wait_and_dequeue_visualizer_sound(self, timeout: float) -> dict | None:
        with self._visualizer_sound_queue_condition:
            if not self._visualizer_sound_queue:
                self._visualizer_sound_queue_condition.wait(timeout=timeout)

            if self._visualizer_sound_queue:
                return self._visualizer_sound_queue.pop(0)

        return None

    def print_open_message(self) -> None:
        print(
            f'\nOpen: http://127.0.0.1:{VISUALIZER_PORT}', flush=True)

    def run(
        self,
        debug: bool = False,
        use_reloader: bool = False
    ) -> None:
        self.app.run(debug=debug, host=HOST_NAME, port=VISUALIZER_PORT,
                     use_reloader=use_reloader)
