import os, datetime, logging
import logging.config
from flask_dance.contrib.google import make_google_blueprint
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from google_auth_oauthlib.flow import Flow
import pathlib


login_manager = LoginManager()
login_manager.login_view = 'app.google_login'
# login_manager.login_message = 'ログインしてください'

# インスタンスを生成

db = SQLAlchemy()
migrate = Migrate()

basedir = os.path.abspath(os.path.dirname(__name__))
database_path = os.path.join(basedir, 'data.sqlite')
SQLALCHEMY_DATABASE_URI=f'sqlite:///{database_path}'
SQLALCHEMY_TRACK_MODIFICATIONS=False



# #app scheduler
# @scheduler.task('interval', id='delete_expired_files', minutes=30)
# def delete_expired_files():
#     expiration_minutes = 30
#     limit_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=expiration_minutes)
#     expired_assets = Asset.query.filter(Asset.uploadtime < limit_time).all()
#     for expired_asset in expired_assets:
#         try:
#             os.remove(expired_asset.asset_path)  # ファイルを削除
#             db.session.delete(expired_asset)  # データベースからレコードを削除
#         except FileNotFoundError:
#             print(f"File not found: {expired_asset.asset_path}")
#         except Exception as e:
#             print(f"Error deleting file {expired_asset.asset_path}: {e}")


client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

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

    # scheduler.init_app(app)
    # scheduler.start()

    # loggingをここに書く
    # log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)
    # if os.getenv('ENVIRONMENT', 'development') == 'development':
    #     log_file_path = os.path.join(basedir, 'excelapp', 'config', 'development', 'logger.conf')
    #     debug_mode = True #開発環境ではtrue
    # else:
    #     log_file_path = os.path.join(basedir, 'excelapp', 'config', 'production', 'logger.conf')
    #     debug_mode = False #本番環境ではfalse
    # logging.config.fileConfig(fname=log_file_path)
    # from flask.logging import default_handler
    # app.logger.removeHandler(default_handler) #デフォルトのログがなくなる
    return app