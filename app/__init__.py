"""Laura AI Hub - Flask application factory."""
import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        APP_NAME="Laura AI Hub",
    )
    if test_config:
        app.config.update(test_config)

    from .routes import bp

    app.register_blueprint(bp)
    return app
