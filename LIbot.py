import os
import re
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

app = Flask(__name__)

# 🚀 填入你的 LINE Bot API Key
line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')

# 🚀 填入你的 Google Places API Key
GOOGLE_PLACES_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'
GOOGLE_MAPS_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'
def get_route(origin, destination):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": "walking",
        "language": "zh-TW",
        "key": GOOGLE_MAPS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data["status"] == "OK":
            steps = data["routes"][0]["legs"][0]["steps"]
            directions = "\n".join([
                f"{i+1}. {re.sub('<[^<]+?>', '', step['html_instructions'])}"
                for i, step in enumerate(steps)
            ])
            map_link = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=walking"
            directions += f"\n\n📍 點我直接導航：\n👉 {map_link}"
            return directions
        else:
            return "🚫 無法取得路線，請確認地點是否正確。"
    except requests.exceptions.RequestException as e:
        return f"❌ 查詢路線時發生錯誤：{e}"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    if user_input.startswith("路線 "):
        try:
            _, origin, destination = user_input.split()
            route_info = get_route(origin, destination)
            reply_text = f"🗺 **從 {origin} 到 {destination} 的建議路線**\n{route_info}"
        except:
            reply_text = "❌ 請輸入格式：**路線 出發地 目的地**"
    else:
        reply_text = "📍 請輸入格式：**路線 出發地 目的地**"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == '__main__':
    app.run()
