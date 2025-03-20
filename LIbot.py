from PIL import Image, ImageDraw, ImageFont
import requests
import os

# 確保 Pillow 已安裝
try:
    from PIL import Image
except ImportError:
    os.system("pip install Pillow")
    from PIL import Image  # 安裝後重新導入

def search_restaurants(location):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{location} 餐廳",
        "key": "YOUR_GOOGLE_PLACES_API_KEY",
        "language": "zh-TW",
    }
    
    response = requests.get(url, params=params).json()
    if "results" not in response or not response["results"]:
        return []
    
    restaurants = sorted(response["results"], key=lambda r: r.get("rating", 0), reverse=True)[:3]
    results = []
    
    for r in restaurants:
        name = r.get("name", "未知餐廳")
        rating = r.get("rating", "無評分")
        address = r.get("formatted_address", "無地址資訊")
        business_status = r.get("business_status", "無營業資訊")
        results.append((name, rating, address, business_status, "暫無評論"))
    
    return results

def generate_restaurant_image(restaurants):
    width, height = 800, 600
    bg_color = (245, 245, 220)
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 40)
        font_text = ImageFont.truetype("arial.ttf", 30)
    except:
        font_title = font_text = None
    
    draw.text((20, 20), "🍽 熱門餐廳推薦", fill=(0, 0, 0), font=font_title)
    
    y = 80
    for index, r in enumerate(restaurants):
        name, rating, address, status, review = r
        text = f"🏆 {index+1}. {name}\n⭐ 評分: {rating}/5.0\n📍 地址: {address}\n🕒 營業狀況: {status}\n💬 評論: {review}"
        draw.text((20, y), text, fill=(50, 50, 50), font=font_text)
        y += 150
    
    image.show()
    image.save("restaurant_info.png")

location = "台北燒肉"
restaurants = search_restaurants(location)
if restaurants:
    generate_restaurant_image(restaurants)

