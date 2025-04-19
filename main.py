from flask import Flask
import os

app = Flask(__name__) 

@app.route("/", methods=['GET'])
def main_welcome():
    return "<h2>Welcome to APIs my chatbot<h2>"


@app.route("/hello", methods=['GET'])
def hello():
    return "hello world"


if __name__ == '__main__':
    app.run(debug=True)