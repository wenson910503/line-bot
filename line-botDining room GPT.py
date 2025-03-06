!pip install line-bot-sdk
# -*- coding: utf-8 -*-
import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 🚀 填入你的 LINE Bot API Key

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('e95d4cac941b6109c3379f5cb7a7c46c')

line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
handler =WebhookHandler ('e95d4cac941b6109c3379f5cb7a7c46c')

# 🚀 填入你的 Google Places API Key
GOOGLE_PLACES_API_KEY = os.getenv('AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM')

# 📍 Google Places API 查詢函數
def search_restaurants(location):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{location} 餐廳",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 如果 API 沒回傳結果
        if "results" not in data or not data["results"]:
            return "😢 沒有找到相關餐廳，請換個關鍵字試試看！"

        # 取得前 5 間餐廳
        restaurants = data["results"][:5]
        reply_message = "🍽 **熱門餐廳推薦** 🍽\n\n"

        for index, r in enumerate(restaurants):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            business_status = r.get("business_status", "無營業資訊")

            reply_message += f"🔹 **{index+1}. {name}**\n"
            reply_message += f"⭐ 評分：{rating}/5.0\n"
            reply_message += f"📍 地址：{address}\n"
            reply_message += f"🕒 營業狀況：{business_status}\n\n"

        return reply_message.strip()

    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取餐廳資訊：{e}"

# 🔄 處理使用者發送的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()

    if len(user_input) >= 2:  # 限制最小字數，避免無效查詢
        result = search_restaurants(user_input)
    else:
        result = "❌ 請輸入 **城市名稱 + 美食類型**（例如：「台北燒肉」）。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

# 📌 Line Bot Webhook 設定
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 🔥 啟動 Flask 應用程式
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
