
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


class PrintInfo:
    def __init__(self, papersize, orientation, fitToHeight, fitToWidth):
        self.papersize = papersize
        self.orientation = orientation
        self.fitToWidth = fitToWidth
        self.fitToHeight = fitToHeight

@app.route('/')
def home():
    return render_template('index.html')

# ファイルアップロード
# index.htmlから/uploadにアクセスがありました
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

            #ファイルディレクトリに保存
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            comment1 = 'ファイルが正常に保存されました'
            
            return render_template('index.html', comment=comment1) #index.htmlに返ります
        else:
            raise ValueError('ファイル形式がサポートされていません。')
    return render_template('upload.html') 


# index.htmlからhrefで/tableにアクセスがありました
# 保存したファイルをtable形式で表示します
# 変更があれば上書きします
# pandasのdataframe形式で読み取ってtable表示
# jQueryでタブをつまんで列順を並べ変える/またはとってくる列の順番をチェックを入れブラウザで選択する　
#0,1,2,3,4,にカラム名1,2,3,4が対応
@app.route('/table') 
def table():
    # この中にjQueryか何かでカラムを移動してそれで保存して確定ボタンポチ(POST)でindex.htmlに返ってくる処理
    filepath = os.path.abspath(os.path.dirname) # dbから呼び出し
    file = request.files.get('file')
    filename = file.filename
    if filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.xlsm'):
        df = pd.read_excel(file)
    elif filename.endswith('.csv'):
        try:
            df = file.read().decode('utf-8')
        except:
            df = file.read().decode('shift-jis')
        header = df.columns
        record = df.values.tolist() # ここら辺はクラスにした方が使いまわしがよさそう

    # この並びで確定しました(確定ボタンポチ)
    if request.get('file') == 'POST':
        # このなかにカラム変更のロジックをかく
        # htmlでカラムの番号を順番に指定して,functionsの引数でiloc番号を指定してカラムの順番
        comment2 = '列の順番が変更されました'
        return render_template('index.html', comment=comment2)
    return render_template('table.html', header=header, record=record)


# index.htmlからhrefで/tableにアクセスがありました
# アップロードしたファイル全てで
# ・{指定したコラム(列)}にある氏名で{氏名}が{sheetname}のws
# または{氏名}で{filename}{sheetname}のbook作る
@app.route('/make_byname')
def make_byname():
    if request.get('file') == 'POST':
        if request.values == 1:
            file = function.make_sheet(1) # シートを作るロジックを適用
        if request.values == 2:
            file = function.make_sheet(2) # ブックを作るロジックを適用
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return render_template('index.html')
    return render_template('make_byname.html')


# 氏名スキャンしてws名が{氏名}/book名が{氏名} のものに重複なしでデータを行ごと移植する



# index.htmlから/printにアクセスがありました
# ログイン情報で割り当てられたディレクトリにあるファイルをExcel形式で呼び出し,printの設定をします
@app.route('/print', methods=['GET', 'POST'])
def print():
    if request.method == 'POST':
        print(request.form) # クラスに適用する引数はsignup.htmlのname属性から取得
        user_info = PrintInfo(
            request.form.get('papersize'),
            request.form.get('orientation'),
            request.form.get('fitToWidth'),
            request.form.get('fitToHeight'),
        ) 

        # functions.excel_print()
        return render_template('index.html')
    return render_template('print.html')




def main():
    app.debug = True
    app.run()

if __name__ == "__main__":
    main()
