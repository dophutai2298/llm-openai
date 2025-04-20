import requests
from wikipediaapi import Wikipedia
import os
import json
from config import get_OpenAI
from constants import system_prompt_function, system_prompt
import inspect
from pydantic import TypeAdapter
# import groq

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
    Retrieve the latest gold price based on a specified location. This function is used to track changes in the gold market, helpful for financial planning or investment updates.
    :param prompt:
    - location (str): Choose either "vietnam" or "world".
        - "vietnam": Returns gold prices in major Vietnamese cities such as Hà Nội and TP.HCM.
        - "world": Returns the current global gold price.
    :output:
    - A list of dictionaries with gold price information.
      Each entry contains:
        - "new": Today's gold price
        - "old": Yesterday's gold price
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
    Summarize website content from the given URL.
    :param url: A valid website URL starting with http:// or https://.
                This is required to fetch and summarize the website content.

    :output: Returns all the content retrieved from the given URL.
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



tools = [
    {
        "type": "function",
        "function": {
            "name": "get_rate_gold",
            "description": inspect.getdoc(get_rate_gold),
            "parameters": TypeAdapter(get_rate_gold).json_schema(),
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": inspect.getdoc(get_current_weather),
            "parameters": TypeAdapter(get_current_weather).json_schema(),
        }
    },
    {
        "type": "view_website",
        "function": {
            "name": "view_website",
            "description": inspect.getdoc(view_website),
            "parameters": TypeAdapter(view_website).json_schema(),
        }
    }
    ]


FUNCTION_MAP = {
"get_rate_gold":get_rate_gold,
"get_current_weather": get_current_weather,
"view_website": view_website
}

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
    messages = [{ "role": "system", "content": system_prompt }]

    for user_message, bot_message in history:
        if user_message:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": bot_message})

    messages.append({"role": "user", "content": message})
    print("message: ",message)

    response = client.chat.completions.create(
        model=os.getenv('MODEL_CHECK_FUNC'),
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    bot_message = response.choices[0].message.content
    print("res bot_message:",response.choices[0].message)
    if (bot_message is not None):
        messages.append({ "role": "system", "content": system_prompt_function })
        response_chat = client.chat.completions.create(
            model=os.getenv('MODEL'),
            messages=messages
        )
        print(response_chat.choices[0].message.content)
        save_message(message, response_chat.choices[0].message.content)
        return {"message": message, "bot_reply": response_chat.choices[0].message.content}, 200
    else:
        first_choice = response.choices[0]
        tool_call = first_choice.message.tool_calls[0]
        print("tool_call:",tool_call)
        tool_call_function = tool_call.function
        tool_call_arguments = json.loads(tool_call_function.arguments)
        tool_function = FUNCTION_MAP[tool_call_function.name]
        result = tool_function(**tool_call_arguments)
        print("result tool_call:",result)
        messages.append(first_choice.message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call_function.name,
            "content": json.dumps({"result": result})
        })
        messages.append({ "role": "system", "content": system_prompt_function })
        response_chat = client.chat.completions.create(
            model=os.getenv('MODEL_CHECK_FUNC'),
            messages=messages
        )
        
        first_choice = response_chat.choices[0]
        print("first_choice:",first_choice)
        finish_reason = first_choice.finish_reason
        print("finish_reason:",finish_reason)
        save_message(message, first_choice.message.content)
        return {"message": message, "bot_reply": first_choice.message.content}, 200
