"""Probe and save board titles."""
import re
import urllib.request
from pathlib import Path

UA = "este_analystics/1.0 (+https://github.com/jim-auto/este_analystics; research bot)"
OUT = Path(__file__).resolve().parent.parent / "data" / "samples" / "board_probe.txt"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


candidates = [
    (3, 2389, "tokyo_sogo"),
    (3, 1714, "tokyo_shop?"),
    (5, 1713, "chubu_1713"),
    (5, 1714, "chubu_1714"),
    (5, 2389, "chubu_2389"),
    (5, 1268, "chubu_1268"),
    (5, 1744, "chubu_1744"),
    (7, 1714, "osaka_shop"),
    (7, 2389, "osaka_2389"),
]

lines = []
for acode, bid, label in candidates:
    url = f"https://bakusai.com/thr_tl/acode={acode}/ctgid=136/bid={bid}/"
    try:
        html = fetch(url)
        m = re.search(r'countyTitle" title="([^"]+)"', html)
        title = m.group(1) if m else "no title"
        lines.append(f"{label}\tacode={acode}\tbid={bid}\t{title}\t{len(html)}\t{url}")
    except Exception as exc:
        lines.append(f"{label}\tERR\t{exc}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(OUT)
