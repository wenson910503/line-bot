import os  # 用於存取環境變數
import re  # 用於正則表達式處理（如移除 HTML 標籤）
import requests  # 用來發送 HTTP 請求的第三方模組
from flask import Flask, request, abort  # Flask 用來建立 Web 應用、處理請求與異常
from linebot import LineBotApi, WebhookHandler  # LINE Bot SDK：API 呼叫與事件處理器
from linebot.exceptions import InvalidSignatureError  # 用來處理簽章驗證錯誤的例外類型
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage  # 處理 LINE 訊息事件與文字、圖片回覆

app = Flask(__name__)  # 建立 Flask Web 應用的實例

# LINE Bot 的 Channel Access Token，授權用來呼叫 Messaging API
line_bot_api = LineBotApi('i8DEpkz7jgRNnqRR4mWbPxC5oesrSpXbw2c+5xpzkLASeiBvdtv1uny/4/iXeO4lJygtxMZylP6IlFmQq/Lva/Ftd/H05aGKjTFlHZ3iSZo1sEMmBKRVMTTemEtU0zKtk9S9nqXIGc8CnOWSS80zKAdB04t89/1O/w1cDnyilFU=')  # 設定 LINE Bot 的金鑰

# LINE Bot 的 Channel Secret，用於驗證從 LINE 發來的請求是否合法
handler = WebhookHandler('e95d4cac941b6109c3379f5cb7a7c46c')  # 設定 LINE Bot 的 Secret

# Google Places API 金鑰，供地點與照片查詢使用
GOOGLE_PLACES_API_KEY = 'AIzaSyBqbjGjjpt3Bxo9RB15DE4uVBmoBRlNXVM'  # 設定 Google Places API 金鑰

# Google Maps API 金鑰，供路線規劃使用
GOOGLE_MAPS_API_KEY = 'AIzaSyBrE625SLt1CFnVtm6mrOlws5gvQaXthHs'  # 設定 Google Maps API 金鑰

# 使用 Google Places API 查詢與使用者輸入關聯的餐廳資訊，最多回傳 3 間
def search_restaurants(location):  # 定義查詢餐廳的函式，參數為位置（location）
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"  # 設定 Google Places Text Search API 的端點
    params = {  # 設定 API 查詢參數
        "query": f"{location} 餐廳",  # 查詢關鍵字，加上「餐廳」以限定類別
        "key": GOOGLE_PLACES_API_KEY,  # 使用 Google Places API 金鑰
        "language": "zh-TW",  # 設定回應語言為繁體中文
    }

    try:
        response = requests.get(url, params=params, timeout=10)  # 發送 GET 請求，最多等 10 秒
        response.raise_for_status()  # 若 HTTP 狀態碼不是 200，會引發例外
        data = response.json()  # 將回應轉為 Python 字典格式

        # 若無結果則回傳預設訊息
        if "results" not in data or not data["results"]:
            return ["😢 沒有找到相關餐廳，請換個關鍵字試試看！"]  # 若找不到餐廳則回傳提示訊息

        # 依評分排序，取出前 3 名
        restaurants = sorted(data["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]

        messages = ["🍽 **熱門餐廳推薦** 🍽\n"]  # 儲存回傳的訊息內容

        for index, r in enumerate(restaurants, start=1):  # 遍歷搜尋結果，最多顯示三間餐廳
            name = r.get("name", "未知餐廳")  # 餐廳名稱
            rating = r.get("rating", "無評分")  # 評分（預設為無評分）
            address = r.get("formatted_address", "無地址資訊")  # 餐廳地址
            business_status = r.get("business_status", "無營業資訊")  # 營業狀態
            place_id = r.get("place_id", "")  # 地點唯一 ID（供後續查詢評論）

            # 嘗試取得照片的 URL（若有提供）
            photo_url = None
            if "photos" in r:  # 若餐廳有提供照片
                photo_reference = r["photos"][0]["photo_reference"]  # 取得照片參考ID
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"  # 生成圖片 URL

            # 取得該餐廳的評論（優先中文）
            reviews = get_reviews(place_id)  # 調用 get_reviews 函式獲取餐廳的評論

            # 組合訊息文字
            message = f"🏆 **{index}. {name}**\n"
            message += f"⭐ 評分：{rating}/5.0\n"
            message += f"📍 地址：{address}\n"
            message += f"🕒 營業狀況：{business_status}\n"
            if reviews:  # 若有評論
                message += f"💬 最佳評論：{reviews}\n"
            message += f"🚗 [Google Maps 導航](https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')})\n"  # 添加導航連結

            messages.append(message.strip())  # 加入文字訊息

            if photo_url:  # 若有圖片則一併加入
                messages.append(photo_url)  # 加入圖片 URL

        return messages  # 回傳所有格式化的訊息

    except requests.exceptions.RequestException as e:  # 捕捉請求錯誤
        return [f"❌ 無法獲取餐廳資訊：{e}"]  # 若請求失敗則回傳錯誤訊息

# 使用 Place ID 查詢特定地點的評論資訊
def get_reviews(place_id):  # 定義用 Place ID 查詢評論的函式
    review_url = "https://maps.googleapis.com/maps/api/place/details/json"  # Google Place Details API 端點
    params = {  # 設定查詢參數
        "place_id": place_id,  # 地點 ID
        "key": GOOGLE_PLACES_API_KEY,  # API 金鑰
        "language": "zh-TW"  # 輸出繁體中文內容
    }

    try:
        response = requests.get(review_url, params=params, timeout=10)  # 發送 GET 請求
        response.raise_for_status()  # 若 HTTP 狀態碼不是 200，會引發例外
        data = response.json()  # 將回應轉為 Python 字典格式

        if "result" in data and "reviews" in data["result"]:  # 檢查是否有評論
            reviews = data["result"]["reviews"]  # 取得評論列表
            for review in reviews:  # 遍歷所有評論
                if 'zh' in review['language']:  # 優先找中文評論
                    return review['text']  # 回傳中文評論
            return reviews[0]['text'] if reviews else None  # 若無中文則回傳第一筆評論
        return None  # 若沒有評論結果

    except requests.exceptions.RequestException:  # 捕捉請求錯誤
        return None  # 請求失敗時不回傳任何評論

# 使用 Google Directions API 查詢步行路線
def get_route(origin, destination):  # 定義一個函式，接收出發地與目的地作為參數
    url = "https://maps.googleapis.com/maps/api/directions/json"  # 設定 Google Directions API 的 JSON 端點
    params = {  # 設定路線查詢的參數
        "origin": origin,  # 出發地
        "destination": destination,  # 目的地
        "mode": "walking",  # 設定交通方式為「步行」
        "language": "zh-TW",  # 設定回傳資料語言為繁體中文
        "key": GOOGLE_MAPS_API_KEY  # Google Maps API 金鑰
    }

    try:
        response = requests.get(url, params=params, timeout=10)  # 發送 GET 請求
        response.raise_for_status()  # 若 HTTP 狀態碼非 200，會觸發例外錯誤
        data = response.json()  # 將回應轉為 Python 字典格式

        if data["status"] == "OK":  # 檢查 API 是否成功回傳路線資料
            steps = data["routes"][0]["legs"][0]["steps"]  # 取得路線中的步驟資料
            directions = "\n".join([  # 格式化每一步的指示
                f"{i+1}. {re.sub('<[^<]+?>', '', step['html_instructions'])}"  # 移除 HTML 標籤，並加上步驟編號
                for i, step in enumerate(steps)  # 逐一處理每一個步驟
            ])
            map_link = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode=walking"  # 產生導航連結
            directions += f"\n\n📍 點我直接導航：\n👉 {map_link}"  # 添加導航連結
            return directions  # 回傳整理好的文字路線資訊
        else:
            return "無法取得路線，請確認地點是否正確。"  # 若 API 回應不成功，回傳錯誤訊息
    except requests.exceptions.RequestException as e:  # 捕捉請求錯誤
        return f"查詢路線時發生錯誤：{e}"  # 回傳錯誤原因
    except requests.exceptions.RequestException as e:  # 捕捉請求錯誤
        return f"查詢路線時發生錯誤：{e}"  # 回傳錯誤原因
