from flask import Flask,request
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.services import get_rate_gold,get_current_weather

load_dotenv()
app = Flask(__name__) 

def get_OpenAI():
    client = OpenAI(
    base_url=os.getenv('URL_TOGETHER'),
    api_key=os.getenv('API_KEY_TOGETHER')
    )
    return client


@app.route("/", methods=['GET'])
def main_welcome():
    return "<h2>Welcome to APIs my chatbot<h2>"

@app.route("/rategold", methods=['GET'])
def rategold():
    return get_rate_gold()

@app.route("/weather", methods=['GET'])
def weather():
    request_location = request.args.get('location')
    return {"message":get_current_weather(request_location)}


client = get_OpenAI()
@app.route("/chat_message", methods=['POST'])
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

    message = request.json.get('message')
    if not message:
        return {"error": "Message is required"}, 400
    if 'messages' not in app.config:
        app.config['messages'] = []

    messages = [
        { "role": "system", "content": system_prompt }]
    
    for user_message, bot_message in app.config['messages']:
        if user_message is not None:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": bot_message})

    # Latest message
    messages.append({"role": "user", "content": message})


    print("messages: ",messages)
    response = client.chat.completions.create(
    model=os.getenv('MODEL'),
    messages=messages
    )

    bot_message = response.choices[0].message.content
    app.config['messages'].append([message, bot_message])
    return [{"bot_reply": bot_message,"message":message}]


@app.route("/get_messages", methods=['GET'])
def get_messages():
    messages = app.config.get('messages', [])
    return {"messages": messages}, 200


if __name__ == '__main__':
    app.run(debug=True)
  