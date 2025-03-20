import os
import requests
from flask import Flask, request, abort
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

app = Flask(__name__)

# 🚀 填入你的 LINE Bot API Key
line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')

# 🚀 填入你的 Google Places API Key
GOOGLE_PLACES_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'

# 📍 Google Places API 查詢函數（顯示最多 3 間餐廳）
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

        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]
        reply_message = "🍽 **熱門餐廳推薦（依評分排序）** 🍽\n\n"

        for index, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            reply_message += f"🏆 **{index}. {name}**\n"
            reply_message += f"⭐ 評分：{rating}/5.0\n"
            reply_message += f"📍 地址：{address}\n\n"

        return reply_message.strip()
    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取餐廳資訊：{e}"

# 📸 文字轉換成圖片函數
def text_to_image(text):
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # 確保伺服器有字體
    font = ImageFont.truetype(font_path, 40)

    # 設定圖片寬度與行高
    max_width = 800
    line_height = 60

    # 文字換行處理
    lines = []
    words = text.split("\n")
    for word in words:
        lines.append(word)

    # 計算圖片高度
    img_height = line_height * (len(lines) + 2)

    # 創建圖片
    img = Image.new("RGB", (max_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # 繪製文字
    y = 20
    for line in lines:
        draw.text((20, y), line, fill="black", font=font)
        y += line_height

    # 儲存圖片到記憶體
    img_io = BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)
    return img_io

# 🔄 處理使用者發送的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()

    if len(user_input) >= 2:
        result = search_restaurants(user_input)
    else:
        result = "❌ 請輸入 **城市名稱 + 美食類型**（例如：「台北燒肉」）。"

    # 如果訊息超過 500 個字，轉換成圖片發送
    if len(result) > 500:
        img_io = text_to_image(result)
        image_url = "你的_圖片_上傳_API"  # 這裡需要上傳圖片到雲端存儲，回傳 URL
        line_bot_api.reply_message(
            event.reply_token, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        )
    else:
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
