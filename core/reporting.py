from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable, Dict, Any


def generate_text_report(posts: Iterable[Dict[str, Any]], path: str | Path) -> Path:
    posts_list = list(posts)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    total = len(posts_list)
    by_mention = Counter(p.get("mention_type") or "Unknown" for p in posts_list)
    dates = [
        datetime.fromisoformat(p["post_date"])
        for p in posts_list
        if p.get("post_date")
    ]
    min_date = min(dates).date().isoformat() if dates else "N/A"
    max_date = max(dates).date().isoformat() if dates else "N/A"

    with p.open("w", encoding="utf-8") as f:
        f.write("LinkedIn Mention Extraction Report\n")
        f.write("=================================\n\n")
        f.write(f"Total posts: {total}\n")
        f.write(f"Date range: {min_date} to {max_date}\n\n")

        f.write("By mention type:\n")
        for k, v in by_mention.items():
            f.write(f"- {k}: {v}\n")
        f.write("\nSample posts:\n")
        for post in posts_list[:10]:
            f.write("- " + (post.get("post_content") or "").strip()[:200] + "\n")
            f.write("  URL: " + (post.get("post_url") or "") + "\n")
            f.write("  Date: " + str(post.get("post_date")) + "\n\n")

    return p

