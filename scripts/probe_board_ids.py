"""Probe bakusai category/board URLs."""
import re
import urllib.request

UA = "este_analystics/1.0 (+https://github.com/jim-auto/este_analystics; research bot)"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


URLS = [
    "https://bakusai.com/thr_tl/acode=5/ctgid=136/",
    "https://bakusai.com/thr_tl/acode=7/ctgid=136/",
    "https://bakusai.com/thr_tl/acode=5/ctgid=136/bid=1714/",
    "https://bakusai.com/thr_tl/acode=5/ctgid=136/bid=2389/",
    "https://bakusai.com/thr_tl/acode=5/ctgid=136/bid=1713/",
    "https://bakusai.com/thr_tl/acode=5/ctgid=136/bid=1715/",
    "https://bakusai.com/thr_tl/acode=7/ctgid=136/bid=2389/",
]

for url in URLS:
    try:
        html = fetch(url)
        m = re.search(r'countyTitle" title="([^"]+)"', html)
        title = m.group(1) if m else "no title"
        bids = sorted(set(re.findall(r"bid=(\d+)", html)))
        print(len(html), title[:70])
        print("  bids sample:", bids[:8], url)
    except Exception as exc:
        print("ERR", exc, url)
