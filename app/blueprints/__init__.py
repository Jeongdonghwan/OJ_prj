def register_blueprints(app):
    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)
