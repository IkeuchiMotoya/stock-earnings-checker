import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os

#決算発表予定銘柄をcsv出力する
# ========================
# 🔧 設定
# ========================
START_DATE = "2025-06-12"
NUM_DAYS = 7
SAVE_DIR = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\決算発表後の反応"

# ========================
# 📥 データ取得関数
# ========================
def fetch_irbank_codes(date_str):
    url = f"https://irbank.net/market/kessan?y={date_str}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"id": "code1"})
    if not table:
        return None
    rows = table.find_all("tr")[1:]

    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 1:
            code = cols[0].text.strip()
            if code:
                data.append({"銘柄コード": code, "決算日": date_str})
    return pd.DataFrame(data) if data else None

# ========================
# 🔁 1週間分処理ループ
# ========================
start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
for i in range(NUM_DAYS):
    target_date = start_date + timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    df = fetch_irbank_codes(date_str)
    if df is not None and not df.empty:
        file_name = f"決算発表予定_{date_str}.csv"
        output_path = os.path.join(SAVE_DIR, file_name)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ {file_name} を保存しました。")
    else:
        print(f"🔍 {date_str} はデータなし → スキップ")
