import time
from flask import Flask, redirect, request, session, jsonify, url_for , send_file, Response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask_cors import cross_origin
from dotenv import load_dotenv
from flask import Blueprint
from slack_sdk.oauth import AuthorizeUrlGenerator
from io import BytesIO
import requests
import os
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

# 環境変数を読み込み
load_dotenv()

app = Flask(__name__)
controller_bp = Blueprint('controller', __name__, url_prefix='/api')

SLACK_CLIENT_ID = "REMOVED"
SLACK_CLIENT_SECRET = "REMOVED"
SLACK_BOT_TOKEN = "REMOVED"

# 初期化
authorize_url_generator = AuthorizeUrlGenerator(
    client_id=SLACK_CLIENT_ID,
    scopes=["channels:history", "channels:read"]
)
user_cache = []
last_update = 0
CACHE_DURATION = 86400  # 1日（秒単位）

def update_user_cache():
    url = "https://slack.com/api/users.list"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    }
    global user_cache
    global last_update
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            user_cache = res["members"]
            last_update = time.time()
            print(user_cache)
        else:
            print(res)
    else:
        return jsonify({"error": "Failed to fetch update_user_cache"}), 500

# 起動時にキャッシュを更新
update_user_cache()

@controller_bp.route("/v1/getAccessToken", methods=['GET'])
def oauth_redirect():
    code = request.args.get("code")
    token = request.headers.get('authorization')
    print( request.headers.get('referer'))
    if not (code or token):
        print("Both code and token are empty")
        return jsonify({"error": "Both code and token are empty"}), 400

    authTest = auth_test(token)
    if authTest:
        return jsonify({"token":token.replace("Bearer ", ""),
                        "team":authTest.get("team")}), 200
    
    url = "https://slack.com/api/oauth.v2.access"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    referer = request.headers.get('referer')

    if referer:
        parsed_referer = urlparse(referer)
        scheme = parsed_referer.scheme
        domain = parsed_referer.netloc
        full_url = f"{scheme}://{domain}"
        print(f"Referer URL: {full_url}")

    params={
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri":full_url
    }
    print(request.headers.get('referer'))
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        res = response.json() 
        print(res)
        if res.get("ok"):
            print(res.get("authed_user").get('access_token'))
            user_cache[res.get("authed_user").get('id')]
            # user_cache からユーザー名を取得。存在しない場合は user_id のまま
            user_info = ""
            for user in user_cache:
                if user["id"] == res.get("authed_user").get('id'):
                    user_info = user["profile"]
                    break
            print(user_info)

            return jsonify({"token":res.get("authed_user").get('access_token'),
                            "scope":res.get("authed_user").get('scope'),
                            "id":user_info.get('id'),
                            "name":user_info.get('display_name'),
                            "team":res.get("team").get('name')}), 200
        else:
            return jsonify(response.json()), 400
    else:
        return jsonify({"error": "Failed to fetch messages"}), 500

def auth_test(token):
    url = "https://slack.com/api/auth.test"

    headers = {
        "Authorization": f"{token}",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json() 
        if res.get("ok"):
            return res
    return

@controller_bp.route('/v1/slack/messages', methods=['GET'])
def get_slack_messages():
    token = request.headers.get('authorization')
    cursor = request.args.get("cursor")
    query = request.args.get("query")

    url = "https://slack.com/api/search.messages"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "query": query,
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
            return jsonify(res)
    else:
        return jsonify({"error": "Failed to fetch messages"}), 500

@controller_bp.route('/v1/slack/messages/replies', methods=['GET'])
def get_slack_message_replies():
    token = request.headers.get('authorization')
    channel = request.args.get("channel")
    ts = request.args.get("ts")
    global user_cache
    global last_update
    # キャッシュが古い場合は更新
    if time.time() - last_update > CACHE_DURATION:
        update_user_cache()

    url = "https://slack.com/api/conversations.replies"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "channel": channel,
      #    "cursor": cursor,
        "ts": ts,
      #  "limit": 100,
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            for message in res.get("messages"):
               if message.get("reactions"):
                for reaction in message.get("reactions"):
                        updated_users = []
                        for user_id in reaction.get("users", []):
                            # user_cache からユーザー名を取得。存在しない場合は user_id のまま
                            user_name = ""
                            for user in user_cache:
                                if user["id"] == user_id:
                                    user_name = user["profile"].get("display_name", user["profile"].get("real_name", "Unknown User"))
                                    break

                            updated_users.append({"id":user_id, "name":user_name })
                        # users リストを更新
                        reaction["users"] = updated_users
            messages = jsonify(res.get("messages"))
           # messages.headers['Cache-Control'] = 'public, max-age=60'  # 1 分間キャッシュ
            return messages
        else:
            return jsonify(res)
    else:
        return jsonify({"error": "Failed to fetch messages"}), 500

@controller_bp.route('/v1/slack/timesChannels', methods=['GET'])
def get_slack_times_channels():
    token = request.headers.get('authorization')
    
    url = "https://slack.com/api/conversations.list"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "limit": 200,
        "types":"public_channel"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            timesChannels = [
                channel
                for channel in res.get("channels", [])
                if isinstance(channel, dict) and channel.get("name", "").startswith('times')
            ]
            timesFollowed = [
                channel
                for channel in timesChannels
                if channel.get('is_member')
            ]
            return jsonify({"channels":timesChannels,"followed_channels":timesFollowed})
        else:
            return jsonify(res)
    else:
        return jsonify({"error": "Failed to fetch timesChannels"}), 500


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
            emojis = jsonify(res.get("emoji"))
            emojis.headers['Cache-Control'] = 'public, max-age=1800'
            return emojis
        else:
            return jsonify(res)
    else:
        return jsonify({"error": "Failed to fetch emoji"}), 500
    
@controller_bp.route('/v1/slack/users/profile', methods=['GET'])
def get_slack_users_profile():
    token = request.headers.get('authorization')
    user = request.args.get("user")

    url = "https://slack.com/api/users.profile.get"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "user": user
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            profile = jsonify(res.get("profile"))
            profile.headers['Cache-Control'] = 'public, max-age=1800'  # 30 分間キャッシュ
            return profile
        else:
            return jsonify(res)
    else:
        return jsonify({"error": "Failed to fetch profile"}), 500

@controller_bp.route('/v1/slack/reactions/insert', methods=['POST'])
def get_slack_reactions_insert():
    token = request.headers.get('authorization')
    channelId = request.args.get("channelId")
    name = request.args.get("name")
    ts = request.args.get("ts")

    url = "https://slack.com/api/reactions.add"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "channel": channelId,
        "name": name,
        "timestamp": ts,
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            return jsonify(), 200
        else:
            return jsonify(res), 400
    else:
        return jsonify({"error": "Failed to set reaction"}), 500

@controller_bp.route('/v1/slack/reactions/delete', methods=['POST'])
def get_slack_reactions_delete():
    token = request.headers.get('authorization')
    channelId = request.args.get("channelId")
    name = request.args.get("name")
    ts = request.args.get("ts")

    url = "https://slack.com/api/reactions.remove"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "channel": channelId,
        "name": name,
        "timestamp": ts,
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            return jsonify(), 200
        else:
            return jsonify(res), 400
    else:
        return jsonify({"error": "Failed to delete reaction"}), 500
 
@controller_bp.route('/v1/slack/image', methods=['GET'])
def get_image():
    token = request.headers.get('authorization')
    url = request.args.get("url")
    type = request.args.get("type")
    if not (url or type):
        return jsonify({"error": "Image URL is required"}), 400
    
    headers = {
        "Authorization": token,
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        if(content_type != type) :
            return jsonify({"error": "Failed to fetch image. return " + content_type}), 500
        flask_response = Response(response.content)
        flask_response.headers['Content-Type'] = type
        flask_response.headers['Content-Length'] = str(len(response.content))
        flask_response.headers['Cache-Control'] = 'public, max-age=60'  # 1 分間キャッシュ

        return flask_response
    else:
        return jsonify({"error": "Failed to fetch image"}), 500