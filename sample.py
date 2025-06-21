import yfinance as yf
import pandas as pd
import csv
import os
import re
from datetime import datetime, timedelta

# 📥 CSVパス
import_path = r'C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\決算発表後の反応\決算発表予定_2025-06-16.csv'

# 📤 出力用日付（1行目の決算日をそのまま使う）
with open(import_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    if not rows:
        raise ValueError("CSVが空です")
    date_str = rows[0]['決算日']  # 変換なし

# データ読み込み
tickers = []
earnings_dates = {}
for row in rows:
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
    start = edate - timedelta(days=5)
    end = edate + timedelta(days=5)

    try:
        data = yf.download(ticker, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        print(f"\n=== {ticker} の株価データ（{start.strftime('%Y-%m-%d')} ～ {end.strftime('%Y-%m-%d')}） ===")
        print(data)

        if 'Close' not in data.columns or data.empty:
            print(f"{ticker} のデータが取得できませんでした。")
            continue

        pre_data = data[data.index <= edate]
        post_data = data[data.index > edate]

        print(f"\n【{ticker}】決算日：{edate.strftime('%Y-%m-%d')}")
        print("▼ 決算前のデータ（pre_data）:")
        print(pre_data)
        print("▼ 決算後のデータ（post_data）:")
        print(post_data)

        if len(pre_data) == 0 or len(post_data) == 0:
            print(f"{ticker} は前後の株価データが不足しています。")
            continue

        pre_close = float(pre_data['Close'].iloc[-1])
        post_close = float(post_data['Close'].iloc[0])
        print(f"▼ pre_close: {pre_close}, post_close: {post_close}")
        change = (post_close - pre_close) / pre_close * 100
        print(f"{ticker} の株価変化率：{round(change, 2)}%")

        results.append({
            '銘柄コード': ticker.replace('.T', ''),
            '決算日': earnings_dates[ticker],
            'Price Change (%)': round(change, 2)
        })

    except Exception as e:
        print(f"{ticker} の処理中にエラーが発生しました: {e}")

# 結果表示（5%以上変動）
df = pd.DataFrame(results)
df['Price Change (%)'] = pd.to_numeric(df['Price Change (%)'], errors='coerce')
df_filtered = df[df['Price Change (%)'] >= 5]

print("\n決算後に5%以上株価が変動した銘柄：")
print(df_filtered)

# 保存
export_path = fr'C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvエクスポート\決算発表後反応銘柄\決算反応銘柄{date_str}.csv'
df_filtered.to_csv(export_path, index=False, encoding='utf-8-sig')
print(f"✅ 出力完了: {export_path}")
