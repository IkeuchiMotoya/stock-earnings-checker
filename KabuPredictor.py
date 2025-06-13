from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# 1. Webページ取得
url = "https://irbank.net/4437/pl"

options = webdriver.ChromeOptions()
options.add_argument('--headless')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get(url)
time.sleep(5)

# 2. BeautifulSoupでテーブル解析
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# 3. テーブル抽出
table = soup.find("table")
df = pd.read_html(str(table), header=0)[0]

# 4. 「通期 実績」の行のみ抽出（2列目に "通期 実績" を含む行）
df_actual = df[df.iloc[:, 1].astype(str).str.contains("通期\s*実績", na=False)].reset_index(drop=True)

# 5. 必要な列の数値化（カラム名は実データに合わせて変更）
df_actual["売上高"] = df_actual["売上高"].astype(str).str.replace(",", "").astype(float)
df_actual["営業利益"] = df_actual["営業利益"].astype(str).str.replace(",", "").astype(float)
df_actual["経常利益"] = df_actual["経常利益"].astype(str).str.replace(",", "").astype(float)
df_actual["当期純利益"] = df_actual["当期純利益"].astype(str).str.replace(",", "").astype(float)

# 6. 前年比を計算（1行目は前年比が出せないので NaN）
df_actual["売上高比率"] = df_actual["売上高"].pct_change().apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
df_actual["営業利益比率"] = df_actual["営業利益"].pct_change().apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
df_actual["経常利益比率"] = df_actual["経常利益"].pct_change().apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
df_actual["当期純利益比率"] = df_actual["当期純利益"].pct_change().apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")

# 7. 表示列を並べ替え
result = df_actual[[
    "提出日", 
    "売上高", "売上高比率",
    "営業利益", "営業利益比率",
    "経常利益", "経常利益比率",
    "当期純利益", "当期純利益比率"
]]

# 8. Excel出力＋起動
output_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\通期業績_4437_比率計算版.xlsx"
result.to_excel(output_path, index=False)
os.startfile(output_path)
