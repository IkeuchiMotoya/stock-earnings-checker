import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import pandas as pd
import os

def fetch_today_news(stock_code):
    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).strftime('%y/%m/%d')

    url = f'https://kabutan.jp/stock/news?code={stock_code}'
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    news_rows = soup.select('table.s_news_list tr')
    today_news = []

    for row in news_rows:
        time_td = row.find('td', class_='news_time')
        if time_td and today in time_td.text:
            title_td = row.find_all('td')[-1]
            a_tag = title_td.find('a')
            if a_tag:
                title = a_tag.text.strip()
                href = a_tag['href']
                link = href if href.startswith('http') else 'https://kabutan.jp' + href
                time_text = time_td.text.strip()
                today_news.append({
                    '銘柄コード': stock_code,
                    '時間': time_text,
                    'タイトル': title,
                    'URL': link
                })

    return today_news

def save_to_excel(news_data, filepath):
    df = pd.DataFrame(news_data)
    df.to_excel(filepath, index=False)
    os.startfile(filepath)

if __name__ == '__main__':
    stock_codes = ['7203', '3350', '9984']  # ← 複数銘柄（トヨタ・ソニー・ソフトバンクなど）
    all_news = []

    for code in stock_codes:
        news = fetch_today_news(code)
        all_news.extend(news)

    if all_news:
        output_path = r'C:\Users\pumpk\OneDrive\デスクトップ\株式\kabutan_all_news.xlsx'
        save_to_excel(all_news, output_path)
        print(f"{len(all_news)} 件のニュースをExcelに保存しました。")
    else:
        print("本日該当するニュースはありません。")
