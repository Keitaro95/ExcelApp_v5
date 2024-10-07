# coding: UTF-8
import os
from flask_dance.contrib.google import make_google_blueprint
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


login_manager = LoginManager()
login_manager.login_view = 'app.google_login'

db = SQLAlchemy()
migrate = Migrate()
basedir = os.path.abspath(os.path.dirname(__name__))
database_path = os.path.join(basedir, 'data.sqlite')
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(database_path)
SQLALCHEMY_TRACK_MODIFICATIONS=False



client_secrets_file = os.path.join(os.path.dirname(__file__), "client_secret.json")

config = {
    'development': 'config/development/settings.cfg',
    'production': 'config/production/settings.cfg',
}

def create_app():
    app = Flask(__name__)
    config_file = config[os.getenv('ENVIRONMENT', 'development')]
    app.config.from_pyfile(config_file)
    from excelapp.views import bp
    app.register_blueprint(bp)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    return app