# 📍 Google Places API 查詢函數（加入餐廳排名與圖片）
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

        # 如果 API 沒回傳結果
        if "results" not in data or not data["results"]:
            return "😢 沒有找到相關餐廳，請換個關鍵字試試看！"

        # 按評分排序（由高到低）
        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:5]
        
        messages = []

        for index, r in enumerate(restaurants, start=1):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            business_status = r.get("business_status", "無營業資訊")

            reply_text = (
                f"🏆 **{index}. {name}**\n"
                f"⭐ 評分：{rating}/5.0\n"
                f"📍 地址：{address}\n"
                f"🕒 營業狀況：{business_status}"
            )

            # 檢查是否有圖片
            photo_url = None
            if "photos" in r and r["photos"]:
                photo_reference = r["photos"][0]["photo_reference"]
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"

            # 回應文字訊息
            messages.append(TextSendMessage(text=reply_text))

            # 回應圖片訊息（如果有圖片）
            if photo_url:
                from linebot.models import ImageSendMessage
                messages.append(ImageSendMessage(original_content_url=photo_url, preview_image_url=photo_url))

        return messages

    except requests.exceptions.RequestException as e:
        return [TextSendMessage(text=f"❌ 無法獲取餐廳資訊：{e}")]

# 🔄 處理使用者發送的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()

    if len(user_input) >= 2:  # 限制最小字數，避免無效查詢
        results = search_restaurants(user_input)
    else:
        results = [TextSendMessage(text="❌ 請輸入 **城市名稱 + 美食類型**（例如：「台北燒肉」）。")]

    line_bot_api.reply_message(event.reply_token, results)
