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

# 📍 Google Places API 查詢函數（顯示最多 3 間餐廳，包含評論與圖片）
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

        if "results" not in data or not data["results"]:
            return "😢 沒有找到相關餐廳，請換個關鍵字試試看！"

        # 按評分排序（由高到低），只顯示 3 間
        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]

        reply_message = "🍽 **熱門餐廳推薦（依評分排序）** 🍽\n\n"
        images = []

        for index, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            business_status = r.get("business_status", "無營業資訊")
            place_id = r.get("place_id", "")

            # 獲取評論與圖片
            reviews = get_reviews(place_id)
            photo_url = get_photos(place_id)

            reply_message += f"🏆 **{index}. {name}**\n"
            reply_message += f"⭐ 評分：{rating}/5.0\n"
            reply_message += f"📍 地址：{address}\n"
            reply_message += f"🕒 營業狀況：{business_status}\n"
            if reviews:
                reply_message += f"💬 最佳評論：{reviews}\n"
            if photo_url:
                images.append(photo_url)  # 儲存圖片 URL

            reply_message += "\n"

        return reply_message.strip(), images  # 回傳文字內容 + 圖片列表

    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取餐廳資訊：{e}", []

# 🔄 獲取餐廳評論的函數
def get_reviews(place_id):
    review_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW"
    }

    try:
        response = requests.get(review_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "result" in data and "reviews" in data["result"]:
            reviews = data["result"]["reviews"]
            for review in reviews:
                if 'zh' in review['language']:  # 優先選擇中文評論
                    return review['text']
            return reviews[0]['text'] if reviews else None
        return None
    except requests.exceptions.RequestException as e:
        return None

# 🔄 獲取餐廳照片的函數
def get_photos(place_id):
    photo_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
    }

    try:
        response = requests.get(photo_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "result" in data and "photos" in data["result"]:
            photos = data["result"]["photos"]
            if photos:
                photo_reference = photos[0]["photo_reference"]
                return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"
        return None
    except requests.exceptions.RequestException as e:
        return None

# 🔄 分段訊息的函數
def split_message(message, limit=5000):
    messages = []
    while len(message) > limit:
        split_pos = message.rfind("\n", 0, limit)
        if split_pos == -1:
            split_pos = limit
        messages.append(message[:split_pos])
        message = message[split_pos:].strip()
    messages.append(message)
    return messages

# 🔄 處理使用者發送的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()

    if len(user_input) >= 2:  # 限制最小字數
        result, images = search_restaurants(user_input)
    else:
        result = "❌ 請輸入 **城市名稱 + 美食類型**（例如：「台北燒肉」）。"
        images = []

    # 分段發送訊息
    message_parts = split_message(result)

    # 第一則訊息使用 reply_message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message_parts[0]))

    # 其餘文字訊息使用 push_message
    if len(message_parts) > 1:
        for part in message_parts[1:]:
            line_bot_api.push_message(event.source.user_id, TextSendMessage(text=part))

    # 發送圖片（如果有）
    for img_url in images:
        line_bot_api.push_message(event.source.user_id, ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))

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
