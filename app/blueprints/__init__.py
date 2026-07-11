def register_blueprints(app):
    from app.blueprints.main import bp as main_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.community import bp as community_bp
    from app.blueprints.news import bp as news_bp
    from app.blueprints.columns import bp as columns_bp
    from app.blueprints.my import bp as my_bp
    from app.blueprints.quiz import bp as quiz_bp
    from app.blueprints.api import bp as api_bp
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.seo import bp as seo_bp

    for bp in (main_bp, auth_bp, community_bp, news_bp, columns_bp,
               my_bp, quiz_bp, api_bp, admin_bp, seo_bp):
        app.register_blueprint(bp)
