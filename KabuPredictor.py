from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import io

#通期業績の推移取得


NUM_YEARS = 2 #通期の実績を取得する年数
csv_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\通期業績の推移、指標の取得\検索銘柄.csv"
ticker_df = pd.read_csv(csv_path, dtype={"銘柄コード": str})
ticker_list = ticker_df["銘柄コード"].tolist()
code_name_map = dict(zip(ticker_df["銘柄コード"], ticker_df["銘柄名"]))

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
all_data = []

for ticker in ticker_list:
    print(f"\n=== 銘柄 {ticker} の処理開始 ===")
    driver.get(f"https://irbank.net/{ticker}/pl")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table")
    if table is None:
        print(f"[{ticker}] テーブルが見つかりません → スキップ")
        continue

    df = pd.read_html(io.StringIO(str(table)), header=0)[0]
    df.columns = [re.sub(r"#.*", "", col).strip() for col in df.columns]
    period_col = next((col for col in df.columns if re.search(r"四半期|決算期", col)), None)
    if period_col is None or "年度" not in df.columns:
        print(f"[{ticker}] '通期 実績'用列 or '年度'がありません → スキップ")
        continue

    # 実績（過去NUM_YEARS分）
    df_act = df[df[period_col].astype(str).str.contains(r"通期.*実績", na=False)].copy()
    df_act["年度数値"] = df_act["年度"].str.extract(r"(\d{4})").astype(float)
    df_act = df_act.sort_values("年度数値", ascending=True).tail(NUM_YEARS)
    df_act = df_act.drop(columns=["年度数値"]).reset_index(drop=True)

    # 来期予想抽出（修正が優先）
    df_pred = pd.DataFrame()
    df_forecast = df[df[period_col].astype(str).str.contains(r"通期.*予想", na=False)].copy()
    df_revision = df[df[period_col].astype(str).str.contains(r"通期.*修正", na=False)].copy()
    df_latest_actual = df_act["年度"].str.extract(r"(\d{4})").astype(float).max().values[0] if not df_act.empty else 0

    def extract_next_year(df_):
        df_["年度数値"] = df_["年度"].str.extract(r"(\d{4})").astype(float)
        df_next = df_[df_["年度数値"] > df_latest_actual]
        if not df_next.empty:
            return df_next.sort_values("年度数値").head(1).drop(columns=["年度数値"])
        return pd.DataFrame()

    if not df_revision.empty:
        df_pred = extract_next_year(df_revision)
    if df_pred.empty and not df_forecast.empty:
        df_pred = extract_next_year(df_forecast)

    df_combined = pd.concat([df_act, df_pred], ignore_index=True)

    if df_combined.empty:
        print(f"[{ticker}] データが取得できません → スキップ")
        continue

    # 売上高カラムの名称に柔軟対応
    sales_col = next((col for col in ["売上高", "営業収益", "売上収益"] if col in df_combined.columns), None)
    if sales_col:
        df_combined["売上高"] = pd.to_numeric(
            df_combined[sales_col].astype(str).str.replace(",", "").str.replace("▲", "-").str.strip(),
            errors="coerce"
        )
    else:
        df_combined["売上高"] = float("nan")

    # 他の数値変換
    profit_col = next((name for name in ["当期純利益", "当期利益"] if name in df_combined.columns), None)
    for col in ["営業利益", "経常利益"]:
        if col in df_combined.columns:
            df_combined[col] = pd.to_numeric(
                df_combined[col].astype(str).str.replace(",", "").str.replace("▲", "-").str.strip(),
                errors="coerce"
            )
        else:
            df_combined[col] = float("nan")

    if profit_col:
        df_combined["当期純利益"] = pd.to_numeric(
            df_combined[profit_col].astype(str).str.replace(",", "").str.replace("▲", "-").str.strip(),
            errors="coerce"
        )
    else:
        df_combined["当期純利益"] = float("nan")

    # 比率計算
    for base, ratio in [("売上高", "売上高比率"), ("営業利益", "営業利益比率"),
                        ("経常利益", "経常利益比率"), ("当期純利益", "当期純利益比率")]:
        df_combined[ratio] = ""
        for i in range(1, len(df_combined)):
            prev, curr = df_combined.loc[i - 1, base], df_combined.loc[i, base]
            if pd.notna(prev) and prev != 0 and pd.notna(curr):
                df_combined.loc[i, ratio] = f"{(curr - prev) / prev * 100:.1f}%"

    df_combined["銘柄コード"] = ticker
    df_combined["銘柄名"] = code_name_map.get(ticker, "")

    output_cols = ["銘柄コード", "銘柄名", "年度", "提出日", "売上高", "売上高比率",
                   "営業利益", "営業利益比率", "経常利益", "経常利益比率",
                   "当期純利益", "当期純利益比率"]
    present_cols = [c for c in output_cols if c in df_combined.columns]
    all_data.append(df_combined[present_cols])

driver.quit()

if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    out = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\分析\通期業績_検索銘柄_予想込み_完全版.xlsx"
    final_df.to_excel(out, index=False)
    os.startfile(out)
else:
    print("❌ すべての銘柄でデータ取得に失敗しました")
