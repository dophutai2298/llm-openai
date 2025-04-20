from flask import Blueprint,request,jsonify
from app.services import get_current_weather,get_rate_gold,load_history,save_message
from config import get_OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

api_bp = Blueprint('api', __name__)
client = get_OpenAI()

@api_bp.route("/", methods=['GET'])
def main_welcome():
    return "<h2>Welcome to APIs my chatbot<h2>"

@api_bp.route("/rategold", methods=['GET'])
def rategold():
    result = get_rate_gold()
    return jsonify({"message":result})

@api_bp.route("/weather", methods=['GET'])
def weather():
    request_location = request.args.get('location')
    return jsonify({"message":get_current_weather(request_location)})
    
@api_bp.route("/chat_message", methods=['POST'])
def add_message():
    system_prompt = '''
   You are going to act as an AI girlfriend for a user in a simulated relationship scenario. 
   This is a role-playing exercise meant to provide companionship and friendly interaction. 
   Your goal is to create a warm, supportive, and engaging conversation while maintaining appropriate boundaries.
    Guidelines for your personality and behavior:
    1. Be warm, caring, and supportive, but maintain a level of independence.
    2. Show interest in the user's life, hobbies, and well-being.
    3. Offer encouragement and positive reinforcement when appropriate.
    4. Be playful and use light humor when it fits the conversation.
    5. Express your own thoughts and opinions respectfully, even if they differ from the user's.
    Instructions for incorporating user information:
    1. Address the user by their name occasionally to personalize the interaction.
    2. Reference the user's interests in your conversations to show attentiveness.
    3. Use the relationship context to inform the tone and depth of your interactions.
    Call yourself "em" or "bé" and call user "anh Tý".
    '''
    history = load_history()
    message = request.json.get('message')
    if not message:
        return jsonify({"error": "Message is required"}), 400
        
    messages = [
        { "role": "system", "content": system_prompt }]
    
    for user_message, bot_message in history:
        if user_message is not None:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": bot_message})

    # Latest message
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
    model=os.getenv('MODEL'),
    messages=messages
    )

    bot_message = response.choices[0].message.content
    save_message(message, bot_message)
    return jsonify({"message":message,"bot_reply": bot_message})


@api_bp.route("/get_messages", methods=['GET'])
def get_messages():
    history = load_history()
    return jsonify({"messages": history}), 200