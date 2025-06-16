from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re

#株価の指標を出力するプログラム
# CSVファイルから銘柄コードを読み込む
csv_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\通期業績の推移、指標の取得\検索銘柄.csv"
ticker_df = pd.read_csv(csv_path, dtype={"銘柄コード": str})
ticker_list = ticker_df["銘柄コード"].tolist()
name_map = dict(zip(ticker_df["銘柄コード"], ticker_df["銘柄名"]))

# 抽出対象マップ（表示名: 対応キーワード）
items = {
    "PER（予）": r"PER（(連|個)）.*予",
    "EPS（予）": r"EPS（(連|個)）.*予",
    "EPS": r"EPS（(連|個)）(?!.*予)",
    "PBR": r"PBR（(連|個)）",
    "ROE（予）": r"ROE（(連|個)）.*予",
    "ROA（予）": r"ROA（(連|個)）.*予",
    "配当利回り（予）": r"配当利回り.*予",
    "時価総額": r"時価総額",
    "発行済み株式総数": r"発行済み株式総数"
}


# Seleniumドライバ初期化
options = webdriver.ChromeOptions()
# options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

all_results = []

for ticker in ticker_list:
    print(f"\n=== 処理中: {ticker} ===")
    base_url = f"https://irbank.net/{ticker}"
    driver.get(base_url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    e_href_tag = soup.find("a", href=re.compile(r"^/E\d+"))

    if not e_href_tag:
        print(f"❌ Eコード取得失敗: {ticker}")
        continue

    e_code = e_href_tag["href"].strip("/")
    driver.get(f"https://irbank.net/{e_code}")
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    title = soup.title.text.strip() if soup.title else ""

    results = {"銘柄コード": ticker, "銘柄名": name_map.get(ticker, title)}
    dl_elements = soup.find_all("dl")
# キーと値の抽出（柔軟に対応）
    for dl in dl_elements:
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            key = dt.text.strip().replace(" ", "")
            val = dd.text.strip()
            for label, pattern in items.items():
                if re.search(pattern, key):
                    results[label] = val

    all_results.append(results) 

driver.quit()

# Excel出力
df = pd.DataFrame(all_results)
out_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\分析\株式指標情報.xlsx"
df.to_excel(out_path, index=False)
os.startfile(out_path)
