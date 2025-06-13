import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

def fetch_today_news_from_kabutan(stock_code):
    # 今日の日付を "yy/mm/dd" 形式で取得
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
                url = href if href.startswith('http') else 'https://kabutan.jp' + href
                time_text = time_td.text.strip()
                today_news.append({'time': time_text, 'title': title, 'url': url})

    return today_news

# 使用例
if __name__ == '__main__':
    stock_code = '3350'
    news_list = fetch_today_news_from_kabutan(stock_code)
    print(f"【{stock_code} の今日のニュース】")
    for news in news_list:
        print(f"- {news['time']} | {news['title']} | {news['url']}")
