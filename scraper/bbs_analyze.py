"""Analyze Bakusai BBS threads and posts."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from scraper.shop_match import match_shops_in_text, normalize_text

KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "caution": (
        "地雷",
        "外れ",
        "ハズレ",
        "詐欺",
        "ぼったくり",
        "最悪",
        "キック",
        "写真詐欺",
        "サギ",
        "残念",
        "二度と",
        "返金",
    ),
    "positive": (
        "オススメ",
        "おすすめ",
        "当たり",
        "ハズレなし",
        "神",
        "最高",
        "リピ",
        "大満足",
        "優良",
    ),
    "value": ("コスパ", "割安", "激安", "安い", "破格", "穴場"),
    "service": ("指名", "延長", "オプション", "寛容", "健全", "密着"),
}

TOPIC_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"おすすめ|オススメ|教えて|ありますか", "店探し・おすすめ"),
    (r"地雷|外れ|ハズレ|注意|詐欺", "注意・トラブル"),
    (r"コスパ|割安|激安|安い", "料金・コスパ"),
    (r"初めて|初心者|ビギナー", "初心者"),
    (r"セラピ|キャスト|嬢", "セラピスト"),
    (r"総合|スレ", "地域・総合"),
)


def _normalize_name(name: str) -> str:
    return normalize_text(name)


def _find_keywords(text: str) -> list[str]:
    found: list[str] = []
    for group, words in KEYWORD_GROUPS.items():
        for word in words:
            if word in text and word not in found:
                found.append(word)
    return found


def _thread_topic(title: str) -> str:
    for pattern, label in TOPIC_PATTERNS:
        if re.search(pattern, title):
            return label
    return "その他"


def _match_shops(text: str, shop_names: list[str], limit: int = 8) -> list[str]:
    return match_shops_in_text(text, shop_names=shop_names, limit=limit)


def analyze_bbs(
    threads: list[dict[str, Any]],
    posts: list[dict[str, Any]],
    shop_names: list[str] | None = None,
) -> dict[str, Any]:
    shop_names = shop_names or []
    post_count = len(posts)
    thread_count = len(threads)

    keyword_counts: Counter[str] = Counter()
    group_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    shop_mentions: Counter[str] = Counter()
    caution_posts: list[dict[str, Any]] = []

    for thread in threads:
        topic_counts[_thread_topic(thread.get("title", ""))] += 1

    for post in posts:
        text = post.get("text") or ""
        keys = _find_keywords(text)
        for key in keys:
            keyword_counts[key] += 1
            for group, words in KEYWORD_GROUPS.items():
                if key in words:
                    group_counts[group] += 1
                    break

        for shop in _match_shops(text, shop_names):
            shop_mentions[shop] += 1

        caution_hits = [k for k in keys if k in KEYWORD_GROUPS["caution"]]
        if caution_hits:
            caution_posts.append(
                {
                    "flags": caution_hits,
                    "excerpt": post.get("excerpt"),
                    "thread_title": post.get("thread_title"),
                    "thread_url": post.get("thread_url"),
                }
            )

    caution_rate = round(len(caution_posts) / post_count * 100, 1) if post_count else 0.0
    positive_hits = sum(1 for p in posts if any(k in (p.get("text") or "") for k in KEYWORD_GROUPS["positive"]))
    positive_rate = round(positive_hits / post_count * 100, 1) if post_count else 0.0

    hot_threads = sorted(
        threads,
        key=lambda t: (t.get("responses") or 0, t.get("views") or 0),
        reverse=True,
    )[:10]

    notes: list[str] = []
    if caution_rate >= 15:
        notes.append(
            f"注意系キーワード（地雷・外れ等）を含むレスがサンプルの{caution_rate}%。"
            "掲示板ではネガティブ報告が目立ちやすい点に留意してください。"
        )
    if positive_rate >= 40:
        notes.append(
            f"高評価キーワードを含むレスが{positive_rate}%。"
            "口コミサイトより口語的・極端な表現が多い傾向があります。"
        )
    if not post_count:
        notes.append("レスの取得に失敗したか、会員限定スレが多い可能性があります。")

    return {
        "parsed_threads": thread_count,
        "parsed_posts": post_count,
        "caution_rate": caution_rate,
        "positive_rate": positive_rate,
        "top_keywords": dict(keyword_counts.most_common(12)),
        "keyword_groups": dict(group_counts),
        "thread_topics": dict(topic_counts.most_common(8)),
        "shop_mentions": [
            {"name": name, "count": count}
            for name, count in shop_mentions.most_common(10)
        ],
        "hot_threads": [
            {
                "title": t.get("title"),
                "url": t.get("url"),
                "responses": t.get("responses"),
                "views": t.get("views"),
                "last_posted": t.get("last_posted"),
            }
            for t in hot_threads
        ],
        "caution_posts": caution_posts[:12],
        "notes": notes,
    }


def build_bbs_summary(regions: dict[str, dict]) -> dict[str, Any]:
    items = []
    for key, payload in regions.items():
        bbs = payload.get("bbs") or {}
        insights = bbs.get("insights") or {}
        board = bbs.get("board") or {}
        items.append(
            {
                "key": key,
                "label": payload.get("region_label"),
                "board_label": board.get("label"),
                "board_url": board.get("url"),
                "parsed_threads": insights.get("parsed_threads"),
                "parsed_posts": insights.get("parsed_posts"),
                "caution_rate": insights.get("caution_rate"),
                "positive_rate": insights.get("positive_rate"),
                "top_keywords": dict(list((insights.get("top_keywords") or {}).items())[:5]),
                "hot_threads": (insights.get("hot_threads") or [])[:3],
            }
        )

    return {
        "source_label": "爆サイ.com（2ch系掲示板）",
        "disclaimer": (
            "掲示板情報は匿名投稿であり、真偽・最新性は保証できません。"
            "誹謗中傷や店舗関係者の書込みも含まれるため、参考程度にご利用ください。"
            "5ch.net への直接スクレイピングは利用規約上禁止のため、本解析は爆サイを対象としています。"
        ),
        "regions": items,
    }
