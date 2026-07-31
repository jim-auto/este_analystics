"""Temporary probe script for HTML structure."""
import re
import urllib.request

USER_AGENT = "este_analystics/1.0 (research; github.com/jim-auto/este_analystics)"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def probe_shoplist(region: str) -> None:
    url = f"https://estama.jp/{region}/shoplist/"
    html = fetch(url)
    print("===", url, "len", len(html))
    shop_ids = re.findall(r"/shop/(\d+)/", html)
    print("shop ids unique", len(set(shop_ids)))
    print("sample ids", list(dict.fromkeys(shop_ids))[:5])
    # price patterns
    prices = re.findall(r"(\d{1,2},\d{3})円", html)
    print("prices sample", prices[:10])
    print()


def probe_ranking(region: str) -> None:
    url = f"https://estama.jp/{region}/ranking/"
    html = fetch(url)
    print("===", url)
    shops = re.findall(r'href="(/shop/\d+/)"[^>]*>([^<]{2,80})', html)
    print("shop links", shops[:12])
    sections = re.findall(r"##?\s*(おもてなし|お店|セラピスト)", html)
    print("sections", sections)
    print()


if __name__ == "__main__":
    for region in ["kanto", "kansai", "chubu"]:
        probe_shoplist(region)
    for region in ["kanto", "kansai", "chubu"]:
        probe_ranking(region)
