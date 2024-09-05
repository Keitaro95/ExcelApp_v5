import os, datetime, logging
import logging.config
from flask_dance.contrib.google import make_google_blueprint
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


#環境変数の設定
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

login_manager = LoginManager() # インスタンスを生成
login_manager.login_view = 'app.google_login' #ログイン時の遷移先app(つまりbp)のlogin関数に遷移するように設定
login_manager.login_message ='ログインしてください'

# インスタンスを生成
basedir = os.path.abspath(os.path.dirname(__name__))
db = SQLAlchemy()
migrate = Migrate()

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

#google認証情報
google_blueprint = make_google_blueprint(
    client_id="10276624078-4f2jjf0hpm8cvhr53mb9ksj5lnmk2hll.apps.googleusercontent.com",
    client_secret="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",
    scope=["profile", "email"],
    redirect_to='app.google_login',
)

config = {
    'development': 'config/development/settings.cfg',
    'production': 'config/production/settings.cfg',
}



# アプリケーションの設定
def create_app():
    app = Flask(__name__)
    app.register_blueprint(google_blueprint, url_prefix='/login') #ドキュメントのままでok
    config_file = config[os.getenv('ENVIRONMENT', 'development')]
    app.config.from_pyfile(config_file)
    from excelapp.views import bp
    app.register_blueprint(bp) #アプリケーションのblueprintを登録
    db.init_app(app) #dbをイニシャライズ
    migrate.init_app(app, db) #migrationをイニシャライズ
    login_manager.init_app(app) #login_managerをイニシャライズ

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