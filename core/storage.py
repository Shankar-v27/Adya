from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Dict, Any

import pandas as pd


def save_json(posts: Iterable[Dict[str, Any]], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(list(posts), f, indent=2, ensure_ascii=False)
    return p


def save_csv(posts: Iterable[Dict[str, Any]], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(list(posts))

    # Restrict to the final AI-structured fields:
    # content_head, post_url, post_date, mention_type.
    desired_cols = ["content_head", "post_url", "post_date", "mention_type"]
    existing_cols = [c for c in desired_cols if c in df.columns]
    if existing_cols:
        df = df[existing_cols]

    df.to_csv(p, index=False)
    return p

