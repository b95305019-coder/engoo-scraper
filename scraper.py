import time
import requests
import xml.etree.ElementTree as ET

# ── 設定 ──────────────────────────────────────────
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/astkw64ndn7wemprvbg9tjri3vwu8t7g"

# Engoo 設定
ENGOO_PAGE_SIZE = 2  # 每天抓 2 篇 Engoo
ENGOO_API = (
    "https://api.engoo.com/api/lesson_headers"
    "?category=0225ae09-5d63-41c2-bd75-693985d07d78"
    "&direction=desc"
    "&for_brand=5a4657f2-e151-4c48-9cce-000000000002"
    "&max_level=9&min_level=4"
    "&order=first_published_at"
    f"&page_size={ENGOO_PAGE_SIZE}"
    "&published_latest=true"
    "&type=Published"
    "&~v=631a9bce"
)

# Reuters via Google News RSS 設定
REUTERS_RSS = "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&ceid=US:en&hl=en-US&gl=US"
REUTERS_COUNT = 2  # 每天抓 2 篇 Reuters
# ─────────────────────────────────────────────────


def get_engoo_articles():
    """從 Engoo API 取得最新文章"""
    print(f"\n📰 抓取 Engoo 文章（{ENGOO_PAGE_SIZE} 篇）...")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(ENGOO_API, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    articles = []
    for item in data.get("data", []):
        title = item.get("title_text", {}).get("text", "")
        intro = item.get("introduction_text", {}).get("text", "")
        articles.append({
            "source": "Engoo",
            "title": title,
            "content": f"Title: {title}\n\nIntroduction: {intro}",
        })
        print(f"  ✓ {title}")
    return articles


def get_reuters_articles():
    """從 Google News RSS 抓 Reuters 最新新聞"""
    print(f"\n📡 抓取 Reuters 新聞（{REUTERS_COUNT} 篇）...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(REUTERS_RSS, headers=headers, timeout=15)
    resp.raise_for_status()

    # 解析 RSS XML
    root = ET.fromstring(resp.content)
    ns = {"media": "http://search.yahoo.com/mrss/"}

    articles = []
    items = root.findall(".//item")[:REUTERS_COUNT]

    for item in items:
        title = item.findtext("title", "").strip()
        description = item.findtext("description", "").strip()
        # 清除 HTML 標籤
        import re
        description = re.sub(r"<[^>]+>", "", description).strip()

        if title:
            articles.append({
                "source": "Reuters",
                "title": title,
                "content": f"Title: {title}\n\nSummary: {description}",
            })
            print(f"  ✓ {title[:60]}...")

    return articles


def send_to_make(article):
    """傳送文章到 Make Webhook"""
    payload = {
        "source": article["source"],
        "title": article["title"],
        "content": article["content"],
    }
    resp = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    print(f"    → Make: {resp.status_code}")
    resp.raise_for_status()


def main():
    print("=== 每日英文學習爬蟲啟動 ===")

    all_articles = []

    # 抓 Engoo 文章
    try:
        all_articles += get_engoo_articles()
    except Exception as e:
        print(f"  ⚠️ Engoo 抓取失敗：{e}")

    # 抓 Reuters 文章
    try:
        all_articles += get_reuters_articles()
    except Exception as e:
        print(f"  ⚠️ Reuters 抓取失敗：{e}")

    print(f"\n📤 共 {len(all_articles)} 篇文章，開始傳送到 Make...")

    for i, article in enumerate(all_articles, 1):
        print(f"\n  [{i}/{len(all_articles)}] [{article['source']}] {article['title'][:50]}...")
        try:
            send_to_make(article)
        except Exception as e:
            print(f"    ❌ 傳送失敗：{e}")
        if i < len(all_articles):
            time.sleep(35)  # 間隔 35 秒避免 Gemini rate limit

    print("\n=== 完成！===")


if __name__ == "__main__":
    main()
