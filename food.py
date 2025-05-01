app = Flask(__name__)

# 從環境變數取得 LINE 憑證
line_bot_api = LineBotApi(os.getenv('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU='))
handler = WebhookHandler(os.getenv('e95d4cac941b6109c3379f5cb7a7c46c'))

# 初始化 Vision API
client = vision.ImageAnnotatorClient()

# 食物名稱辨識
def recognize_food(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    if labels:
        return labels[0].description
    else:
        return None

# 食譜查詢
def get_recipe(food_name):
    recipes = {
        "pizza": "1. 準備麵團\n2. 加入番茄醬和起司\n3. 放進烤箱烤約15分鐘",
        "burger": "1. 準備漢堡餅乾\n2. 煎牛肉餡餅\n3. 組合：麵包 + 牛肉餡 + 生菜 + 番茄"
    }
    return recipes.get(food_name.lower(), "找不到此食物的製作過程，請嘗試其他食物。")

# LINE webhook 入口
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image_bytes = b''.join(chunk for chunk in message_content.iter_content(1024))

    food_name = recognize_food(image_bytes)

    if food_name:
        recipe = get_recipe(food_name)
        reply = f"您上傳的食物是：{food_name}\n製作過程：\n{recipe}"
    else:
        reply = "無法識別圖片中的食物，請再試一次。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# Render 啟動設定
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
