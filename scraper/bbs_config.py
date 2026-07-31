"""Bakusai (2ch-style BBS) board configuration for 東名阪."""

BAKUSAI_BASE = "https://bakusai.com"
CTGID_MENES = 136

BBS_THREAD_LIST_PAGES = 1
BBS_SAMPLE_THREADS_PER_BOARD = 5
BBS_MAX_POSTS_PER_THREAD = 40
BBS_POST_EXCERPT_MAX = 160

# Primary 総合 boards + お店 boards per region.
BBS_BOARD_SETS: dict[str, list[dict[str, object]]] = {
    "kanto": [
        {"acode": 3, "bid": 2389, "label": "東京メンエス・リラクゼーション・総合"},
        {"acode": 3, "bid": 2027, "label": "東京メンエス・リラクゼーション・お店"},
    ],
    "chubu": [
        {"acode": 5, "bid": 2375, "label": "愛知メンエス・リフレ・癒し・総合"},
        {"acode": 5, "bid": 1326, "label": "愛知メンエス・リフレ・癒し・お店"},
    ],
    "kansai": [
        {"acode": 7, "bid": 2383, "label": "大阪メンエス・リフレ・癒し・総合"},
        {"acode": 7, "bid": 1714, "label": "大阪メンエス・リフレ・癒し・お店"},
    ],
}

# Backward-compatible primary board per region.
BBS_BOARDS = {key: boards[0] for key, boards in BBS_BOARD_SETS.items()}


def board_list_url(acode: int, bid: int, page: int = 1) -> str:
    base = f"{BAKUSAI_BASE}/thr_tl/acode={acode}/ctgid={CTGID_MENES}/bid={bid}/"
    if page <= 1:
        return base
    return f"{base}p={page}/"
