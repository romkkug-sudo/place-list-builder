"""一覧ページから「名称・エリア・詳細URL」を収集する。

対象サイトごとに、下の「設定」部分を書き換えて使う。
※ 利用前に、対象サイトの利用規約でデータ収集が禁止されていないことを必ず確認すること。
"""
import time
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ==============================
# 設定（対象サイトに合わせて変更）
# ==============================
BASE_URL = "https://example.com/area/osaka/"   # 一覧ページの1ページ目
PAGE_URL_FORMAT = "{base}p{page}/"              # 2ページ目以降のURL形式
CATEGORY = "大阪エリア"                          # 出力CSVの「カテゴリ」列に入れる値

SELECTORS = {
    "card": ("div", "p-jobCard"),                        # 1件分の枠
    "name": ("h3", "p-jobCard__headerOfficeName"),       # 名称
    "area": ("span", "p-jobCard__infoAddress"),          # エリア（住所）
    "link": ("a", "p-jobCard__header"),                  # 詳細ページへのリンク
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; place-list-builder)"}
REQUEST_INTERVAL = 1.0   # サイトへの負荷を抑えるため、1ページごとに待つ秒数


def is_allowed(url: str) -> bool:
    """robots.txt でクローリングが許可されているか確認する。"""
    parsed = urlparse(url)
    rp = robotparser.RobotFileParser()
    rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        return True  # robots.txt が取得できない場合は許可とみなす
    return rp.can_fetch(HEADERS["User-Agent"], url)


def _text(card, key: str) -> str:
    tag, cls = SELECTORS[key]
    found = card.find(tag, class_=cls)
    return found.get_text(strip=True) if found else ""


def scrape(max_pages: int = 50) -> list[list[str]]:
    """一覧ページを順に取得し、[名称, エリア, URL, カテゴリ] のリストを返す。"""
    if not is_allowed(BASE_URL):
        print("robots.txt で許可されていないため、処理を中止します。")
        return []

    rows = []
    for page in range(1, max_pages + 1):
        url = BASE_URL if page == 1 else PAGE_URL_FORMAT.format(base=BASE_URL, page=page)
        print(f"取得中: {page}ページ目")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
        except requests.RequestException as e:
            print(f"通信エラーのため終了します: {e}")
            break
        if response.status_code != 200:
            print(f"ステータス {response.status_code} のため終了します")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        tag, cls = SELECTORS["card"]
        cards = soup.find_all(tag, class_=cls)
        if not cards:
            print("これ以上データがないため終了します")
            break

        for card in cards:
            link_tag, link_cls = SELECTORS["link"]
            link = card.find(link_tag, class_=link_cls)
            detail_url = urljoin(BASE_URL, link["href"]) if link and link.get("href") else ""
            rows.append([_text(card, "name"), _text(card, "area"), detail_url, CATEGORY])

        time.sleep(REQUEST_INTERVAL)

    print(f"収集件数: {len(rows)}件")
    return rows
