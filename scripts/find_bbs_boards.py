"""Find bakusai menes board IDs per area."""
import re
import urllib.request

UA = "este_analystics/1.0 (+https://github.com/jim-auto/este_analystics; research bot)"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


for acode, name in [(3, "tokyo"), (5, "chubu"), (7, "osaka")]:
    html = fetch(f"https://bakusai.com/areatop/acode={acode}/")
    links = re.findall(
        r'href="(/thr_tl/acode=\d+/ctgid=136/bid=\d+/)"[^>]*>([^<]{0,80})',
        html,
    )
    print(f"\n=== {name} acode={acode} ===")
    seen = set()
    for href, title in links:
        key = href
        if key in seen:
            continue
        seen.add(key)
        print(href, title.strip()[:60])
