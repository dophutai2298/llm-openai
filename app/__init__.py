from flask import Flask
from dotenv import load_dotenv
from .routes import api_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Register Blueprints
    app.register_blueprint(api_bp)

    return app
