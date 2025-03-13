import requests

# 📍 Google Places API 查詢函數
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

        # 取得前 5 間餐廳
        restaurants = data["results"][:5]
        reply_message = "🍽 熱門餐廳推薦 🍽\n\n"
        all_messages = []  # 儲存所有分段訊息

        for index, r in enumerate(restaurants):
            name = r.get("name", "未知餐廳")
            rating = r.get("rating", "無評分")
            address = r.get("formatted_address", "無地址資訊")
            business_status = r.get("business_status", "無營業資訊")
            place_id = r.get("place_id")

            # Retrieve details for each restaurant to get reviews
            place_details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": place_id,
                "key": GOOGLE_PLACES_API_KEY,
            }
            details_response = requests.get(place_details_url, params=details_params, timeout=10)
            details_response.raise_for_status()
            details_data = details_response.json()

            # Get reviews from place details
            reviews = details_data.get("result", {}).get("reviews", [])
            best_review_text = "沒有可用的評價"
            best_review_image = None

            if reviews:
                # Assuming the best review is the one with the highest rating
                best_review = max(reviews, key=lambda review: review.get("rating", 0))
                best_review_text = best_review.get("text", "無評價內容")
                best_review_image = best_review.get("profile_photo_url", None)

            # Try getting photo reference for richer information
            photos = r.get("photos", [])
            photo_reference = photos[0]["photo_reference"] if photos else None
            photo_url = None
            if photo_reference:
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"

            # Build the message for this restaurant
            restaurant_message = f"🔹 **{index+1}. {name}**\n"
            restaurant_message += f"⭐ 評分：{rating}/5.0\n"
            restaurant_message += f"📍 地址：{address}\n"
            restaurant_message += f"🕒 營業狀況：{business_status}\n"
            if photo_url:
                restaurant_message += f"📸 [餐廳照片]({photo_url})\n"
            restaurant_message += f"📝 最佳評價：\n{best_review_text}\n"
            if best_review_image:
                restaurant_message += f"📷 評論圖片：[查看圖片]({best_review_image})\n"
            restaurant_message += "\n"

            # If adding this message exceeds 5000 characters, split it into a new message
            if len(reply_message + restaurant_message) > 5000:
                all_messages.append(reply_message.strip())  # Save the current message
                reply_message = "🍽 熱門餐廳推薦 🍽\n\n"  # Start a new message

            reply_message += restaurant_message  # Append the restaurant info

        # Add the final message if it's not empty
        if reply_message.strip():
            all_messages.append(reply_message.strip())

        return "\n\n---\n\n".join(all_messages)  # Join all the segments

    except requests.exceptions.RequestException as e:
        return f"❌ 無法獲取餐廳資訊：{e}"
