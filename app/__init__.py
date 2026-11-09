"""Laura AI Hub - Flask application factory."""
import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # read ANTHROPIC_API_KEY etc. from .env if present


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        APP_NAME="Laura AI Hub",
        APP_PASSWORD=os.environ.get("APP_PASSWORD", ""),
    )
    if test_config:
        app.config.update(test_config)

    from .routes import bp

    app.register_blueprint(bp)
    return app
