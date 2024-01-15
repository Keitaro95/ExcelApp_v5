
from pathlib import Path
import tempfile
import os
from flask import Flask, flash, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from glob import glob
import pandas as pd
import chardet
import openpyxl
import pykakasi

import functions

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xlsm', 'xls', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000  # 16メガバイト
app.secret_key = 'your_secret_key_here'

kakasi = pykakasi.kakasi()


# 拡張子の確認
def allowed_file(filename):
    # .があるかどうか
    # .の右で1回区切って、index1を小文字にして拡張子を得る
    # それがEXTENTIONSにあり、OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('index.html')


# 一つのファイルを扱う # 多分,まずはdbに格納するのがいい
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('ファイルがありません')

        file = request.files.get('file')

        if file.filename == '':
            flash('選択されたファイルがありません。')

        if file and allowed_file(file.filename):
            # ファイル名を日本語名からローマ字に変換
            japanese_filename = "".join([item['hepburn'] for item in kakasi.convert(file.filename)])
            filename = secure_filename(japanese_filename)

            #upload用のフォルダに保存
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            comment1 = 'ファイルが正常に保存されました'
            
            # return render_template('table.html', header=header, record=record)
            return render_template('index.html', comment=comment1)
        else:
            raise ValueError('ファイル形式がサポートされていません。')
    return render_template('index.html') 


@app.route('/table') # /tableがきたら処理
def table():
    file = request.files.get('file')
    filename = file.filename
    #pandasのdf形式にする
    if filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.xlsm'):
        df = pd.read_excel(file)
    elif filename.endswith('.csv'):
        try:
            df = file.read().decode('utf-8')
        except:
            df = file.read().decode('shift-jis')
        header = df.columns
        record = df.values.tolist()
    return render_template('table.html')



@app.route('/print', methods=['GET', 'POST'])
def print():
    if request.method == 'POST':
        functions.excel_print()
    return render_template('index.html')

# # ファイルを一時時保存するパーツ

# file_dir = Path(r'data/')
# password = 'hogehoge'
# sheet_name = 'Sheet1'

# # 複数ファイル一個ずつ
# for file in file_dir.glob("*.xlsx"):
#     with file.open("rb") as f, tempfile.TemporaryFile() as tf:
#         office_file = msoffcrypto.OfficeFile(f)
#         office_file.load_key(password=password)
#         office_file.decrypt(tf) パスワード解除
#         df = pd.read_excel(tf, sheet_name=sheet_name)
#     df.to_csv('output/' + file.name.replace('', 'xlsx') + '.csv',index=False)


def main():
    app.debug = True
    app.run()

if __name__ == "__main__":
    main()
