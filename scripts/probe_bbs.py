"""Probe bakusai board and thread HTML."""
import re
import urllib.request
from pathlib import Path

UA = "este_analystics/1.0 (+https://github.com/jim-auto/este_analystics; research bot)"
OUT = Path(__file__).resolve().parent.parent / "data" / "samples"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    urls = {
        "bakusai_tokyo_sogo.html": "https://bakusai.com/thr_tl/acode=3/ctgid=136/bid=2389/",
        "bakusai_osaka_shop.html": "https://bakusai.com/thr_tl/acode=7/ctgid=136/bid=1714/",
        "bakusai_chubu.html": "https://bakusai.com/thr_tl/acode=5/ctgid=136/bid=1714/",
    }
    for name, url in urls.items():
        try:
            html = fetch(url)
            (OUT / name).write_text(html, encoding="utf-8")
            print(name, len(html), "ok")
        except Exception as e:
            print(name, "ERR", e)

    # fetch one thread
    thread_url = "https://bakusai.com/thr_res/acode=3/ctgid=136/bid=2389/tid=11739836/"
    html = fetch(thread_url)
    (OUT / "bakusai_thread_sample.html").write_text(html, encoding="utf-8")
    print("thread", len(html))


if __name__ == "__main__":
    main()
