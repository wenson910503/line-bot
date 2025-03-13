# -*- coding: utf-8 -*-
import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 🚀 填入你的 LINE Bot API Key
line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')

# 🚀 填入你的 Google Places API Key
GOOGLE_PLACES_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'

# 📍 Google Places API 查詢函數（加入餐廳排名及評論、圖片）
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

        # 按評分排序（由高到低）
        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:5]
        
        reply_message = "🍽 **熱門餐廳推薦（依評分排序）** 🍽\n\n"

        for index, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            business_status = r.get("business_status", "無營業資訊")
            place_id = r.get("place_id", "")

            # 查詢每間餐廳的評論
            reviews = get_reviews(place_id)  # 獲取餐廳評論
            photos = get_photos(place_id)  # 獲取餐廳照片

            reply_message += f"🏆 **{index}. {name}**\n"
            reply_message += f"⭐ 評分：{rating}/5.0\n"
            reply_message += f"📍 地址：{address}\n"
            reply_message += f"🕒 營業狀況：{business_status}\n"
            if reviews:
                reply_message += f"💬 最佳評論：{reviews}\n"
            if photos:
                reply_message += f"📸 相關照片：{photos}\n"
            reply_message += "\n"

        return reply_message.strip()

    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取餐廳資訊：{e}"

# 🔄 獲取餐廳評論的函數
def get_reviews(place_id):
    review_url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "placeid": place_id,
        "key": GOOGLE_PLACES_API_KEY,
    }
    
    try:
        response = requests.get(review_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "result" in data and "reviews" in data["result"]:
            reviews = data["result"]["reviews"]
            if reviews:
                # 取第一條評論作為最佳評論
                best_review = reviews[0]["text"]
                return best_review
        return None
    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取評論：{e}"

# 🔄 獲取餐廳照片的函數
def get_photos(place_id):
    photo_url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "placeid": place_id,
        "key": GOOGLE_PLACES_API_KEY,
    }

    try:
        response = requests.get(photo_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "result" in data and "photos" in data["result"]:
            photos = data["result"]["photos"]
            if photos:
                # 使用第一張照片的 photo_reference
                photo_reference = photos[0]["photo_reference"]
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"
                return photo_url
        return None
    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取照片：{e}"

# 🔄 分段訊息的函數
def split_message(message, limit=5000):
    # 分段長訊息
    messages = []
    while len(message) > limit:
        # 找到最後一個適合分割的位置（此處以 "\n" 為分割點）
        split_pos = message.rfind("\n", 0, limit)
        if split_pos == -1:  # 如果沒有找到分割點，直接從 limit 處分割
            split_pos = limit
        messages.append(message[:split_pos])
        message = message[split_pos:].strip()
    messages.append(message)
    return messages

# 🔄 處理使用者發送的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()

    if len(user_input) >= 2:  # 限制最小字數，避免無效查詢
        result = search_restaurants(user_input)
    else:
        result = "❌ 請輸入 **城市名稱 + 美食類型**（例如：「台北燒肉」）。"

    # 分段發送訊息
    message_parts = split_message(result)
    for part in message_parts:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=part))

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
