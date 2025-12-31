"""
Flask application factory.
Creates and configures the Flask app instance.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import get_config


db = SQLAlchemy()


def create_app(config_name='development'):
    """
    Application factory function.
    
    Args:
        config_name: Configuration environment ('development', 'testing', 'production')
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    
    config = get_config()
    app.config.from_object(config)
    
    db.init_app(app)
    
    # db.create_all() is moved to setup scripts to avoid issues with different SQL dialects
    
    from routes.views import views_bp
    from routes.api import api_bp
    
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
