
import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from google.cloud import vision

# ====== 設定憑證路徑（Render Secret File 的路徑）======
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vision-api-key.json"

# ====== LINE BOT 設定 ======
LINE_CHANNEL_ACCESS_TOKEN = 'i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'e95d4cac941b6109c3379f5cb7a7c46c'

# === 初始化 ===
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = vision.ImageAnnotatorClient()

# === 食物辨識函式 ===
def recognize_food(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.label_detection(image=image)
    labels = response.label_annotations
    if labels:
        return labels[0].description
    return None

# === 模擬查詢食譜函式 ===
def get_recipe(food_name):
    recipes = {
        "pizza": "1. 準備麵團\n2. 加入番茄醬和起司\n3. 放進烤箱烤約15分鐘",
        "hamburger": "1. 準備漢堡麵包\n2. 煎牛肉餅\n3. 組合：麵包 + 牛肉餅 + 生菜 + 番茄"
    }
    return recipes.get(food_name.lower(), "找不到此食物的製作過程，請嘗試其他食物。")

# === Webhook 路由 ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# === 處理圖片訊息 ===
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image_data = b''.join(chunk for chunk in message_content.iter_content(1024))

    food_name = recognize_food(image_data)
    if food_name:
        recipe = get_recipe(food_name)
        reply = f"您上傳的食物是：{food_name}\n製作過程：\n{recipe}"
    else:
        reply = "無法識別圖片中的食物，請再試一次。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# === 本地端啟動（Render 會自動指定 PORT） ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
