from flask import Flask, render_template, jsonify
from flask_cors import CORS  # CORSをインポート
from controller.controller import get_slack_messages  # コントローラーをインポート
from controller.controller import controller_bp  # コントローラーをインポート

app = Flask(__name__, static_folder='../frontend/dist/static', template_folder='../frontend/dist')
CORS(app, supports_credentials=True)
app.register_blueprint(controller_bp)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
        # 特定のAPIパスをチェック
    if path.startswith('api/'):
        return "This API endpoint does not exist.", 404  # APIのエンドポイントが存在しない場合

    print("Index route accessed")  # デバッグメッセージ
    return render_template('index.html')  # Vueアプリのエントリーポイント
    