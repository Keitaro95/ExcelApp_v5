

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