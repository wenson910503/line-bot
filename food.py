import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, ImageSendMessage, TextSendMessage
from google.cloud import vision

# ========== [API 金鑰與憑證設定區段] ==========

# 設定 LINE BOT 金鑰
LINE_CHANNEL_ACCESS_TOKEN = 'i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'e95d4cac941b6109c3379f5cb7a7c46c'

# 設定 Google Vision API 憑證（這是你下載的 JSON 檔案路徑）
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "AIzaSyCij1x89o3PQHpKlMF0XnGbzTsjYTWap9g"

# ========== [Flask 與 LINE BOT 設定區段] ==========

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化 Google Vision API 用戶端
client = vision.ImageAnnotatorClient()

# ========== [圖片辨識與食譜查詢功能區段] ==========

# 使用 Vision API 辨識圖片中的食物
def recognize_food(image_url):
    response = requests.get(image_url)
    image_content = response.content

    image = vision.Image(content=image_content)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    if labels:
        food_name = labels[0].description
        return food_name
    else:
        return None

# 查找指定食物的製作過程
def get_recipe(food_name):
    recipes = {
        "pizza": "1. 準備麵團\n2. 加入番茄醬和起司\n3. 放進烤箱烤約15分鐘",
        "burger": "1. 準備漢堡餅乾\n2. 煎牛肉餡餅\n3. 組合：麵包 + 牛肉餡 + 生菜 + 番茄"
    }
    return recipes.get(food_name.lower(), "找不到此食物的製作過程，請嘗試其他食物。")

# ========== [LINE Webhook 路由區段] ==========

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 當使用者上傳圖片時，識別食物並回覆製作方式
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image_data = b''.join(chunk for chunk in message_content.iter_content(1024))

    image = vision.Image(content=image_data)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    if labels:
        food_name = labels[0].description
        recipe = get_recipe(food_name)
        reply = f"您上傳的食物是：{food_name}\n製作過程：\n{recipe}"
    else:
        reply = "無法識別圖片中的食物，請再試一次。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# ========== [主程式啟動點] ==========

if __name__ == "__main__":
    app.run(debug=True)
