import time
from flask import Flask, redirect, request, session, jsonify, url_for
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask_cors import CORS  # CORSをインポート
from dotenv import load_dotenv
from flask import Blueprint
from slack_sdk.oauth import AuthorizeUrlGenerator

import requests
import os
import os

# 環境変数を読み込み
load_dotenv()

app = Flask(__name__)
controller_bp = Blueprint('controller', __name__, url_prefix='/api')

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

# 初期化
authorize_url_generator = AuthorizeUrlGenerator(
    client_id=SLACK_CLIENT_ID,
    scopes=["channels:history", "channels:read"]
)

@controller_bp.route("/v1/getAccessToken", methods=['GET'])
def oauth_redirect():
    # 認可コードを取得し、トークンをリクエスト
    code = request.args.get("code")
    response = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data={
            "client_id": SLACK_CLIENT_ID,
            "client_secret": SLACK_CLIENT_SECRET,
            "code": code,
        },
    )
    if response.status_code == 200:
        res = response.json() 
        if res.get("ok"):
            return jsonify(res.get("access_token")), 200
        else:
            return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch messages"}), 500

@controller_bp.route('/v1/slack/messages', methods=['POST'])
def get_slack_messages():
    token = request.get_json().get("token")
    cursor = request.get_json().get("cursor")

    url = "https://slack.com/api/search.messages"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    params = {
        "query": "times",
        "cursor": cursor,
        "limit": 20,
        "sort":"timestamp"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            return jsonify(res.get("messages"))
        else:
            return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch messages"}), 500

@controller_bp.route('/v1/slack/emojis', methods=['GET'])
def get_slack_reactions():
    token = request.headers.get('authorization')
    print(token)
    url = "https://slack.com/api/emoji.list"
    headers = {
        "Authorization": token,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            return jsonify(res.get("emoji"))
        else:
            return jsonify(res)
    else:
        return jsonify({"error": "Failed to fetch messages"}), 500