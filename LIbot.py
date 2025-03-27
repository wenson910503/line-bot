import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage

app = Flask(__name__)

# 🚀 填入你的 LINE Bot API Key
line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')

# 🚀 填入你的 Google API Key
GOOGLE_PLACES_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'
GOOGLE_MAPS_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'

# 📍 Google Places API 查詢函數（搜尋餐廳）
def search_restaurants(query, location=None):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{query} 餐廳",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW",
    }
    if location:
        params["location"] = location

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "results" not in data or not data["results"]:
            return ["😢 沒有找到相關餐廳，請換個關鍵字試試看！"]

        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]

        messages = ["🍽 **熱門餐廳推薦** 🍽\n"]
        for index, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            place_id = r.get("place_id", "")

            # 獲取照片
            photo_url = None
            if "photos" in r:
                photo_reference = r["photos"][0]["photo_reference"]
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"

            message = f"🏆 **{index}. {name}**\n"
            message += f"⭐ 評分：{rating}/5.0\n"
            message += f"📍 地址：{address}\n"
            message += f"🚗 [Google Maps 導航](https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')})\n"

            messages.append(message.strip())
            if photo_url:
                messages.append(photo_url)

        return messages

    except requests.exceptions.RequestException as e:
        return [f"❌ 無法獲取餐廳資訊：{e}"]

# 📨 處理 LINE 訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    if len(user_input) >= 2:
        messages = search_restaurants(user_input)
    else:
        messages = ["❌ 請輸入 **城市名稱 + 美食類型**（例如：「台北燒肉」）。"]

    for msg in messages:
        if msg.startswith("http"):
            line_bot_api.push_message(event.source.user_id, ImageSendMessage(original_content_url=msg, preview_image_url=msg))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))

# 📨 處理地理位置訊息
@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    location = f"{latitude},{longitude}"
    messages = search_restaurants("餐廳", location)

    for msg in messages:
        if msg.startswith("http"):
            line_bot_api.push_message(event.source.user_id, ImageSendMessage(original_content_url=msg, preview_image_url=msg))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))

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
