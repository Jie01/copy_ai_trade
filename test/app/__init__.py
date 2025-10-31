from flask import Flask

def create_app():
    app = Flask(__name__)

    # Register blueprints
    from .routes import trades_bp
    app.register_blueprint(trades_bp)

    return app