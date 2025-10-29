from flask import Flask
from auth.routes import auth_bp
from main.routes import main_bp
import os

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    # IMPORTANT: set a strong secret key in production (env var)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
