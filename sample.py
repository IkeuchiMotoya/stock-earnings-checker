import yfinance as yf
import pandas as pd
import csv
import os
import re


from datetime import datetime, timedelta

# # 対象の銘柄リスト（東証銘柄は .T を付ける）
# tickers = ['135A.T']

# # 仮の決算日データ（実際はスクレイピング等で自動取得も可）
# earnings_dates = {
#     '135A.T': '2025-04-14'
# }

#決算後に反応があった銘柄選出するプログラム
# 読み込むCSVファイルのパス
import_path = r'C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\決算発表後の反応\決算予定_20250612.csv'

# 日付部分（例: 20250606）を抽出
filename = os.path.basename(import_path)
match = re.search(r'_(\d{8})', filename)
date_str = match.group(1) if match else datetime.now().strftime('%Y%m%d')  # 抽出失敗時は今日の日付


# CSVから銘柄コードと決算日を読み込む
tickers = []
earnings_dates = {}
with open(import_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ticker_code = row['銘柄コード'].strip() + '.T'
        tickers.append(ticker_code)
        earnings_dates[ticker_code] = row['決算日']

# 結果格納用
results = []

for ticker in tickers:
    if ticker not in earnings_dates:
        print(f"{ticker} の決算日が未登録です。")
        continue

    edate = datetime.strptime(earnings_dates[ticker], "%Y-%m-%d")
    print("edate")
    print(edate)
    start = edate - timedelta(days=5)
    end = edate + timedelta(days=5)
    # print(f"{ticker} の取得対象期間：{start.strftime('%Y-%m-%d')} ～ {end.strftime('%Y-%m-%d')}")

    try:
        # 株価データ取得
        data = yf.download(ticker, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        print(f"\n=== {ticker} の株価データ（{start.strftime('%Y-%m-%d')} ～ {end.strftime('%Y-%m-%d')}） ===")
        print(data)

        # Close列があるか確認
        if 'Close' not in data.columns or data.empty:
            print(f"{ticker} のデータが取得できませんでした。")
            continue

        # 日付で分けて前後の株価を抽出
        pre_data = data[data.index <= edate]
        post_data = data[data.index > edate]
        # print(f"\n【{ticker}】決算日：{edate.strftime('%Y-%m-%d')}")
        # print("▼ 決算前のデータ（pre_data）:")
        # print(pre_data)
        # print("▼ 決算前のデータ（post_data）:")
        # print(post_data)


        if len(pre_data) == 0 or len(post_data) == 0:
            print(f"{ticker} は前後の株価データが不足しています。")
            continue

        pre_close = float(pre_data['Close'].iloc[-1])
        post_close = float(post_data['Close'].iloc[0])
        # print("▼ pre_close:post_close")
        # print(pre_close)
        # print(post_close)
        change = (post_close - pre_close) / pre_close * 100
        # print(f"{ticker} の株価変化率：{round(change, 2)}%")

        results.append({
            '銘柄コード': ticker,
            '決算日': earnings_dates[ticker],
            'Price Change (%)': round(change, 2)
        })

    except Exception as e:
        print(f"{ticker} の処理中にエラーが発生しました: {e}")

# 結果を表示（5%以上動いた銘柄のみ）
df = pd.DataFrame(results)


df['Price Change (%)'] = pd.to_numeric(df['Price Change (%)'], errors='coerce')
df_filtered = df[df['Price Change (%)'] >= 5]
df_filtered['銘柄コード'] = df_filtered['銘柄コード'].str.replace('.T', '', regex=False)

print("\n決算後に5%以上株価が変動した銘柄：")
print(df_filtered)
export_path = fr'C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvエクスポート\決算発表後反応銘柄\決算反応銘柄_{date_str}.csv'
df_filtered.to_csv(export_path, index=False, encoding='utf-8-sig')
