from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Iterable, List, Dict, Any

from .extraction import RawPost, _infer_mention_type


def filter_by_date(posts: Iterable[RawPost], months: int) -> List[RawPost]:
    cutoff = datetime.utcnow() - timedelta(days=30 * months)
    filtered: List[RawPost] = []
    for post in posts:
        # If we don't know the date, keep the post (best-effort filtering).
        if post.post_date is None or post.post_date >= cutoff:
            filtered.append(post)
    return filtered


def ensure_relevance(posts: Iterable[RawPost], person_name: str) -> List[RawPost]:
    relevant: List[RawPost] = []
    for post in posts:
        content = post.post_content or ""
        mention_type = _infer_mention_type(content, person_name)
        if mention_type:
            post.mention_type = mention_type
            relevant.append(post)
    return relevant


def remove_duplicates(posts: Iterable[RawPost]) -> List[RawPost]:
    seen_urls: set[str] = set()
    unique: List[RawPost] = []
    for post in posts:
        if post.post_url in seen_urls:
            continue
        seen_urls.add(post.post_url)
        unique.append(post)
    return unique


def normalize_posts(posts: Iterable[RawPost]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for post in posts:
        data = asdict(post)
        data["post_date"] = post.post_date.isoformat() if post.post_date else None
        normalized.append(data)
    return normalized

