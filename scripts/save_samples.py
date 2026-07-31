"""Save HTML samples for parser development."""
import urllib.request
from pathlib import Path

USER_AGENT = "este_analystics/1.0 (research; github.com/jim-auto/este_analystics)"
OUT = Path(__file__).resolve().parent.parent / "data" / "samples"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    urls = {
        "kanto_shoplist.html": "https://estama.jp/kanto/shoplist/",
        "kanto_ranking.html": "https://estama.jp/kanto/ranking/",
        "kanto_couponlist.html": "https://estama.jp/kanto/couponlist/",
        "kansai_shoplist.html": "https://estama.jp/kansai/shoplist/",
        "chubu_shoplist.html": "https://estama.jp/chubu/shoplist/",
        "shop_detail.html": "https://estama.jp/shop/43984/",
    }
    for name, url in urls.items():
        html = fetch(url)
        (OUT / name).write_text(html, encoding="utf-8")
        print(name, len(html))


if __name__ == "__main__":
    main()
