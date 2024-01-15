from flask import Flask, render_template, request, redirect, url_for
import csv
from io import StringIO
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            return redirect(request.url)

        file = request.files['csv_file']
        if file.filename == '':
            return redirect(request.url)
        try:
            content = file.read().decode('utf-8')
        except:
            content = file.read().decode('shift-jis')

        #読み込んだcsvを行ごとに読み込む,csv_dataは行ごとのリスト？
        csv_data = csv.reader(StringIO(content).readlines())

        datalist = []
        if csv_data:
            for r in csv_data:
                datalist.append([d for d in r])
            df = pd.DataFrame(datalist)
            print(df)
            table = df.to_html(classes='table') # データフレームをテーブルタグに変換
            return render_template('index.html', table=table)
        else:
            print('読み込み失敗')
            return redirect(request.url)
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)