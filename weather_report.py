import os
import json
import requests
from datetime import datetime

# Cấu hình
LAT = 21.0285 # Tọa độ Hà Nội
LON = 105.8542
HISTORY_FILE = "weather_history.json"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_weather():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=temperature_2m_max,temperature_2m_min,uv_index_max&hourly=precipitation_probability&timezone=Asia%2FBangkok"
    res = requests.get(url).json()
    
    daily = res['daily']
    hourly = res['hourly']
    
    max_temp = daily['temperature_2m_max'][0]
    min_temp = daily['temperature_2m_min'][0]
    uv_max = daily['uv_index_max'][0]
    
    # Tìm giờ có khả năng mưa cao nhất trong ngày (từ 7h sáng đến 23h)
    today_rain_probs = hourly['precipitation_probability'][7:24]
    max_rain_prob = max(today_rain_probs)
    rain_hour = today_rain_probs.index(max_rain_prob) + 7
    
    return max_temp, min_temp, uv_max, max_rain_prob, rain_hour

def main():
    max_temp, min_temp, uv_max, max_rain_prob, rain_hour = get_weather()
    
    # 1. Đọc dữ liệu hôm qua
    history_data = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history_data = json.load(f)
            except:
                pass
    last_max_temp = history_data.get("last_max_temp")

    # 2. Xây dựng tin nhắn
    msg = f"🌤 **BẢN TIN THỜI TIẾT HÀ NỘI**\n\n"
    msg += f"• Nhiệt độ: {min_temp}°C - {max_temp}°C\n"
    
    if max_rain_prob >= 50:
        msg += f"• Mưa: Khả năng {max_rain_prob}% (Dễ mưa nhất lúc {rain_hour}h00)\n"
    
    # 3. Logic nhắc nhở
    notes = []
    
    if max_rain_prob >= 50:
        notes.append("- Có thể mưa, hãy mang theo ô/áo mưa.")
        
    if max_temp >= 34 or uv_max >= 8:
        notes.append("- Nắng gắt (UV cao), chú ý chống nắng.")
    elif max_temp <= 18:
        notes.append("- Trời lạnh, nhớ mặc ấm.")

    # So sánh chênh lệch nhiệt độ
    if last_max_temp:
        diff = max_temp - last_max_temp
        if diff >= 3:
            notes.append(f"- Nóng hơn hôm qua {round(diff, 1)}°C.")
        elif diff <= -3:
            notes.append(f"- Lạnh hơn hôm qua {round(abs(diff), 1)}°C, chú ý sức khỏe.")

    if notes:
        msg += f"\n💡 **Lưu ý:**\n" + "\n".join(notes)

    # 4. Gửi Telegram
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(tg_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

    # 5. Lưu lại cho ngày mai
    with open(HISTORY_FILE, "w") as f:
        json.dump({"last_max_temp": max_temp}, f)

if __name__ == "__main__":
    main()