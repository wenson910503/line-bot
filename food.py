
import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from google.cloud import vision  # Google Vision API 用於圖像識別

app = Flask(__name__)

line_bot_api = LineBotApi('YOUR_LINE_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')

client = vision.ImageAnnotatorClient()

# 上傳圖片並識別食物
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

# 查找食物的製作過程
def get_recipe(food_name):
    recipes = {
        "pizza": "1. 準備麵團\n2. 加入番茄醬和起司\n3. 放進烤箱烤約15分鐘",
        "burger": "1. 準備漢堡餅乾\n2. 煎牛肉餡餅\n3. 組合：麵包 + 牛肉餡 + 生菜 + 番茄"
    }
    return recipes.get(food_name.lower(), "找不到此食物的製作過程，請嘗試其他食物。")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image_url = message_content.content_url
    food_name = recognize_food(image_url)
    if food_name:
        recipe = get_recipe(food_name)
        reply_message = TextSendMessage(text=f"您上傳的食物是：{food_name}\n製作過程：\n{recipe}")
    else:
        reply_message = TextSendMessage(text="無法識別圖片中的食物，請再試一次。")
    line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == "__main__":
    app.run(debug=True)
