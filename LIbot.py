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

def get_reviews(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if "result" in data and "reviews" in data["result"]:
            reviews = data["result"]["reviews"]
            for review in reviews:
                if 'zh' in review['language']:
                    return review['text']
            return reviews[0]['text'] if reviews else None
    except:
        return None

def search_restaurants(location):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{location} 餐廳",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if "results" not in data or not data["results"]:
            return ["😢 沒有找到相關餐廳，請換個關鍵字試試看！"]

        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]
        messages = ["🍽 **熱門餐廳推薦** 🍽\n"]
        for index, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            business_status = r.get("business_status", "無營業資訊")
            place_id = r.get("place_id", "")
            photo_url = None
            if "photos" in r:
                photo_reference = r["photos"][0]["photo_reference"]
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"

            reviews = get_reviews(place_id)
            message = f"🏆 **{index}. {name}**\n⭐ 評分：{rating}/5.0\n📍 地址：{address}\n🕒 營業狀況：{business_status}\n"
            if reviews:
                message += f"💬 最佳評論：{reviews}\n"
            message += f"🚗 [Google Maps 導航](https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')})\n"
            messages.append(message.strip())
            if photo_url:
                messages.append(photo_url)

        return messages
    except requests.exceptions.RequestException as e:
        return [f"❌ 無法獲取餐廳資訊：{e}"]

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    if len(user_input) >= 2:
        messages = search_restaurants(user_input)
    else:
        messages = ["❌ 請輸入 **城市名稱 + 美食類型**（例如：「臺北燒肉」）"]

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
    app.run()
