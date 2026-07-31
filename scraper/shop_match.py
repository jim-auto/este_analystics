"""Fuzzy shop name matching for BBS post cross-reference."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

STRIP_SUFFIXES = (
    "メンズエステ",
    "メンエス",
    "リラクゼーション",
    "リラク",
    "エステ",
    "サロン",
)

STRIP_PREFIXES = (
    "メンズエステ",
    "メンエス",
)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", "", text)
    return text.lower()


def shop_aliases(name: str) -> list[str]:
    if not name:
        return []

    aliases: set[str] = set()
    base = normalize_text(name)
    if len(base) >= 3:
        aliases.add(base)

    no_paren = re.sub(r"[（(][^）)]*[）)]", "", name).strip()
    no_paren_norm = normalize_text(no_paren)
    if len(no_paren_norm) >= 3:
        aliases.add(no_paren_norm)

    for suffix in STRIP_SUFFIXES:
        if no_paren_norm.endswith(normalize_text(suffix)) and len(no_paren_norm) > len(suffix) + 2:
            aliases.add(no_paren_norm[: -len(normalize_text(suffix))])

    for prefix in STRIP_PREFIXES:
        p = normalize_text(prefix)
        if no_paren_norm.startswith(p) and len(no_paren_norm) > len(p) + 2:
            aliases.add(no_paren_norm[len(p) :])

    for token in re.split(r"[\s　・/\\\-|｜]", name):
        token_norm = normalize_text(token)
        if len(token_norm) >= 3:
            aliases.add(token_norm)

    # Katakana / alphanumeric runs (e.g. Mスパ, GOLD)
    for token in re.findall(r"[A-Za-z0-9ぁ-んァ-ヶー]{3,}", name):
        token_norm = normalize_text(token)
        if len(token_norm) >= 3:
            aliases.add(token_norm)

    return sorted(aliases, key=len, reverse=True)


def build_shop_matcher(shops: list[dict[str, Any]]) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Return (alias, canonical_name) pairs sorted by alias length desc, and alias->name map."""
    pairs: list[tuple[str, str]] = []
    for shop in shops:
        name = shop.get("name")
        if not name:
            continue
        for alias in shop_aliases(name):
            pairs.append((alias, name))

    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    alias_map = {alias: name for alias, name in pairs}
    return pairs, alias_map


def match_shops_in_text(
    text: str,
    shop_pairs: list[tuple[str, str]] | None = None,
    shop_names: list[str] | None = None,
    limit: int = 8,
) -> list[str]:
    if shop_pairs is None:
        if not shop_names:
            return []
        shop_pairs = []
        for name in shop_names:
            for alias in shop_aliases(name):
                shop_pairs.append((alias, name))
        shop_pairs.sort(key=lambda x: len(x[0]), reverse=True)

    normalized = normalize_text(text)
    hits: list[str] = []
    seen_aliases: set[str] = set()

    for alias, name in shop_pairs:
        if alias in seen_aliases:
            continue
        if len(alias) < 3:
            continue
        if alias in normalized:
            if name not in hits:
                hits.append(name)
            seen_aliases.add(alias)
        if len(hits) >= limit:
            break

    return hits
