"""Bakusai (2ch-style BBS) board configuration for 東名阪."""

BAKUSAI_BASE = "https://bakusai.com"
CTGID_MENES = 136

# Thread list pages and post sampling limits (keep requests modest).
BBS_THREAD_LIST_PAGES = 1
BBS_SAMPLE_THREADS = 10
BBS_MAX_POSTS_PER_THREAD = 40
BBS_POST_EXCERPT_MAX = 160

BBS_BOARDS = {
    "kanto": {
        "acode": 3,
        "bid": 2389,
        "label": "東京メンエス・リラクゼーション・総合",
    },
    "chubu": {
        "acode": 5,
        "bid": 2375,
        "label": "愛知メンエス・リフレ・癒し・総合",
    },
    "kansai": {
        "acode": 7,
        "bid": 2383,
        "label": "大阪メンエス・リフレ・癒し・総合",
    },
}


def board_list_url(region_key: str, page: int = 1) -> str:
    cfg = BBS_BOARDS[region_key]
    base = (
        f"{BAKUSAI_BASE}/thr_tl/acode={cfg['acode']}/ctgid={CTGID_MENES}/bid={cfg['bid']}/"
    )
    if page <= 1:
        return base
    return f"{base}p={page}/"
