"""Scan bakusai bid range for Nagoya/Chubu menes boards."""
import re
import urllib.request

UA = "este_analystics/1.0 (+https://github.com/jim-auto/este_analystics; research bot)"
KEYWORDS = ("名古屋", "東海", "愛知", "名駅", "栄", "中部", "岐阜", "静岡")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


# bids seen in chubu pages plus nearby
bids = list(range(1100, 2200))
found = []
for bid in bids:
    url = f"https://bakusai.com/thr_tl/acode=5/ctgid=136/bid={bid}/"
    try:
        html = fetch(url)
    except Exception:
        continue
    m = re.search(r'countyTitle" title="([^"]+)"', html)
    if not m:
        continue
    title = m.group(1)
    if any(k in title for k in KEYWORDS):
        found.append((bid, title, len(html)))
        print(bid, title, len(html))

print("found", len(found))
