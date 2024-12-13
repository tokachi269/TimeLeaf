from flask import Flask, render_template, jsonify
from flask_cors import CORS
from controller.controller import controller_bp

app = Flask(__name__, static_folder='../frontend/dist/static', template_folder='../frontend/dist')
CORS(app, resources={r"/*": {"origins": ["https://192.168.1.2:8081", "https://www.timeleaff.com"], "allow_headers": ["Authorization", "Content-Type"]}})
app.register_blueprint(controller_bp)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    # 特定のAPIパスをチェック
    if path.startswith('api/'):
        return "This API endpoint does not exist.", 404  # APIのエンドポイントが存在しない場合

    print("Index route accessed")
    return render_template('index.html')  # Vueアプリのエントリーポイント

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('sample.crt', 'sample.key'))