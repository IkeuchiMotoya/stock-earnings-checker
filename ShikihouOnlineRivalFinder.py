from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time

def get_competitor_codes_and_names(stock_code):
    url = f"https://shikiho.toyokeizai.net/stocks/{stock_code}#rivals"
    print(f"[INFO] アクセス中: {url}")

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # 表示必要な場合はOFF
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    results = []

    # 競合テーブルの企業名欄のaタグを探す
    for a in soup.select("div.company-name-inner a[href^='/stocks/']"):
        href = a["href"]
        name = a.get_text(strip=True)
        match = re.search(r"/stocks/(\d+)", href)
        if match:
            scode = match.group(1)
            results.append({"銘柄コード": scode, "銘柄名": name})
            print(f"[INFO] 取得: {scode} {name}")

    return results

# === 実行 ===
if __name__ == "__main__":
    rivals = get_competitor_codes_and_names("2975")

    print("\n=== 銘柄コード＋銘柄名 一覧 ===")
    for item in rivals:
        print(f"{item['銘柄コード']},{item['銘柄名']}")
