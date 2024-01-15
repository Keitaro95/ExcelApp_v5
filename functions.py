import openpyxl



#プリント設定
def excel_print(filepath):
  wb = openpyxl.load_workbook(filepath)
  for ws in wb.worksheets:
      ws.page_setup.orientation = "portrait" #印刷の向きは縦 横にしたいときは"landscape"
      ws.page_setup.fitToWidth = 1 #横方向は1ページ(用紙に揃える)
      ws.page_setup.fitToHeight = 0 #縦方向は用紙に揃えない
      ws.sheet_properties.pageSetUpPr.fitToPage = True #上2つのオプションを適用する
  wb.save("setting_print.xlsx") #ファイル名は適宜変更
