import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import pandas as pd
import os

# ================================
# 🔧 設定（取得期間の定数）
# ================================
DAYS_BACK = 7  # ← ここを変更すれば対象期間を簡単に変更可能
JST = timezone(timedelta(hours=9))
END_DATE = datetime.now(JST)
START_DATE = END_DATE - timedelta(days=DAYS_BACK)

# ================================
# 📰 ニュース取得関数（期間指定）
# ================================
def fetch_news_in_range(stock_code, start_date, end_date):
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
                    '銘柄名': "",
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
if __name__ == '__main__':
    csv_path = r'C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\保有銘柄\保有銘柄.csv'
    stock_df = pd.read_csv(csv_path, dtype=str)
    stock_list = stock_df.to_dict('records')

    all_news = []

    for stock in stock_list:
        code = str(stock['銘柄コード'])
        name = stock['銘柄名']
        news = fetch_news_in_range(code, START_DATE, END_DATE)
        for n in news:
            n['銘柄名'] = name
        all_news.extend(news)

    if all_news:
        output_path = r'C:\Users\pumpk\OneDrive\デスクトップ\株式\kabutan_news_期間指定.xlsx'
        save_to_excel(all_news, output_path)
        print(f"{len(all_news)} 件のニュースをExcelに保存しました。")
    else:
        print("指定期間に該当するニュースはありません。")
