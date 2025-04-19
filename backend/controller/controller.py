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

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# 初期化
authorize_url_generator = AuthorizeUrlGenerator(
    client_id=SLACK_CLIENT_ID,
    scopes=["channels:history", "channels:read"]
)
user_cache = []
last_user_update = 0
USER_CACHE_DURATION = 86400  # 1日（秒単位）

reaction_cache = []
last_reaction_update = 0
REACTION_CACHE_DURATION = 1800  # 30分（秒単位）

def update_user_cache():
    url = "https://slack.com/api/users.list"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    }
    global user_cache
    global last_user_update
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            user_cache = res["members"]
            last_user_update = time.time()
        else:
            print(res)
    else:
        return jsonify({"error": "Failed to fetch update_user_cache"}), 500

# 起動時にキャッシュを更新
update_user_cache()

def update_reaction_cache():
    url = "https://slack.com/api/emoji.list"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    }
    global reaction_cache
    global last_user_update
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            reaction_array = []
            for key, value in res.get("emoji").items():
                reaction_object = {
                    "id": key,
                    "name": key,
                    "colons": f":{key}:",
                    "text": "",
                    "emoticons": [],
                    "short_names": [key],
                    "keywords": [key],
                    "custom": True,
                    "imageUrl": value
                }
                reaction_array.append(reaction_object)

            reaction_cache = reaction_array
            last_user_update = time.time()
        else:
            print(res)
    else:
        return jsonify({"error": "Failed to fetch update_user_cache"}), 500

# 起動時にキャッシュを更新
update_reaction_cache()

@controller_bp.route("/v1/getAccessToken", methods=['GET'])
def oauth_redirect():
    code = request.args.get("code")
    token = request.headers.get('authorization')
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

    params={
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri":full_url
    }
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        res = response.json() 
        if res.get("ok"):
            print(res.get("authed_user").get('access_token'))
            # user_cache からユーザー名を取得。存在しない場合は user_id のまま
            user_info = ""
            for user in user_cache:
                if user["id"] == res.get("authed_user").get('id'):
                    user_info = user["profile"]
                    break
            return jsonify({"token":res.get("authed_user").get('access_token'),
                            "scope":res.get("authed_user").get('scope'),
                            "id":res.get("authed_user").get('id'),
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
        "limit": 30,
        "sort": "timestamp"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json()
        if res.get("ok"):
            # "messages"キーが存在し、"matches"キーが存在するか確認
            messages_data = res.get("messages", {})
            matches = messages_data.get("matches", [])

            # 再帰的にelementsを処理する関数
            def process_elements(elements):
                for element in elements:
                    if element.get("type") == "user":
                        user_id = element.get("user_id")
                        user_name = user_id  # デフォルトは user_id
                        for user in user_cache:
                            if user["id"] == user_id:
                                user_name = user["profile"].get("display_name", user["profile"].get("real_name", user_id))
                                break
                        element["user_name"] = user_name  # user_name を追加
                    elif "elements" in element:
                        process_elements(element["elements"])  # 再帰的に処理

            # 各メッセージのblocksを処理
            for message in matches:
                blocks = message.get("blocks", [])
                for block in blocks:
                    if "elements" in block:
                        process_elements(block["elements"])

            # messages_data に上書きして返す
            messages_data["matches"] = matches
            return jsonify(messages_data), 200
        else:
            return jsonify(res), 400
    else:
        return jsonify({"error": "Failed to fetch messages"}), 500

@controller_bp.route('/v1/slack/messages/replies', methods=['GET'])
def get_slack_message_replies():
    token = request.headers.get('authorization')
    channel = request.args.get("channel")
    ts = request.args.get("ts")
    global user_cache
    global last_user_update

    # キャッシュが古い場合は更新
    if time.time() - last_user_update > USER_CACHE_DURATION:
        update_user_cache()

    url = "https://slack.com/api/conversations.replies"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "channel": channel,
        "ts": ts,
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json()
        if res.get("ok"):
            messages = res.get("messages", [])

            # 再帰的に elements を処理する関数
            def process_elements(elements):
                for element in elements:
                    if element.get("type") == "user":
                        user_id = element.get("user_id")
                        user_name = user_id  # デフォルトは user_id
                        for user in user_cache:
                            if user["id"] == user_id:
                                user_name = user["profile"].get("display_name", user["profile"].get("real_name", user_id))
                                break
                        element["user_name"] = user_name  # user_name を追加
                    elif "elements" in element:
                        process_elements(element["elements"])  # 再帰的に処理

            # 各メッセージの blocks を処理
            for message in messages:
                blocks = message.get("blocks", [])
                for block in blocks:
                    if "elements" in block:
                        process_elements(block["elements"])

                # ユーザー情報を追加
                postUser = message.get("user")
                user_real_name = ""
                user_name = ""
                user_img_src = ""
                for user in user_cache:
                    if user["id"] == postUser:
                        user_real_name = user["profile"].get("display_name", user["profile"].get("real_name", "Unknown User"))
                        user_name = user["profile"].get("real_name", "Unknown User")
                        user_img_src = user["profile"].get("image_72")
                        break

                # メッセージにユーザー名と和名を追加
                message["user_real_name"] = user_real_name
                message["user_name"] = user_name
                message["user_image"] = user_img_src

                # reactions のユーザー情報を更新
                if message.get("reactions"):
                    for reaction in message.get("reactions"):
                        updated_users = []
                        for user_id in reaction.get("users", []):
                            # user_cache からユーザー名を取得。存在しない場合は user_id のまま
                            user_real_name = ""
                            for user in user_cache:
                                if user["id"] == user_id:
                                    user_real_name = user["profile"].get("display_name", user["profile"].get("real_name", "Unknown User"))
                                    break
                            updated_users.append({"id": user_id, "name": user_real_name})
                        # users リストを更新
                        reaction["users"] = updated_users

            # メッセージを返す
            return jsonify(messages), 200
        else:
            return jsonify(res), 400
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
        "limit": 500,
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
def get_slack_reactions_v1():
    token = request.headers.get('authorization')

    url = "https://slack.com/api/emoji.list"
    headers = {
        "Authorization": token,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            emojis = jsonify(res.get("emoji"))
            emojis.headers['Cache-Control'] = 'public, max-age=3600' # 60 分間キャッシュ
            return emojis
        else:
            return jsonify(res)
    else:
        return jsonify({"error": "Failed to fetch emoji"}), 500
    
@controller_bp.route('/v2/slack/emojis', methods=['GET'])
def get_slack_reactions_v2():
    token = request.headers.get('authorization')
    global reaction_cache
    global last_reaction_update
    # キャッシュが古い場合は更新
    if time.time() - last_reaction_update > REACTION_CACHE_DURATION:
        update_reaction_cache()

    if reaction_cache:
        res = jsonify(reaction_cache)
        res.headers['Cache-Control'] = 'public, max-age=3600' # 60 分間キャッシュ
        return res
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
            profile.headers['Cache-Control'] = 'public, max-age=3600'  # 60 分間キャッシュ
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
    response = requests.post(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            return jsonify({"message": "Reaction added successfully"}), 200
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
    response = requests.post(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            return jsonify({"message": "Reaction delete successfully"}), 200
        else:
            return jsonify(res), 400
    else:
        return jsonify({"error": "Failed to delete reaction"}), 500
 
@controller_bp.route('/v1/slack/messages/reply', methods=['POST'])
def get_slack_messages_reply():
    token = request.headers.get('authorization')
    channelId = request.args.get("channelId")
    text = request.args.get("text")
    thread_ts = request.args.get("thread_ts")

    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"{token}",
    }
    params = {
        "channel": channelId,
        "text": text,
        "thread_ts": thread_ts,
    }
    response = requests.post(url, headers=headers, params=params)
    if response.status_code == 200:
        res = response.json() 
        if response.json().get("ok"):
            message = res.get("message")

            postUser = message.get("user")
            user_real_name = ""
            for user in user_cache:
                if user["id"] == postUser:
                    user_real_name = user["profile"].get("display_name", user["profile"].get("real_name", "Unknown User"))
                    user_name = user["profile"].get("real_name", "Unknown User")
                    user_img_src = user["profile"].get("image_72")
                    break
            # メッセージにユーザー名と和名を追加
            message["user_real_name"] = user_real_name
            message["user_name"] = user_name
            message["user_image"] = user_img_src
            if message.get("reactions"):
                for reaction in message.get("reactions"):
                        updated_users = []
                        for user_id in reaction.get("users", []):
                            # user_cache からユーザー名を取得。存在しない場合は user_id のまま
                            user_real_name = ""
                            for user in user_cache:
                                if user["id"] == user_id:
                                    user_real_name = user["profile"].get("display_name", user["profile"].get("real_name", "Unknown User"))
                                    break

                            updated_users.append({"id":user_id, "name":user_real_name })
                        # users リストを更新
                        reaction["users"] = updated_users
            res = jsonify(message)
            res.headers['Cache-Control'] = 'public, max-age=60'  # 1 分間キャッシュ
            return res, 200
        else:
            return jsonify(res), 400
    else:
        return jsonify({"error": "Failed to set reaction"}), 500

@controller_bp.route('/v1/slack/image', methods=['GET'])
def get_image():
    token = request.headers.get('authorization')
    if not token:
        token = f"Bearer {request.cookies.get('token')}"
    url = request.args.get("url")
    type = request.args.get("type")
    if not (url or type):
        return jsonify({"error": "Image URL is required"}), 400
    
    headers = {
        "Authorization": f"{token}",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        if(content_type != type) :
            return jsonify({"error": "Failed to fetch image. return " + content_type}), 500
        flask_response = Response(response.content)
        flask_response.headers['Content-Type'] = type
        flask_response.headers['Content-Length'] = str(len(response.content))
        flask_response.headers['Cache-Control'] = 'public, max-age=3600'  # 60 分間キャッシュ

        return flask_response
    else:
        return jsonify({"error": "Failed to fetch image"}), 500