import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, TextSendMessage, ImageSendMessage
)

app = Flask(__name__)

# 🚀 填入你的 LINE Bot API Key
line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')

# 🚀 填入你的 Google Places API Key
GOOGLE_PLACES_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'

def search_nearby_restaurants(lat, lng):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 1000,  # 搜尋半徑 1000 公尺（1 公里）
        "type": "restaurant",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "results" not in data or not data["results"]:
            return ["😢 附近沒有找到餐廳，請換個地點試試看！"]

        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]
        messages = ["🍽 **附近餐廳推薦** 🍽\n"]

        for index, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("vicinity", "無地址資訊")
            place_id = r.get("place_id", "")
            photo_url = get_photos(place_id)

            message = f"🏆 **{index}. {name}**\n"
            message += f"⭐ 評分：{rating}/5.0\n"
            message += f"📍 地址：{address}\n"
            
            messages.append(message.strip())
            if photo_url:
                messages.append(photo_url)

        return messages
    except requests.exceptions.RequestException as e:
        return [f"❌ 無法獲取餐廳資訊：{e}"]

def get_photos(place_id):
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
    }

    try:
        response = requests.get(details_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "result" in data and "photos" in data["result"]:
            photos = data["result"]["photos"]
            if photos:
                photo_reference = photos[0]["photo_reference"]
                return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"
        return None
    except requests.exceptions.RequestException:
        return None

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    lat = event.message.latitude
    lng = event.message.longitude
    
    messages = search_nearby_restaurants(lat, lng)
    
    first_message_sent = False
    for msg in messages:
        if msg.startswith("http"):
            line_bot_api.push_message(
                event.source.user_id,
                ImageSendMessage(original_content_url=msg, preview_image_url=msg)
            )
        else:
            text_message = TextSendMessage(text=msg)
            if not first_message_sent:
                line_bot_api.reply_message(event.reply_token, text_message)
                first_message_sent = True
            else:
                line_bot_api.push_message(event.source.user_id, text_message)

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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
