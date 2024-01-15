
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


# db保存用関数
#index.htmlから/uploadにアクセスがありました
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

            #dbに保存
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            comment1 = 'ファイルが正常に保存されました'
            
            # return render_template('table.html', header=header, record=record)
            return render_template('index.html', comment=comment1) #index.htmlに返ります
        else:
            raise ValueError('ファイル形式がサポートされていません。')
    return render_template('upload.html') 


# index.htmlから/tableにアクセスがありました
# dbに保存したファイルをtable形式で表示します
# 変更があれば上書きします
@app.route('/table') 
def table():
    filepath = os.path.abspath(os.path.dirname) # dbから呼び出し
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


# index.htmlから/printにアクセスがありました
# dbに保存のあるファイルをExcel形式で呼び出し,printの設定をします
@app.route('/print', methods=['GET', 'POST'])
def print():
    if request.method == 'POST':
        functions.excel_print()
    return render_template('index.html')


def main():
    app.debug = True
    app.run()

if __name__ == "__main__":
    main()
