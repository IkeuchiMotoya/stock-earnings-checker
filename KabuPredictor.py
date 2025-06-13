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
df = pd.read_html(str(table))[0]

# ✅ 4. 「通期 実績」の行のみ抽出（1列目に含まれている前提）
df_actual = df[df.iloc[:, 1].astype(str).str.contains("通期\s*実績", na=False)].reset_index(drop=True)

# 5. Excel出力＋起動
output_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\通期業績_4437_実績のみ.xlsx"
df_actual.to_excel(output_path, index=False)
os.startfile(output_path)
