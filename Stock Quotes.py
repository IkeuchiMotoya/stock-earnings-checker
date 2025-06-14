from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

# 対象の証券コード
ticker = "9984"
base_url = f"https://irbank.net/{ticker}"

# Selenium ドライバー初期化
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 通常の銘柄コードURLにアクセス
print(f"🔍 アクセス中: {base_url}")
driver.get(base_url)
time.sleep(3)

# ページHTMLを取得
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# Eコードを含むリンクを検索（形式: /Exxxxx）
e_href_tag = soup.find("a", href=re.compile(r"^/E\d+"))
if e_href_tag:
    e_path = e_href_tag["href"]
    e_code = e_path.strip("/")

    print(f"✅ Eコード取得成功: {e_code}")
    full_url = f"https://irbank.net/{e_code}"
    print(f"🌐 遷移先URL: {full_url}")

    # そのページに遷移して中身を確認
    driver.get(full_url)
    time.sleep(3)
    title = driver.title
    print(f"📄 ページタイトル: {title}")
else:
    print("❌ Eコードの取得に失敗しました")

driver.quit()
