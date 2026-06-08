import json
import requests

# ── 設定 ──────────────────────────────────────────
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/astkw64ndn7wemprvbg9tjri3vwu8t7g"
ENGOO_LIST_API = (
    "https://api.engoo.com/api/lesson_headers"
    "?category=0225ae09-5d63-41c2-bd75-693985d07d78"
    "&direction=desc"
    "&for_brand=5a4657f2-e151-4c48-9cce-000000000002"
    "&max_level=9&min_level=4"
    "&order=first_published_at"
    "&page_size=1"
    "&published_latest=true"
    "&type=Published"
    "&~v=631a9bce"
)
# ─────────────────────────────────────────────────


def get_latest_article():
    """從 Engoo API 取得最新一篇文章的標題與摘要"""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(ENGOO_LIST_API, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("data", [])
    if not items:
        raise ValueError("API 沒有回傳任何文章")

    article = items[0]
    title = article.get("title_text", {}).get("text", "")
    intro = article.get("introduction_text", {}).get("text", "")
    article_id = article.get("id", "")
    master_id = article.get("master_id", "")

    print(f"標題：{title}")
    print(f"摘要：{intro}")

    return {
        "title": title,
        "intro": intro,
        "id": article_id,
        "master_id": master_id,
    }


def send_to_make(article):
    """把文章資訊傳送到 Make Webhook"""
    payload = {
        "title": article["title"],
        "content": f"Title: {article['title']}\n\nIntroduction: {article['intro']}",
    }
    resp = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    print(f"Make 回應：{resp.status_code} {resp.text}")
    resp.raise_for_status()


def main():
    print("=== Engoo 爬蟲啟動 ===")

    print("1. 取得最新文章...")
    article = get_latest_article()

    print("2. 傳送到 Make Webhook...")
    send_to_make(article)

    print("=== 完成！===")


if __name__ == "__main__":
    main()
