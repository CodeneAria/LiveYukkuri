from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import threading

app = Flask(__name__)

# 画像ディレクトリのパスを設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'material/れいむ')

# 口アニメーション用キュー
_sound_queue: list[dict] = []
_sound_queue_lock = threading.Lock()


@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')


@app.route('/images/<path:folder>/<path:filename>')
def serve_image(folder, filename):
    """れいむフォルダ内の画像を配信"""
    image_path = os.path.join(IMAGE_DIR, folder)
    return send_from_directory(image_path, filename)


@app.route('/play_sound', methods=['POST'])
def play_sound():
    """正規化済みsound_valuesとsample_timeを受け取り、キューに追加する"""
    data = request.get_json(force=True)
    sound_values = data.get('sound_values', [])
    sample_time = data.get('sample_time', 0.1)
    with _sound_queue_lock:
        _sound_queue.append({'sound_values': sound_values,
                            'sample_time': sample_time})
    return jsonify({'status': 'ok'})


@app.route('/sound_queue', methods=['GET'])
def get_sound_queue():
    """キューの先頭データを取り出して返す（なければ empty）"""
    with _sound_queue_lock:
        if _sound_queue:
            data = _sound_queue.pop(0)
            return jsonify({'status': 'ok', 'data': data})
    return jsonify({'status': 'empty'})


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
