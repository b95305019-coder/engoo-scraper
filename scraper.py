import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── 設定 ──────────────────────────────────────────
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/astkw64ndn7wemprvbg9tjri3vwu8t7g"
ENGOO_LIST_API = (
    "https://api.engoo.com/api/lesson_headers"
    "?category=0225ae09-5d63-41c2-bd75-693985d07d78"
    "&direction=desc"
    "&for_brand=5a4657f2-e151-4c48-9cce-000000000002"
    "&max_level=9&min_level=4"
    "&order=first_published_at"
    "&page_size=3"
    "&published_latest=true"
    "&type=Published"
    "&~v=631a9bce"
)
# ─────────────────────────────────────────────────


def get_latest_article_url():
    """從 Engoo API 取得最新一篇文章的 slug"""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(ENGOO_LIST_API, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # 取第一篇（最新）
    items = data.get("data") or data.get("items") or data
    if isinstance(items, list) and len(items) > 0:
        first = items[0]
        # 嘗試常見欄位名稱
        slug = (first.get("slug")
                or first.get("path")
                or first.get("url_slug")
                or first.get("id"))
        if slug:
            return f"https://engoo.com/app/daily-news/article/{slug}", first
    raise ValueError(f"找不到文章 slug，API 回傳：{json.dumps(data)[:300]}")


def scrape_article(url):
    """用 Selenium 抓取 Engoo 文章內文"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    try:
        print(f"開啟頁面：{url}")
        driver.get(url)

        # 等待文章內文載入（最多 20 秒）
        wait = WebDriverWait(driver, 20)

        # Engoo 文章內文通常在 .article-body 或 .lesson-content
        selectors = [
            ".article-body",
            ".lesson-content",
            "[class*='article']",
            "[class*='content']",
            "article",
            "main",
        ]

        content_el = None
        for sel in selectors:
            try:
                content_el = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                text = content_el.text.strip()
                if len(text) > 200:  # 確認有足夠內容
                    print(f"找到內容（selector: {sel}），長度：{len(text)}")
                    break
            except Exception:
                continue

        if not content_el or len(content_el.text.strip()) < 200:
            # 備用：抓整個 body
            time.sleep(5)
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"備用方案：body 文字長度 {len(body_text)}")
            return body_text

        return content_el.text.strip()

    finally:
        driver.quit()


def send_to_make(article_url, article_text):
    """把文章內文傳送到 Make Webhook"""
    payload = {
        "url": article_url,
        "content": article_text,
    }
    resp = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    print(f"Make 回應：{resp.status_code} {resp.text}")
    resp.raise_for_status()


def main():
    print("=== Engoo 爬蟲啟動 ===")

    # 1. 取得最新文章 URL
    print("1. 取得最新文章連結...")
    article_url, meta = get_latest_article_url()
    print(f"   文章 URL：{article_url}")

    # 2. 爬取文章內文
    print("2. 爬取文章內文...")
    article_text = scrape_article(article_url)
    print(f"   內文長度：{len(article_text)} 字元")
    print(f"   內文預覽：{article_text[:100]}...")

    # 3. 傳送到 Make
    print("3. 傳送到 Make Webhook...")
    send_to_make(article_url, article_text)

    print("=== 完成！===")


if __name__ == "__main__":
    main()
