from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Any

from anthropic import Anthropic


@dataclass
class AnalyzedPost:
    content_head: str
    post_url: str
    post_date: str | None
    mention_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_head": self.content_head,
            "post_url": self.post_url,
            "post_date": self.post_date,
            "mention_type": self.mention_type,
        }


SYSTEM_PROMPT = """
You are an assistant that labels LinkedIn posts about a company named "Adya" (also referenced as "Adya AI")
and a specific founder.

You will receive:
- The full text content of a LinkedIn post
- The founder's full name

Your tasks:
1. Generate a short, human-readable headline (content_head) summarizing the main idea of the post
   in one concise sentence. Avoid generic phrases and keep it under 20 words.

2. Decide the mention_type according to these STRICT rules:
   - "Company Mention": The post clearly refers to the company "Adya" or "Adya AI" as an organization,
     brand, product, or account. Ignore unrelated people whose surname or first name is "Adya"
     (e.g. "Adya Chatterjee", "Adya Roy", etc.) unless the text explicitly indicates they are
     representing or talking about the company Adya.
   - "Founder Mention": The post clearly mentions the founder by full name.
   - "Both Mentioned": The post clearly mentions BOTH the company "Adya" / "Adya AI" and the founder.

If you are not reasonably sure that the company "Adya" is being referenced, you MUST choose
"Founder Mention" (if only the founder is mentioned) or say that the post does not mention the
company at all by picking "Founder Mention" only.

Return ONLY a JSON object with keys:
- content_head (string)
- mention_type (one of: "Company Mention", "Founder Mention", "Both Mentioned")
"""


def _build_claude_client() -> Anthropic | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def analyze_posts_with_ai(
    posts: List[Dict[str, Any]],
    person_name: str,
) -> List[Dict[str, Any]]:
    """
    Analyze posts using Claude (if API key available). Falls back to a simple heuristic if not.

    Input posts are dictionaries that MUST contain:
    - post_content
    - post_url
    - post_date
    """
    client = _build_claude_client()
    analyzed: List[Dict[str, Any]] = []

    for post in posts:
        content = post.get("post_content") or ""
        url = post.get("post_url") or ""
        date = post.get("post_date")

        if client and content:
            try:
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=256,
                    temperature=0,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Founder full name: {person_name}\n\nPost content:\n{content}",
                        }
                    ],
                )
                text = msg.content[0].text if msg.content else "{}"
                import json

                parsed = json.loads(text)
                content_head = parsed.get("content_head") or content[:120]
                mention_type = parsed.get("mention_type") or "Company Mention"
            except Exception:
                # Fallback heuristic on error
                content_head, mention_type = _heuristic_analysis(content, person_name)
        else:
            content_head, mention_type = _heuristic_analysis(content, person_name)

        analyzed_post = AnalyzedPost(
            content_head=content_head.strip(),
            post_url=url,
            post_date=date,
            mention_type=mention_type,
        )
        analyzed.append(analyzed_post.to_dict())

    return analyzed


def _heuristic_analysis(content: str, person_name: str) -> tuple[str, str]:
    """Simple non-LLM fallback matching the same categories."""
    text = content.lower()
    has_company = "adya" in text
    has_person = person_name.lower() in text

    if has_company and has_person:
        mention_type = "Both Mentioned"
    elif has_company:
        mention_type = "Company Mention"
    elif has_person:
        mention_type = "Founder Mention"
    else:
        mention_type = "Company Mention"

    # Naive content head: first 120 chars
    content_head = content.strip().split("\n")[0][:120] if content else ""
    return content_head, mention_type


# ================================
# Dynamic multi-name analysis mode
# ================================

from typing import Tuple
import json as _json


def _build_dynamic_prompt(names: List[str]) -> str:
    names_list = "\n".join(f"- {n}" for n in names)
    return f"""You are an assistant that labels LinkedIn posts. You will receive a list of names/keywords and a post.

The names to look for:
{names_list}

Your tasks:

1. Generate a short, human-readable headline (content_head) summarizing the main idea of the post
   in one concise sentence. Keep it under 20 words.

2. Determine which of the provided names are clearly mentioned in the post.
   Return them as a list in "mentioned_names".

   Be STRICT: only include a name if the post clearly refers to that exact entity.
   Ignore unrelated people or brands that happen to share part of a name.

Return ONLY a JSON object with keys:
- content_head (string)
- mentioned_names (array of strings, subset of the names provided)
"""


def analyze_posts_dynamic(
    posts: List[Dict[str, Any]],
    names: List[str],
) -> List[Dict[str, Any]]:
    """
    Classify posts against a dynamic list of names.

    Returns dicts with: content_head, post_url, post_date, mention_type.
    """
    client = _build_claude_client()
    prompt = _build_dynamic_prompt(names)
    analyzed: List[Dict[str, Any]] = []

    for post in posts:
        content = post.get("post_content") or ""
        url = post.get("post_url") or ""
        date = post.get("post_date")

        if client and content:
            try:
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=256,
                    temperature=0,
                    system=prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": f"post_content:\n{content}",
                        }
                    ],
                )
                text = msg.content[0].text if msg.content else "{}"
                parsed = _json.loads(text)
                content_head = parsed.get("content_head") or content[:120]
                mentioned = parsed.get("mentioned_names") or []
                mention_type = _format_mention_type(mentioned, names)
            except Exception:
                content_head, mention_type = _heuristic_multi(content, names)
        else:
            content_head, mention_type = _heuristic_multi(content, names)

        analyzed_post = AnalyzedPost(
            content_head=content_head.strip(),
            post_url=url,
            post_date=date,
            mention_type=mention_type,
        )
        analyzed.append(analyzed_post.to_dict())

    return analyzed


def _format_mention_type(mentioned: List[str], all_names: List[str]) -> str:
    if not mentioned:
        return f"{all_names[0]} Mention"
    if len(mentioned) == 1:
        return f"{mentioned[0]} Mention"
    return "Multiple: " + ", ".join(mentioned)


def _heuristic_multi(content: str, names: List[str]) -> Tuple[str, str]:
    """Simple fallback when Claude is unavailable."""
    text = content.lower()
    found = [n for n in names if n.lower() in text]

    if not found:
        mention_type = f"{names[0]} Mention"
    elif len(found) == 1:
        mention_type = f"{found[0]} Mention"
    else:
        mention_type = "Multiple: " + ", ".join(found)

    content_head = content.strip().split("\n")[0][:120] if content else ""
    return content_head, mention_type


