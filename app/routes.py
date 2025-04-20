from flask import Blueprint,request,jsonify
from app.services import get_current_weather,get_rate_gold,load_history,handle_chat_message,get_wikipedia_doc,normalize_text,view_website

from dotenv import load_dotenv
import os
load_dotenv()

api_bp = Blueprint('api', __name__)

@api_bp.route("/", methods=['GET'])
def main_welcome():
    return "<h2>Welcome to APIs my chatbot<h2>"



@api_bp.route("/gold", methods=['POST'])
def rategold():
    location = request.json.get('location')
    location=normalize_text(location)
    format_location = ""
    if location in ["vietnam","VN"]:
        format_location="vietnam"
    elif location in ["thegioi","world"]:
        format_location="world"
    else:
        return {"error": "Invalid location."}, 400

    result = get_rate_gold(format_location)
    return jsonify({"result": result})

@api_bp.route("/weather", methods=['GET'])
def weather():
    request_location = request.args.get('location')
    return jsonify({"result":get_current_weather(request_location)})


@api_bp.route("/wikipedia", methods=['POST'])
def wikipedia_api():
    message = request.json.get('message')
    result = get_wikipedia_doc(message,"vi")

    return jsonify({"result":result})


@api_bp.route("/view_website",methods=['POST'])
def summary():
    url = request.json.get('url')
    result = view_website(url)
    return jsonify({"result":result})

@api_bp.route("/chat_message", methods=['POST'])
def add_message():
    message = request.json.get('message')
    result = handle_chat_message(message)
    return jsonify(result)


@api_bp.route("/get_messages", methods=['GET'])
def get_messages():
    history = load_history()
    jsonify({"messages": history}), 200


