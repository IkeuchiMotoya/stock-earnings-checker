from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import io

#通期業績の推移を取得するプログラム
# 上部に追加：取得したい年数をここで切り替え可能
NUM_YEARS = 3

# CSVから銘柄コード＋銘柄名を読み込む
csv_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\通期業績の推移、指標の取得\検索銘柄.csv"
ticker_df = pd.read_csv(csv_path, dtype={"銘柄コード": str})
ticker_list = ticker_df["銘柄コード"].tolist()
code_name_map = dict(zip(ticker_df["銘柄コード"], ticker_df["銘柄名"]))

# ブラウザ設定
options = webdriver.ChromeOptions()
# options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
all_data = []

for ticker in ticker_list:
    print(f"\n=== 銘柄 {ticker} の処理開始 ===")
    driver.get(f"https://irbank.net/{ticker}/pl")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table")
    if table is None:
        print(f"[{ticker}] テーブルが見つかりません")
        continue

    df = pd.read_html(io.StringIO(str(table)), header=0)[0]
    df.columns = [re.sub(r"#.*", "", col).strip() for col in df.columns]
    print(f"[{ticker}] 正規化後の列名: {df.columns.tolist()}")

    period_col = next((col for col in df.columns if re.search(r"四半期|決算期", col)), None)
    if period_col is None or "年度" not in df.columns:
        print(f"[{ticker}] '通期 実績'用列 or '年度'がありません → スキップ")
        continue

    # 通期 実績のみ抽出
    df_act = df[df[period_col].astype(str).str.contains(r"通期.*実績", na=False)].copy()
    df_act = df_act.sort_values("年度", ascending=True).tail(NUM_YEARS).reset_index(drop=True)

    # 通期予想の最新のみ抽出
    df_pred = df[df[period_col].astype(str).str.contains(r"通期.*予想", na=False)].copy()
    if not df_pred.empty and "年度" in df_pred.columns:
        latest_year = df_pred["年度"].max()
        df_pred = df_pred[df_pred["年度"] == latest_year].reset_index(drop=True)
    else:
        df_pred = pd.DataFrame()

    # 結合
    df_combined = pd.concat([df_act, df_pred], ignore_index=True)

    if df_combined.empty:
        print(f"[{ticker}] データが取得できません → スキップ")
        continue

    # 利益列の統一
    profit_col = next((name for name in ["当期純利益", "当期利益"] if name in df_combined.columns), None)
    for col in ["売上高", "営業利益", "経常利益"]:
        if col in df_combined.columns:
            df_combined[col] = pd.to_numeric(
                df_combined[col].astype(str).str.replace(",", "").str.replace("▲", "-").str.replace("*", "").str.replace("＊", "").str.strip(),
                errors="coerce"
            )
        else:
            df_combined[col] = float("nan")
            print(f"[{ticker}] 注意：列 '{col}' が欠落していました")

    if profit_col:
        df_combined["当期純利益"] = pd.to_numeric(
            df_combined[profit_col].astype(str).str.replace(",", "").str.replace("▲", "-").str.replace("*", "").str.replace("＊", "").str.strip(),
            errors="coerce"
        )
    else:
        df_combined["当期純利益"] = float("nan")
        print(f"[{ticker}] 注意：当期純利益に該当する列が見つかりません")

    # 前年比計算
    for base, ratio in [("売上高", "売上高比率"), ("営業利益", "営業利益比率"), ("経常利益", "経常利益比率"), ("当期純利益", "当期純利益比率")]:
        df_combined[ratio] = df_combined[base].pct_change().apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "")

    # 銘柄コード・銘柄名を追加
    df_combined["銘柄コード"] = ticker
    df_combined["銘柄名"] = code_name_map.get(ticker, "")

    output_cols = ["銘柄コード", "銘柄名", "年度", "提出日", "売上高", "売上高比率",
                   "営業利益", "営業利益比率", "経常利益", "経常利益比率",
                   "当期純利益", "当期純利益比率"]
    present_cols = [c for c in output_cols if c in df_combined.columns]
    print(f"[{ticker}] 出力列：{present_cols}")
    all_data.append(df_combined[present_cols])

driver.quit()

# 出力
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    print("\n✅ 最終出力行数:", len(final_df))
    out = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\分析\通期業績_検索銘柄_予想込み.xlsx"
    final_df.to_excel(out, index=False)
    os.startfile(out)
else:
    print("❌ すべての銘柄でデータ取得に失敗しました")
