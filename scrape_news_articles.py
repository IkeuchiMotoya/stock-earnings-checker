import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import pandas as pd
import os
import chardet

# ================================
# 🔧 設定
# ================================
DAYS_BACK = 3
JST = timezone(timedelta(hours=9))
END_DATE = datetime.now(JST)
START_DATE = END_DATE - timedelta(days=DAYS_BACK)

CSV_PATHS = [
    r'C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\保有銘柄\保有銘柄_信用.csv',
    r'C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\保有銘柄\保有銘柄_現物.csv'
]

OUTPUT_PATH = r'C:\Users\pumpk\OneDrive\デスクトップ\株式\kabutan_news_期間指定_統合版.xlsx'

# ================================
# 📥 ファイル読み込み（自動エンコーディング）
# ================================
def load_stock_csv(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")
    with open(filepath, 'rb') as f:
        encoding = chardet.detect(f.read())['encoding']
    df = pd.read_csv(filepath, encoding=encoding, dtype=str)
    df = df.rename(columns=lambda x: x.strip())
    return df[["コード", "銘柄名"]].dropna()

# ================================
# 📰 ニュース取得関数
# ================================
def fetch_news_in_range(stock_code, stock_name, start_date, end_date):
    url = f'https://kabutan.jp/stock/news?code={stock_code}'
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    news_rows = soup.select('table.s_news_list tr')
    collected_news = []

    for row in news_rows:
        time_td = row.find('td', class_='news_time')
        if not time_td:
            continue
        time_text = time_td.text.strip()
        try:
            news_date = datetime.strptime(time_text[:8], '%y/%m/%d').replace(tzinfo=JST)
        except ValueError:
            continue
        if start_date <= news_date <= end_date:
            title_td = row.find_all('td')[-1]
            a_tag = title_td.find('a')
            if a_tag:
                title = a_tag.text.strip()
                href = a_tag['href']
                link = href if href.startswith('http') else 'https://kabutan.jp' + href
                collected_news.append({
                    '銘柄コード': stock_code,
                    '銘柄名': stock_name,
                    '時間': time_text,
                    'タイトル': title,
                    'URL': link
                })
    return collected_news

# ================================
# 💾 Excel保存関数
# ================================
def save_to_excel(news_data, filepath):
    df = pd.DataFrame(news_data)
    df.to_excel(filepath, index=False)
    os.startfile(filepath)

# ================================
# 🔁 メイン処理
# ================================
def main():
    all_news = []

    for path in CSV_PATHS:
        try:
            stock_df = load_stock_csv(path)
        except Exception as e:
            print(f"❌ ファイル読み込みエラー：{path} → {e}")
            continue

        for _, row in stock_df.iterrows():
            code = row["コード"].zfill(4)
            name = row["銘柄名"]
            try:
                news = fetch_news_in_range(code, name, START_DATE, END_DATE)
                all_news.extend(news)
            except Exception as e:
                print(f"[{code}] {name} の取得失敗: {e}")

    if all_news:
        save_to_excel(all_news, OUTPUT_PATH)
        print(f"✅ {len(all_news)} 件のニュースをExcelに保存しました。")
    else:
        print("🔍 指定期間に該当するニュースはありません。")

if __name__ == '__main__':
    main()
