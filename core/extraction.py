from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterable, List, Dict, Any

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser


logger = logging.getLogger(__name__)


GOOGLE_SEARCH_URL = "https://www.google.com/search"
SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"


@dataclass
class RawPost:
    author_name: str | None
    author_profile: str | None
    post_content: str | None
    post_url: str
    post_date: datetime | None
    reactions: int | None
    comments: int | None
    hashtags: List[str]
    mention_type: str | None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["post_date"] = self.post_date.isoformat() if self.post_date else None
        return data


def build_search_queries(person_name: str) -> List[str]:
    # Search for the company account name "Adya" and the specific person.
    terms = ['"Adya"', f'"{person_name}"', f'"Adya" "{person_name}"']
    return [f'site:linkedin.com {t}' for t in terms]


def _extract_hashtags(text: str | None) -> List[str]:
    if not text:
        return []
    return re.findall(r"#\w+", text)


def _has_company_mention(content: str) -> bool:
    """
    Detect company mentions:
    - 'Adya' as the company/account name.
    - Avoid cases where 'Adya' is clearly a surname like 'Mayank Adya'.
    """
    # Token-level check for 'Adya' not used as a person name (heuristic)
    tokens = re.findall(r"\b\w+\b", content)
    for i, token in enumerate(tokens):
        if token.lower() == "adya":
            prev_token = tokens[i - 1] if i > 0 else ""
            next_token = tokens[i + 1] if i + 1 < len(tokens) else ""

            # If previous token looks like a first name (Capitalized), treat this as a surname -> skip
            if prev_token and prev_token[0].isupper() and prev_token[1:].islower():
                continue

            # If next token looks like a capitalized name or brand (e.g. 'Chatterjee', 'Care'), skip,
            # except when it's explicitly 'AI' which we still want.
            if (
                next_token
                and next_token.lower() != "ai"
                and next_token[0].isupper()
                and next_token[1:].islower()
            ):
                continue
            return True
    return False


def _has_person_mention(content: str, person_name: str) -> bool:
    # Exact phrase match for the full name with word boundaries.
    pattern = r"\b" + re.escape(person_name.lower()) + r"\b"
    return re.search(pattern, content.lower()) is not None


def _infer_mention_type(content: str | None, person_name: str) -> str | None:
    if not content:
        return None

    has_adya = _has_company_mention(content)
    has_person = _has_person_mention(content, person_name)

    if has_adya and has_person:
        return "Both"
    if has_adya:
        return "Adya"
    if has_person:
        return "Founder"
    return None


def _parse_google_result_block(block, person_name: str) -> RawPost | None:
    link_tag = block.find("a", href=True)
    if not link_tag:
        return None
    href = link_tag["href"]
    if "linkedin.com" not in href:
        return None

    title = link_tag.get_text(strip=True)
    snippet_tag = block.find("div", class_="VwiC3b")
    snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""

    date = None
    date_match = re.search(r"(\w+\s+\d{1,2},\s+\d{4})", snippet)
    if date_match:
        try:
            date = date_parser.parse(date_match.group(1))
        except (ValueError, OverflowError):
            date = None

    mention_type = _infer_mention_type(f"{title} {snippet}", person_name)
    hashtags = _extract_hashtags(snippet)

    return RawPost(
        author_name=None,
        author_profile=None,
        post_content=snippet,
        post_url=href,
        post_date=date,
        reactions=None,
        comments=None,
        hashtags=hashtags,
        mention_type=mention_type,
    )


def _parse_serpapi_result_item(item: Dict[str, Any], person_name: str) -> RawPost | None:
    link = item.get("link")
    if not link or "linkedin.com" not in link:
        return None

    title = item.get("title", "") or ""
    snippet = item.get("snippet", "") or ""
    date_str = item.get("date") or ""

    date = None
    if date_str:
        try:
            date = date_parser.parse(date_str)
        except (ValueError, OverflowError):
            date = None

    combined_text = f"{title} {snippet}"
    mention_type = _infer_mention_type(combined_text, person_name)
    hashtags = _extract_hashtags(snippet)

    return RawPost(
        author_name=None,
        author_profile=None,
        post_content=combined_text.strip(),
        post_url=link,
        post_date=date,
        reactions=None,
        comments=None,
        hashtags=hashtags,
        mention_type=mention_type,
    )


def search_linkedin_posts_google(person_name: str, num_pages: int = 3) -> List[RawPost]:
    results: List[RawPost] = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    for query in build_search_queries(person_name):
        for page in range(num_pages):
            params = {"q": query, "start": page * 10}
            try:
                response = requests.get(GOOGLE_SEARCH_URL, params=params, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Failed to fetch Google results for %s page %s: %s", query, page, exc)
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            blocks = soup.select("div.g")
            for block in blocks:
                post = _parse_google_result_block(block, person_name)
                if post and post.mention_type:
                    results.append(post)

    return results


def search_linkedin_posts_serpapi(person_name: str, num_pages: int = 3) -> List[RawPost]:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY environment variable is not set.")

    results: List[RawPost] = []
    for query in build_search_queries(person_name):
        for page in range(num_pages):
            params = {
                "engine": "google",
                "q": query,
                "start": page * 10,
                "api_key": api_key,
            }
            try:
                resp = requests.get(SERPAPI_SEARCH_URL, params=params, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Failed to fetch SerpAPI results for %s page %s: %s", query, page, exc)
                continue

            data = resp.json()
            organic_results = data.get("organic_results") or []
            for item in organic_results:
                post = _parse_serpapi_result_item(item, person_name)
                if post and post.mention_type:
                    results.append(post)

    return results


def search_linkedin_posts(person_name: str, num_pages: int = 3, source: str = "serpapi") -> List[RawPost]:
    """
    High-level search API.

    :param person_name: Founder/person name.
    :param num_pages: Number of pages per query.
    :param source: 'serpapi' (default) or 'google'.
    """
    if source.lower() == "google":
        return search_linkedin_posts_google(person_name, num_pages=num_pages)
    return search_linkedin_posts_serpapi(person_name, num_pages=num_pages)


def deduplicate_raw_posts(posts: Iterable[RawPost]) -> List[RawPost]:
    seen_urls: set[str] = set()
    unique: List[RawPost] = []
    for post in posts:
        if post.post_url in seen_urls:
            continue
        seen_urls.add(post.post_url)
        unique.append(post)
    return unique

