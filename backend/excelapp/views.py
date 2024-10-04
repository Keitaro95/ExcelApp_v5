from flask import (
    Blueprint, Flask, session, flash, render_template, request, 
    redirect, url_for, send_file, jsonify, json, current_app, abort
)
from flask_login import (
    login_user, login_required, logout_user, current_user
)
from werkzeug.utils import secure_filename
from flask_dance.contrib.google import google
from google.oauth2 import id_token, service_account
from sqlalchemy import select
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from io import BytesIO
import pandas as pd
from uuid import uuid4
import tempfile, chardet, os, openpyxl, pykakasi, requests, os, google

from excelapp import basedir, db
from excelapp.models import User, Asset, PrintInfo
from excelapp.forms import LoginForm, RegisterForm
from excelapp.functions import sheetbyname, copyrowdata, excel_print


ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
bp = Blueprint('app', __name__, url_prefix='') 
kakasi = pykakasi.kakasi()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_username(email):
    return email.rsplit('@')[0]

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/signup')
def signup():
    return render_template('signup.html')

@bp.route('/explain')
def explain():
    return render_template('explain.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.select_by_email(form.email.data)
        if user and user.verify_password(form.password.data):
            login_user(user)
            flash('ログインに成功しました。', 'success')
            return redirect(url_for('app.home'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません。', 'error')
    return render_template('login.html', form=form)

CLIENT_SECRET_FILE = 'backend/excelapp/client_secret.json'
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google_auth_oauthlib.flow import Flow
import google.oauth2.credentials
import os, hashlib

@bp.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
    )
    flow.redirect_uri = url_for('app.oauth2callback', _external=True)
    authorization_url, state  = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        )
    session['state'] = state
    return redirect(authorization_url)


@bp.route('/oauth2callback')
def oauth2callback():
    state = session.get('state')
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = url_for('app.oauth2callback', _external=True)
    print(f"Authorization response: {request.url}")  # デバッグ用のログ
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }
    from google.oauth2 import id_token
    token_request = google.auth.transport.requests.Request()
    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=token_request,
        audience=os.getenv('GOOGLE_CLIENT_ID')
    )
    email = id_info['email']
    user = User.select_by_email(email)
    if not user:
        user = User(
            email=email,
            username=extract_username(email)
        )
        user.add_user()
    login_user(user, remember=True)
    return redirect(url_for('app.index'))

@bp.route('/logout')
@login_required
def logout():
    if 'credentials' not in session:
        return redirect(url_for('app.authorize'))
    credentials = session['credentials']
    token = credentials['refresh_token']
    revoke = requests.post(
        "https://oauth2.googleapis.com/revoke",
        params={"token": token},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    status_code = getattr(revoke, 'status_code')
    print(status_code)
    if status_code == 200:
        del session['credentials']
        session.clear()
        logout_user()
        return redirect(url_for('app.home'))
    else:
        flash('An error occurred.')
        return redirect(url_for('app.index'))

# sessionの期限が過ぎていたら、ログアウトにリダイレクトする
@bp.before_request
def timeout_and_usercheck():
    # セッションタイムアウトのチェック
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        if datetime.now() - last_activity > timedelta(minutes=30):  # 前回のリクエストから30分経っていたら強制タイムアウト
            session.clear()
            flash('セッションがタイムアウトしました。再度ログインしてください。', 'info')
            return redirect(url_for('logout')) # ログアウトに遷移
    # 現在の時刻を最終アクティビティとして記録
    session['last_activity'] = datetime.now().isoformat()
    # IPアドレスとユーザーエージェントのチェック（既存のコード）
    # if 'ip' not in session:
    #     session['ip'] = request.remote_addr
    # if 'user_agent' not in session:
    #     session['user_agent'] = request.headers.get('User-Agent')

    # if session['ip'] != request.remote_addr or session['user_agent'] != request.headers.get('User-Agent'):
    #     session.clear()
    #     flash('セッションが無効になりました。再度ログインしてください。', 'warning')
    #     return redirect(url_for('app.home'))


@bp.route('/user')
@login_required
def user():
    return render_template('user.html')

@bp.route('/user_delete', methods=['GET', 'POST'])
@login_required
def user_delete():
    if current_user.is_authenticated:
        if request.method == "POST":
            user = User.select_by_id(current_user.id) 
            user.delete_user()
            return redirect(url_for('app.home'))
    return render_template('user_delete.html')


@bp.route('/index')
@login_required
def index():
    user_id = current_user.id
    assets = db.session.execute(select(Asset).filter_by(user_id=user_id)).scalars().all()
    if assets:
        return render_template('index.html', assets=assets)
    return render_template('index.html')

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'GET':
        return render_template('index.html')
    
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('ファイルが指定されていません。', 'error')
            return redirect(url_for('app.index'))
        if file.filename == '':
            flash('選択されたファイルがありません。', 'error')
            return redirect(url_for('app.index'))
        if not allowed_file(file.filename):
            flash('ファイル形式が許可されていません。', 'error')
            return redirect(url_for('app.index'))
        japanese_filename = "".join([item['hepburn'] for item in kakasi.convert(file.filename)])
        file_name = secure_filename(japanese_filename)

        # try:
        #     df = pd.read_excel(file)
        #     # ここに読み込んだファイルの形式のエラー判定を書く(今回は省略)
        # except Exception as e:
        #     flash('ファイルの読み込みに失敗しました。', 'error')
        #     return redirect(url_for('app.index'))

        # # ユーザーの現在のアップロード数を確認
        # upload_limit = 5
        # current_uploads = Asset.query.filter_by(user_id=current_user.id).count()
        # if current_uploads >= upload_limit:
        #     flash('アップロード制限に達しました。最大5ファイルまでです。', 'error')
        #     return redirect(url_for('app.index'))

        userdir = session.get('userdir')
        if not os.path.exists(userdir):
            os.makedirs(userdir)
        file_path = os.path.join(userdir, file_name)
        if os.path.exists(file_path):
            flash ('同一のファイル名で保存できません。', 'error')
            return redirect(url_for('app.index'))
        file.save(file_path)
        asset = Asset(
                asset_name = file_name,
                asset_path = file_path,
                user_id = current_user.id
            )
        asset.add_asset()
        flash('ファイルが正常にアップロードされました。', 'success_upload')
        return redirect(url_for('app.index'))
    

@bp.route('/preview/<int:fileid>') 
@login_required
def preview(fileid):
    user_id = current_user.id
    asset = Asset.get_one_asset(fileid, user_id)
    if not asset:
        flash('ファイルがありません', 'error')
        return redirect('app.index')
    filename = asset.asset_name
    filepath = asset.asset_path
    sheets_data = []
    if filename.endswith(('.xlsx', '.xls')):
        try:
            excel_file = pd.ExcelFile(filepath)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets_data.append({
                    'sheet_name': sheet_name,
                    'header': df.columns.tolist(),
                    'record': df.values.tolist()
                })
        except Exception as e:
            return render_template('error.html', error_message='Excelファイルの処理中にエラーが発生しました')
    elif filename.endswith('.csv'):
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filepath, encoding='shift-jis')
            except Exception as e:
                return render_template('error.html', error_message='CSVファイルの読み込みに失敗しました')
        sheets_data.append({
            'sheet_name': 'Sheet1',
            'header': df.columns.tolist(),
            'record': df.values.tolist()
        })
    else:
        return render_template('error.html', error_message='サポートされていないファイル形式です')
    return render_template('preview.html', sheets_data=sheets_data)


@bp.route('/download/<int:fileid>', methods=['GET'])
@login_required
def download(fileid):
    user_id = current_user.id
    asset = Asset.get_one_asset(fileid, user_id)
    if asset is None:
        abort(404)
    if asset.user_id != user_id:
        abort(403)
    try:
        return send_file(asset.asset_path,
                        download_name=asset.asset_name,
                        as_attachment=True
                        )
    except IOError:
        abort(404)


@bp.route('/delete/<int:fileid>')
@login_required
def delete(fileid):
    user_id = current_user.id
    asset = Asset.get_one_asset(fileid, user_id)
    file_path = asset.asset_path
    if os.path.exists(file_path):
        os.remove(file_path)
    asset.delete_asset()
    flash('ファイルが削除されました', 'success_delete')
    return redirect(url_for('app.index'))


@bp.route('/sheet/<int:fileid>', methods=['GET', 'POST'])
@login_required
def sheet(fileid):
    user_id = current_user.id
    asset = Asset.get_one_asset(fileid, user_id)
    if not asset:
        flash('ファイルがありません', 'error')
        return redirect(url_for('app.index'))
    filename = asset.asset_name
    file_path = asset.asset_path
    try:
        file = glob(file_path)[0]
    except IndexError:
        flash('ファイルが見つかりません。', 'error')
        return redirect(url_for('app.index'))
    if request.method == 'POST': 
        _file = sheetbyname(file_path)
        _filename = filename.split('.xlsx')[0].split(',')[0] + '_sheet.xlsx'
        _filepath = os.path.join(os.path.dirname(asset.asset_path), _filename.split('.')[0] + '_sheet.xlsx')
        _file.save(_filepath)
        new_asset = Asset(
            asset_name = _filename,
            asset_path = _filepath,
            user_id = current_user.id
        )
        new_asset.add_asset()
        flash('列にある氏名からシートを作成しました', 'success_sheet')
        return redirect(url_for('app.index'))
    flash('シート作成を開始します', 'info')
    return redirect(url_for('app.index'))


@bp.route('/copy/<int:fileid>', methods=['GET', 'POST'])
@login_required
def copy(fileid):
    user_id = current_user.id
    asset = Asset.get_one_asset(fileid, user_id)
    if not asset:
        flash('ファイルがありません', 'error')
        return redirect(url_for('app.index'))
    filename = asset.asset_name
    file_path = asset.asset_path
    if not os.path.exists(file_path):
        flash('ファイルが見つかりません。', 'error')
        return redirect(url_for('app.index'))
    if request.method == 'POST': 
        _file = copyrowdata(file_path)
        _filename = f"{os.path.splitext(filename)[0]}_copyrow.xlsx"
        _filepath = os.path.join(os.path.dirname(asset.asset_path), _filename)
        _file.save(_filepath)
        new_asset = Asset(
            asset_name = _filename,
            asset_path = _filepath,
            user_id = current_user.id
        )
        new_asset.add_asset()
        flash('シート名ごとにデータを移植しました', 'success_copyrow')
        return redirect(url_for('app.index'))
    flash('データ移植を開始します', 'info')
    return redirect(url_for('app.index'))


