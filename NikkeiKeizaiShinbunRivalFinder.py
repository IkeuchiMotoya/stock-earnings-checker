import csv
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_competitor_links_below_same_industry(scode):
    url = f"https://www.nikkei.com/nkd/company/?scode={scode}"
    print(f"[INFO] アクセス中: {url}")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 必要に応じて可視化
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    same_link = soup.find("a", href=re.compile(r"/markets/kabu/stkcomp/\?scode="))
    if not same_link:
        print("[WARN] '同業他社リンク' が見つかりませんでした")
        return []

    container = same_link.find_parent().find_next_sibling()
    if not container:
        print("[WARN] 同業他社リンクの下に企業リンク群が見つかりませんでした")
        return []

    links = container.find_all("a", href=True)
    competitors = []
    for link in links:
        name = link.get_text(strip=True)
        href = link["href"]
        match = re.search(r"scode=(\d+)", href)
        if match and name:
            scode_extracted = match.group(1)
            competitors.append({"銘柄コード": scode_extracted, "銘柄名": name})
            print(f"[INFO] 登録: {name} ({scode_extracted})")

    return competitors

def write_to_csv(data, filepath):
    with open(filepath, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["銘柄コード", "銘柄名"])
        writer.writeheader()
        writer.writerows(data)
    print(f"[INFO] 書き込み完了: {filepath}")

# === 実行 ===
if __name__ == "__main__":
    target_scode = "3135"  # 任意の銘柄コード
    competitors = get_competitor_links_below_same_industry(target_scode)

    output_path = r"C:\Users\pumpk\OneDrive\デスクトップ\株式\csv\csvインポート\通期業績の推移、指標の取得\検索銘柄.csv"
    write_to_csv(competitors, output_path)
