import requests
from wikipediaapi import Wikipedia
def get_rate_gold():
    get_api_gold = requests.get('https://gw.vnexpress.net/cr/?name=tygia_vangv202206')
    data_gold = get_api_gold.json()
    return data_gold['data']['data']['gold']


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

get_wikipedia_doc("Hồ Chí Minh")
