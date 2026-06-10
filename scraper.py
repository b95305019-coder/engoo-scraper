import time
import requests
import xml.etree.ElementTree as ET
import re

# ── 設定 ──────────────────────────────────────────
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/astkw64ndn7wemprvbg9tjri3vwu8t7g"

# Engoo 設定
ENGOO_PAGE_SIZE = 2
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

# 國際新聞 RSS 設定（多個備用來源）
NEWS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.npr.org/1004/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
]
NEWS_COUNT = 2
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
        master_id = item.get("master_id", "")
        # Engoo 文章 URL（用 master_id 組成）
        url = f"https://engoo.com/app/daily-news/article/{master_id}" if master_id else "https://engoo.com/app/daily-news"
        articles.append({
            "source": "Engoo",
            "title": title,
            "content": f"Title: {title}\n\nIntroduction: {intro}",
            "url": url,
        })
        print(f"  ✓ {title}")
    return articles


def get_news_articles():
    """從多個 RSS 來源抓國際新聞，自動切換備用"""
    print(f"\n📡 抓取國際新聞（{NEWS_COUNT} 篇）...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    for feed_url in NEWS_FEEDS:
        try:
            domain = feed_url.split("//")[1].split("/")[0]
            source_name = domain.replace("feeds.", "").replace("rss.", "").split(".")[0].upper()
            print(f"  → 嘗試 {source_name}: {feed_url}")
            resp = requests.get(feed_url, headers=headers, timeout=15)
            print(f"     HTTP {resp.status_code}, {len(resp.content)} bytes")
            if resp.status_code != 200 or len(resp.content) < 2000:
                print("     ⚠️ 回應太小或狀態異常，跳過")
                continue
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:NEWS_COUNT]
            if not items:
                print("     ⚠️ 找不到文章，跳過")
                continue
            articles = []
            for item in items:
                title = item.findtext("title", "").strip()
                description = item.findtext("description", "").strip()
                description = re.sub(r"<[^>]+>", "", description).strip()
                url = item.findtext("link", "").strip()
                if title:
                    articles.append({
                        "source": source_name,
                        "title": title,
                        "content": f"Title: {title}\n\nSummary: {description}",
                        "url": url,
                    })
                    print(f"  ✓ {title[:60]}...")
            if articles:
                return articles
        except Exception as e:
            print(f"     ❌ 失敗：{e}")
            continue
    print("  ⚠️ 所有新聞來源都失敗了")
    return []


def send_to_make(article):
    """傳送文章到 Make Webhook"""
    payload = {
        "source": article["source"],
        "title": article["title"],
        "content": article["content"],
        "url": article.get("url", ""),
    }
    resp = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    print(f"    → Make: {resp.status_code}")
    resp.raise_for_status()


def main():
    print("=== 每日英文學習爬蟲啟動 ===")

    all_articles = []

    try:
        all_articles += get_engoo_articles()
    except Exception as e:
        print(f"  ⚠️ Engoo 抓取失敗：{e}")

    try:
        all_articles += get_news_articles()
    except Exception as e:
        import traceback
        print(f"  ⚠️ 新聞抓取失敗：{e}")
        print(traceback.format_exc())

    print(f"\n📤 共 {len(all_articles)} 篇文章，開始傳送到 Make...")

    for i, article in enumerate(all_articles, 1):
        print(f"\n  [{i}/{len(all_articles)}] [{article['source']}] {article['title'][:50]}...")
        print(f"     URL: {article.get('url', '無')}")
        try:
            send_to_make(article)
        except Exception as e:
            print(f"    ❌ 傳送失敗：{e}")
        if i < len(all_articles):
            time.sleep(75)

    print("\n=== 完成！===")


if __name__ == "__main__":
    main()
