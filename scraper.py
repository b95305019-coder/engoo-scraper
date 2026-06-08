import time
import requests

# ── 設定 ──────────────────────────────────────────
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/astkw64ndn7wemprvbg9tjri3vwu8t7g"
PAGE_SIZE = 4  # 每天抓幾篇
ENGOO_LIST_API = (
    "https://api.engoo.com/api/lesson_headers"
    "?category=0225ae09-5d63-41c2-bd75-693985d07d78"
    "&direction=desc"
    "&for_brand=5a4657f2-e151-4c48-9cce-000000000002"
    "&max_level=9&min_level=4"
    "&order=first_published_at"
    f"&page_size={PAGE_SIZE}"
    "&published_latest=true"
    "&type=Published"
    "&~v=631a9bce"
)
# ─────────────────────────────────────────────────


def get_latest_articles():
    """從 Engoo API 取得最新文章列表"""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(ENGOO_LIST_API, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("data", [])
    if not items:
        raise ValueError("API 沒有回傳任何文章")

    articles = []
    for item in items:
        title = item.get("title_text", {}).get("text", "")
        intro = item.get("introduction_text", {}).get("text", "")
        articles.append({
            "title": title,
            "intro": intro,
            "id": item.get("id", ""),
        })
        print(f"  - {title}")

    return articles


def send_to_make(article):
    """把文章資訊傳送到 Make Webhook"""
    payload = {
        "title": article["title"],
        "content": f"Title: {article['title']}\n\nIntroduction: {article['intro']}",
    }
    resp = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    print(f"    Make 回應：{resp.status_code} {resp.text}")
    resp.raise_for_status()


def main():
    print("=== Engoo 爬蟲啟動 ===")

    print(f"1. 取得最新 {PAGE_SIZE} 篇文章...")
    articles = get_latest_articles()

    print(f"2. 逐篇傳送到 Make Webhook（共 {len(articles)} 篇）...")
    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{len(articles)}] {article['title']}")
        send_to_make(article)
        if i < len(articles):
            time.sleep(3)  # 每篇間隔 3 秒，避免太快

    print("=== 完成！===")


if __name__ == "__main__":
    main()
