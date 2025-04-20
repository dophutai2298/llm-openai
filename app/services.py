import requests
from wikipediaapi import Wikipedia
import os
import json
from config import get_OpenAI
from constants import system_prompt_function
import inspect
from pydantic import TypeAdapter

import unicodedata
import re

def normalize_text(text):
    # Chuyển thành dạng chuẩn unicode (NFD) để tách dấu ra khỏi chữ
    text = unicodedata.normalize('NFD', text)
    
    # Loại bỏ dấu (loại bỏ các ký tự không phải chữ cái Latin)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    
    # Xóa khoảng trắng và các ký tự không phải chữ cái/thường
    text = re.sub(r'\s+', '', text)  # Xóa khoảng trắng
    text = re.sub(r'[^a-zA-Z0-9]', '', text)  # Loại bỏ ký tự đặc biệt
    
    return text.lower()


def get_rate_gold(location:str="vietnam"):
    """
    Get the current gold rates for Vietnam or World.
    :param prompt: The location to get gold prices for. Accepted values are:
                     - "vietnam": returns prices for major cities in Vietnam (Hà Nội, TP.HCM)
                     - "world": returns global gold price ("Giá vàng thế giới")
    :output: List of dictionaries containing gold prices (new and old), formatted for each selected source. Key New is today's gold price and key old is yesterday's gold price
    """
    get_api_gold = requests.get('https://gw.vnexpress.net/cr/?name=tygia_vangv202206')
    data_gold = get_api_gold.json()
 
    keys_vietnam = ["ha_noi_sjc", "ha_noi_pnj", "tphcm_pnj", "tphcm_sjc"]
    keys_world = ["thegioi"]
    keys = keys_vietnam if location == "vietnam" else keys_world
    
    data = data_gold['data']['data']['gold']
    result=[]
    for key in keys:
        new = data["new"].get(key)
        old = data["old"].get(key)
        if new and old:
            result.append({
                "label": new["label"],
                "new_buy": new["buy"],
                "new_sell": new["sell"],
                "new_date": new["date_label"],
                "old_buy": old["buy"],
                "old_sell": old["sell"],
                "old_date": old["date_label"]
            })
    return result



def get_current_weather(location: str, unit: str='celsius'):
    """
    Get the current weather in a given location
    :param prompt: The parameters are the location to get the city name; the unit is Celsius or Fahrenheit, which is the temperature unit.
    :output: The temperature in the location input
    """
    format_location = location.lower().replace(" ", "+")
    url_get_lat_lon = f"https://nominatim.openstreetmap.org/search?q={format_location}&format=json"
    headers = {"User-Agent": "Function-calling/1.0"} 

    response = requests.get(url_get_lat_lon, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            response_temperature = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={data[0]["lat"]}&longitude={data[0]["lon"]}&current_weather=true&temperature_unit={unit}')
            if response_temperature.status_code == 200:
                data_temp = response_temperature.json()
                get_temperature = data_temp.get("current_weather", {}).get("temperature")
                return f'Ở {location} có nhiệt độ là {get_temperature} {unit}'
    else:
        print(f"Lỗi {response.status_code}: {response.text}")
        return "Vị trí chưa chính xác"
    


def get_wikipedia_doc(title: str, lang: str = 'en'):
    """
    Retrieve the specified Wikipedia page for using the library wikipediaapi by get title page
    :param title: The name of the page for which to retrieve the Wikipedia page,, e.g., 'Hồ Chí Minh'.
    :output: All detail content of this title in Wikipedia  get by library wikipediaapi
    """
    wiki = Wikipedia(user_agent='DoPhuTai (dophutai.qn@gmail.com)', language=lang)
    page = wiki.page(title)

    if not page.exists():
        return f"Error: Wikipedia page '{title}' not found."

    doc = page.text
    # Split the document into paragraphs
    paragraphs = doc.split('\n\n')
    return paragraphs



def view_website(url: str):
    """
    Summarize website content through input url
    :param prompt: The parameter is URL to get content
    :output: All content is taken from URL
    """
    headers = {
    'Authorization': f'Bearer {os.getenv("AUTHORIZATION_JINA")}'
    }
    url_w_jina = f'https://r.jina.ai/{url}'
    response = requests.get(url_w_jina, headers=headers)
    if response.status_code != 200:
        print(f"Không thể truy cập {url}")
        return None
    return response.text


history_file_path = "chat_history.json"
def load_history():
    if not os.path.exists(history_file_path):
        return []
    with open(history_file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_message(user_message, bot_message):
    history = load_history()
    history.append({"user": user_message, "bot": bot_message})
    with open(history_file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# To do
def handle_chat_message(message: str):
    """
    Handle chat message logic for AI girlfriend.
    :param message: The user input message
    :return: A dict containing original message and bot reply
    """
    if not message:
        return {"error": "Message is required"}, 400

    client = get_OpenAI()
    
    history = load_history()
    messages = [{ "role": "system", "content": system_prompt_function }]

    for user_message, bot_message in history:
        if user_message:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": bot_message})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=os.getenv('MODEL'),
        messages=messages
    )

    bot_message = response.choices[0].message.content
    save_message(message, bot_message)

    return {"message": message, "bot_reply": bot_message}, 200
