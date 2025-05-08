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
GOOGLE_MAPS_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'


# 📍 文字查詢餐廳
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

        if not data.get("results"):
            return ["😢 沒有找到相關餐廳，請換個關鍵字試試看！"]

        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]
        messages = ["🍽 **熱門餐廳推薦** 🍽\n"]
        for idx, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            status = r.get("business_status", "無營業資訊")
            place_id = r.get("place_id", "")

            photo_url = None
            if "photos" in r:
                photo_ref = r["photos"][0]["photo_reference"]
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref}&key={GOOGLE_PLACES_API_KEY}"

            reviews = get_reviews(place_id)

            msg = f"🏆 **{idx}. {name}**\n⭐ 評分：{rating}/5.0\n📍 地址：{address}\n🕒 營業狀況：{status}\n"
            if reviews:
                msg += f"💬 評論：{reviews}\n"
            msg += f"🚗 [導航](https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')})\n"
            messages.append(msg.strip())
            if photo_url:
                messages.append(photo_url)
        return messages

    except requests.exceptions.RequestException as e:
        return [f"❌ 無法獲取餐廳資訊：{e}"]

# 📍 位置查詢附近餐廳
def search_nearby_restaurants(lat, lng):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 1000,
        "type": "restaurant",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            return ["😢 附近找不到餐廳，換個地點試試吧！"]

        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]
        messages = ["📍 **你附近的熱門餐廳** 🍽\n"]
        for idx, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("vicinity", "無地址資訊")
            place_id = r.get("place_id", "")

            photo_url = None
            if "photos" in r:
                photo_ref = r["photos"][0]["photo_reference"]
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref}&key={GOOGLE_PLACES_API_KEY}"

            reviews = get_reviews(place_id)

            msg = f"🏅 **{idx}. {name}**\n⭐ 評分：{rating}\n📍 地址：{address}\n"
            if reviews:
                msg += f"💬 評論：{reviews}\n"
            msg += f"🚗 [導航](https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')})\n"
            messages.append(msg.strip())
            if photo_url:
                messages.append(photo_url)
        return messages

    except requests.exceptions.RequestException as e:
        return [f"❌ 查詢失敗：{e}"]

# 🗣 查詢評論
def get_reviews(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        reviews = data.get("result", {}).get("reviews", [])
        for r in reviews:
            if 'zh' in r.get("language", ""):
                return r.get("text")
        return reviews[0]["text"] if reviews else None
    except requests.exceptions.RequestException:
        return None

# 🚣 查詢路線
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
        response.raise_for_status()
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

# 📤 共用訊息發送函數
def send_messages(event, messages):
    first_message_sent = False
    for msg in messages:
        if msg.startswith("http"):  # 圖片 URL
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

# 📨 處理文字訊息
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
        messages = [reply_text]

    elif len(user_input) >= 2:
        messages = search_restaurants(user_input)
    else:
        messages = ["❌ 請輸入 **城市名稱 + 美食類型**（例如：「台北燒肉」），或使用 `路線 出發地 目的地` 查詢路線。"]

    send_messages(event, messages)

# 📍 處理位置訊息
@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    lat = event.message.latitude
    lng = event.message.longitude
    print(f"📍 使用者位置：{lat}, {lng}")
    messages = search_nearby_restaurants(lat, lng)
    send_messages(event, messages)

# 📬 LINE Webhook Endpoint
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 🚀 啟動 Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
