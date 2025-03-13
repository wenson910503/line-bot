import os
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
        reply_message = "🍽 熱門餐廳推薦 🍽\n\n"

        for index, r in enumerate(restaurants):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            business_status = r.get("business_status", "無營業資訊")
            place_id = r.get("place_id", None)

            reply_message += f"🔹 **{index+1}. {name}**\n"
            reply_message += f"⭐ 評分：{rating}/5.0\n"
            reply_message += f"📍 地址：{address}\n"
            reply_message += f"🕒 營業狀況：{business_status}\n\n"

            # 使用 Place ID 取得詳細資訊（評論和圖片）
            if place_id:
                detailed_info = get_restaurant_details(place_id)
                reviews = detailed_info.get("reviews", [])
                photos = detailed_info.get("photos", [])
                
                # 收集前五條評論
                review_text = "\n".join([f"⭐ {review['author_name']}：{review['text']}" for review in reviews[:5]]) if reviews else "無評論"
                
                # 收集餐廳的第一張圖片
                photo_url = None
                if photos:
                    photo_reference = photos[0].get("photo_reference")
                    if photo_reference:
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"

                # 如果有評論，加入評論
                if review_text:
                    reply_message += f"📝 評論：\n{review_text}\n\n"
                
                # 如果有圖片，加入圖片
                if photo_url:
                    reply_message += f"📸 圖片：{photo_url}\n"

        return reply_message.strip()

    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取餐廳資訊：{e}"

# 📍 取得餐廳詳細資訊 (包括評論和圖片)
def get_restaurant_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("result", {})
    except requests.exceptions.RequestException as e:
        return {}

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
