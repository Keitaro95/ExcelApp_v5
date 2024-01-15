
from pathlib import Path
import tempfile
import os
from flask import Flask, flash, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from glob import glob
import pandas as pd
import chardet

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xlsm', 'xls', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000  # 16メガバイト
app.secret_key = 'your_secret_key_here'


# 拡張子の確認
def allowed_file(filename):
    # .があるかどうか
    # .の右で1回区切って、index1を小文字にして拡張子を得る
    # それがEXTENTIONSにあり、OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 一つのファイルを扱う
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # fileはHTMLのname="file"に対応
        # flask側でもファイル形式の判定をサポートした方が良い
        if 'file' not in request.files:
            flash('ファイルがありません')
            # return redirect(request.url)

        # 複数ファイルをリスト形式で受け取る
        file = request.files['file']
        if file.filename == '':
            flash('選択されたファイルがありません。')
            # return redirect(request.url)

        # ここから以下がファイルに実際に処置を施す処理

        # ファイルがちゃんとあって、かつallowed_fileですよ
        if file and allowed_file(file.filename):
            # ファイル名の安全を保証する関数
            filename = secure_filename(file.filename)
            # excelファイルをcontentに格納
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            if filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.xlsm'):
                df = pd.read_excel(file)

            #csvファイルをcontentに格納
            elif filename.endswith('.csv'):
                try:
                    df = file.read().decode('utf-8')
                except:
                    df = file.read().decode('shift-jis')
                # with open(file, 'rb') as f:
                #     raw_data = file.read()
                #     result = chardet.detect(raw_data)
                #     encoding = result['encoding']
                # with open(file, 'rb') as f:

            #データフレームをHTMLの表形式に変換,htmlのtableタグに表示
            table = df.to_html(classes='table')
            return render_template('index.html')



        # エラー処理
        else:
            raise ValueError('ファイル形式がサポートされていません。')
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
