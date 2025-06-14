from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import io

# 上部に追加：取得したい年数をここで切り替え可能
NUM_YEARS = 2  # ← ここを5にすれば直近5年になる

# CSVから銘柄コード＋銘柄名を読み込む
csv_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\通期業績の推移\検索銘柄.csv"
ticker_df = pd.read_csv(csv_path, dtype={"銘柄コード": str})
ticker_list = ticker_df["銘柄コード"].tolist()
code_name_map = dict(zip(ticker_df["銘柄コード"], ticker_df["銘柄名"]))

options = webdriver.ChromeOptions()
options.add_argument('--headless')
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

    df_act = df[df[period_col].astype(str).str.contains(r"通期.*実績", na=False)].reset_index(drop=True)
    if df_act.empty:
        print(f"[{ticker}] 通期実績が見つかりません → スキップ")
        continue

    # 年度で並び替えて直近NUM_YEARS年に限定
    df_act = df_act.sort_values("年度", ascending=True).tail(NUM_YEARS).reset_index(drop=True)
    print(f"[{ticker}] 年度絞り込み後の行数: {len(df_act)}")

    # 当期純利益列の名前統一（存在する方を使う）
    profit_col = next((name for name in ["当期純利益", "当期利益"] if name in df_act.columns), None)

    for col in ["売上高", "営業利益", "経常利益"]:
        if col in df_act.columns:
            df_act[col] = pd.to_numeric(
                df_act[col].astype(str)
                .str.replace(",", "")
                .str.replace("▲", "-")
                .str.replace("*", "")
                .str.replace("＊", "")
                .str.strip(),
                errors="coerce"
            )
        else:
            df_act[col] = float("nan")
            print(f"[{ticker}] 注意：列 '{col}' が欠落していました")

    if profit_col:
        df_act["当期純利益"] = pd.to_numeric(
            df_act[profit_col].astype(str)
            .str.replace(",", "")
            .str.replace("▲", "-")
            .str.replace("*", "")
            .str.replace("＊", "")
            .str.strip(),
            errors="coerce"
        )
    else:
        df_act["当期純利益"] = float("nan")
        print(f"[{ticker}] 注意：当期純利益に該当する列が見つかりません")

    for base, ratio in [("売上高", "売上高比率"),
                        ("営業利益", "営業利益比率"),
                        ("経常利益", "経常利益比率"),
                        ("当期純利益", "当期純利益比率")]:
        df_act[ratio] = df_act[base].pct_change().apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "")

    # 銘柄コードと銘柄名を付加
    df_act["銘柄コード"] = ticker
    df_act["銘柄名"] = code_name_map.get(ticker, "")

    # 出力列の順番（銘柄名を銘柄コードの直後に）
    output_cols = ["銘柄コード", "銘柄名", "年度", "提出日", "売上高", "売上高比率",
                   "営業利益", "営業利益比率", "経常利益", "経常利益比率",
                   "当期純利益", "当期純利益比率"]
    present_cols = [c for c in output_cols if c in df_act.columns]
    print(f"[{ticker}] 出力列：{present_cols}")
    all_data.append(df_act[present_cols])

driver.quit()

if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    print("\n✅ 最終出力行数:", len(final_df))
    out = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\通期業績_検索銘柄_銘柄名付き.xlsx"
    final_df.to_excel(out, index=False)
    os.startfile(out)
else:
    print("❌ すべての銘柄でデータ取得に失敗しました")
