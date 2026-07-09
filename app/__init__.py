from flask import Flask

from config import Config


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    from app.db import engine as db_engine
    db_engine.init_app(app)

    from app.extensions import csrf, limiter, login_manager
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    limiter.enabled = app.config.get("RATELIMIT_ENABLED", True)

    from app.blueprints import register_blueprints
    register_blueprints(app)

    return app
