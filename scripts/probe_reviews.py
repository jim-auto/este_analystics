"""Probe review list HTML structure."""
import re
import urllib.request
from pathlib import Path

UA = "este_analystics/1.0 (+https://github.com/jim-auto/este_analystics)"
OUT = Path(__file__).resolve().parent.parent / "data" / "samples"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for region in ["kanto", "kansai", "chubu"]:
        url = f"https://estama.jp/{region}/reviewlist/"
        html = fetch(url)
        name = f"{region}_reviewlist.html"
        (OUT / name).write_text(html, encoding="utf-8")
        print(name, len(html))
        for pat in ["reviewlist", "極上体験", "review", "口コミ", "5.0", "4.0"]:
            print(f"  {pat}: {html.count(pat)}")


if __name__ == "__main__":
    main()
