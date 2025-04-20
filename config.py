from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


def get_OpenAI():
    client = OpenAI(
    base_url=os.getenv('URL_TOGETHER'),
    api_key=os.getenv('API_KEY_TOGETHER')
    )
    return client
