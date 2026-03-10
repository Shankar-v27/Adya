from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

import requests
from dateutil import parser as date_parser
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file

from core.ai_analysis import analyze_posts_dynamic


load_dotenv()

app = Flask(__name__)

SERPAPI_URL = "https://serpapi.com/search.json"


def _fetch_linkedin_posts(names: List[str], combined: bool, months: int) -> List[Dict[str, Any]]:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY environment variable is not set.")

    # Individual queries for each name
    queries: List[str] = [f'site:linkedin.com/posts "{n}"' for n in names]
    # Optional combined query for the first two names
    if combined and len(names) >= 2:
        queries.append(f'site:linkedin.com/posts "{names[0]}" "{names[1]}"')

    all_posts: List[Dict[str, Any]] = []
    cutoff = datetime.utcnow() - timedelta(days=30 * months)

    for q in queries:
        # Fetch multiple pages of results to increase coverage.
        for page in range(3):  # up to ~30 results per query
            params = {
                "engine": "google",
                "q": q,
                "api_key": api_key,
                "num": 10,
                "start": page * 10,
            }
            try:
                resp = requests.get(SERPAPI_URL, params=params, timeout=15)
                resp.raise_for_status()
            except requests.RequestException:
                continue

            data = resp.json()
            organic = data.get("organic_results") or []
            for item in organic:
                link = item.get("link")
                if not link or "linkedin.com" not in link:
                    continue

                title = item.get("title") or ""
                snippet = item.get("snippet") or ""
                date_str = item.get("date") or ""

                post_date = None
                if date_str:
                    try:
                        post_date = date_parser.parse(date_str)
                    except Exception:
                        post_date = None

                # Drop only if we have a known date that is older than cutoff.
                # Keep posts with unknown dates (SerpAPI often omits dates).
                if post_date is not None and post_date < cutoff:
                    continue

                content = f"{title}. {snippet}".strip()
                all_posts.append(
                    {
                        "post_content": content,
                        "post_url": link,
                        "post_date": post_date.isoformat() if post_date else None,
                    }
                )

    seen = set()
    unique_posts: List[Dict[str, Any]] = []
    for p in all_posts:
        url = p["post_url"]
        if url in seen:
            continue
        seen.add(url)
        unique_posts.append(p)

    return unique_posts


def _run_dynamic_pipeline(names: List[str], combined: bool, months: int) -> List[Dict[str, Any]]:
    raw_posts = _fetch_linkedin_posts(names, combined, months)
    return analyze_posts_dynamic(raw_posts, names=names)


@app.route("/", methods=["GET", "POST"])
def index():
    results: List[Dict[str, Any]] = []
    names: List[str] = []
    combined = False
    months = 6

    if request.method == "POST":
        raw_names = request.form.getlist("names[]")
        names = [n.strip() for n in raw_names if n.strip()]
        combined = request.form.get("combined_search") == "on"
        time_range = request.form.get("time_range", "6")

        try:
            months = int(time_range)
        except ValueError:
            months = 6

        if names:
            results = _run_dynamic_pipeline(names, combined, months)

    return render_template(
        "index.html",
        results=results,
        names=names,
        combined=combined,
        months=months,
    )


@app.route("/download/json")
def download_json():
    raw_names = request.args.getlist("names")
    names = [n.strip() for n in raw_names if n.strip()]
    combined = request.args.get("combined", "false") == "true"
    months = int(request.args.get("months", "6"))

    data = _run_dynamic_pipeline(names, combined, months)
    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    buf = io.BytesIO(json_bytes)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="linkedin_mentions.json",
        mimetype="application/json",
    )


@app.route("/download/csv")
def download_csv():
    raw_names = request.args.getlist("names")
    names = [n.strip() for n in raw_names if n.strip()]
    combined = request.args.get("combined", "false") == "true"
    months = int(request.args.get("months", "6"))

    data = _run_dynamic_pipeline(names, combined, months)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["content_head", "post_url", "post_date", "mention_type"])
    writer.writeheader()
    for row in data:
        writer.writerow(
            {
                "content_head": row.get("content_head", ""),
                "post_url": row.get("post_url", ""),
                "post_date": row.get("post_date", ""),
                "mention_type": row.get("mention_type", ""),
            }
        )

    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(
        mem,
        as_attachment=True,
        download_name="linkedin_mentions.csv",
        mimetype="text/csv",
    )


if __name__ == "__main__":
    app.run(debug=True)

