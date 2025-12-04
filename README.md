
TimeLeaf は、Slack メッセージをタイムライン形式で表示し、リアクションやスレッド管理を直感的に行える Web アプリケーションです。  

---

## 📂 プロジェクト構成

```
.
├── backend/                # バックエンド (Flask)
│   ├── controller/         # API コントローラー
│   ├── main.py             # アプリケーションエントリーポイント
│   ├── requirements.txt    # Python 依存関係
│   └── wsgi.py             # WSGI サーバー設定
├── frontend/               # フロントエンド (Vue.js)
│   ├── src/                # ソースコード
│   ├── public/             # 静的ファイル
│   └── vue.config.js       # Vue.js 設定ファイル
└── README.md               # このファイル
```

---

## ⚙️ 必要条件

- **Node.js**: 16.x
- **Python**: 3.10 以上
- **Flask**: バックエンドフレームワーク
- **Vue CLI**: フロントエンドビルドツール

---

## 🛠️ セットアップ

### 1️⃣ リポジトリのクローン

```bash
git clone https://github.com/your-repo/TimeLeaf.git
cd TimeLeaf
```

### 2️⃣ バックエンドのセットアップ

```bash
cd backend
pip install -r requirements.txt
```

`.env` ファイルを作成し、以下を記載してください:

```
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret
SLACK_BOT_TOKEN=your-bot-token
```

### 3️⃣ フロントエンドのセットアップ

```bash
cd ../frontend
npm install
```

### 4️⃣ 開発サーバーの起動

#### バックエンド

```bash
cd backend
python main.py
```

#### フロントエンド

```bash
cd frontend
npm run serve
```

ブラウザで以下の URL にアクセスしてください:

```
https://localhost:8080
```

---

## 📦 ビルド

フロントエンドを本番環境用にビルドするには、以下を実行します:

```bash
cd frontend
npm run build
```

ビルドされたファイルは `frontend/dist` ディレクトリに出力されます。

---

## 📜 ライセンス

このプロジェクトは [MIT ライセンス](LICENSE) のもとで公開されています。

---
