from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# 画像ディレクトリのパスを設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'れいむ')

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')

@app.route('/images/<path:folder>/<path:filename>')
def serve_image(folder, filename):
    """れいむフォルダ内の画像を配信"""
    image_path = os.path.join(IMAGE_DIR, folder)
    return send_from_directory(image_path, filename)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
