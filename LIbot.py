# -*- coding: utf-8 -*-
import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationMessage

app = Flask(__name__)

# 🚀 LINE Bot API Key
line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')

# 🔑 Google API Keys
GOOGLE_PLACES_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'
ROUTE_OPTIMIZATION_API_KEY = 'AIzaSyBrE625SLt1CFnVtm6mrOlws5gvQaXthHs'

# 📍 Google Places 查詢餐廳

def search_restaurants(location_query):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{location_query} 餐廳",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW",
    }
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    if "results" not in data or not data["results"]:
        return [], "😢 沒有找到相關餐廳，請換個關鍵字試試看！"

    restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]
    results = []
    for r in restaurants:
        results.append({
            "name": r.get("name", "未知餐廳"),
            "rating": r.get("rating", "無評分"),
            "address": r.get("formatted_address", "無地址資訊"),
            "location": r["geometry"]["location"],
            "place_id": r.get("place_id")
        })
    return results, ""

# ⭐ 取得最佳評論

def get_best_review(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "zh-TW"
    }
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    if "result" in data and "reviews" in data["result"]:
        for review in data["result"]["reviews"]:
            if 'zh' in review['language']:
                return review['text']
        return data["result"]["reviews"][0]['text']
    return ""

# 🗺️ 取得最佳路線 (Route Optimization API)

def get_optimized_route(start_location, destinations):
    url = f"https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": ROUTE_OPTIMIZATION_API_KEY,
        "X-Goog-FieldMask": "routes.optimizedIntermediateWaypointIndex,routes.summary,routes.polyline"
    }

    waypoints = [{"location": {"latLng": dest}} for dest in destinations]
    payload = {
        "origin": {"location": {"latLng": start_location}},
        "destination": {"location": {"latLng": destinations[-1]}},
        "intermediates": waypoints[:-1],
        "travelMode": "DRIVE"
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    data = response.json()

    if "routes" in data:
        route = data["routes"][0]
        polyline = route["polyline"]["encodedPolyline"]
        summary = route["summary"]
        map_url = f"https://www.google.com/maps/dir/?api=1&origin={start_location['latitude']},{start_location['longitude']}&destination={destinations[-1]['latitude']},{destinations[-1]['longitude']}&travelmode=driving"
        return summary, polyline, map_url

    return None, None, None

# 📩 分段訊息

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

# 📌 訊息處理：文字查詢
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_input = event.message.text.strip()

    if len(user_input) < 2:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請輸入城市+美食類型（例如：台北燒肉）或傳送位置。"))
        return

    restaurants, error = search_restaurants(user_input)

    if error:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error))
        return

    message = "🍽 **熱門餐廳推薦** 🍽\n\n"
    destinations = []
    for i, r in enumerate(restaurants, start=1):
        review = get_best_review(r["place_id"])
        message += f"🏆 {i}. {r['name']}\n⭐ 評分：{r['rating']}\n📍 地址：{r['address']}\n💬 評論：{review}\n\n"
        destinations.append(r["location"])

    # 通知使用者傳送位置以取得最佳路線
    message += "📌 請傳送您的目前位置，幫您規劃最佳路線。"
    message_parts = split_message(message)
    for part in message_parts:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=part))

# 📌 訊息處理：位置訊息
@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user_location = {
        "latitude": event.message.latitude,
        "longitude": event.message.longitude
    }

    # 先從 user profile 取得最後查詢記錄
    # 👉 如果要完整功能，可以幫你加上 Redis/Mongo 記錄最後查詢地點

    # 範例 (假資料示範)：
    location_query = "台北燒肉"
    restaurants, _ = search_restaurants(location_query)
    if not restaurants:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 查無餐廳資訊，請先輸入美食類型。"))
        return

    destinations = [r["location"] for r in restaurants]
    summary, polyline, map_url = get_optimized_route(user_location, destinations)

    if not summary:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 路線規劃失敗。"))
        return

    reply = f"🚗 **最佳路線規劃完成** 🚗\n\n總距離：約 {summary['distanceMeters']/1000:.1f} 公里\n預估時間：約 {summary['duration']}\n\n👉 [點我打開導航地圖]({map_url})"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 📌 Webhook 設定
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 🔥 啟動
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


