from __future__ import annotations

import argparse
from typing import List

from dotenv import load_dotenv

from core.extraction import search_linkedin_posts
from core.filtering import filter_by_date, ensure_relevance, remove_duplicates, normalize_posts
from core.ai_analysis import analyze_posts_with_ai
from core.storage import save_json, save_csv
from core.reporting import generate_text_report


def run_pipeline(person_name: str, months: int, output_prefix: str, source: str) -> None:
    raw_posts = search_linkedin_posts(person_name, source=source)

    recent_posts = filter_by_date(raw_posts, months=months)
    relevant_posts = ensure_relevance(recent_posts, person_name=person_name)
    unique_posts = remove_duplicates(relevant_posts)
    normalized = normalize_posts(unique_posts)

    # AI analysis module: produce final structured records
    analyzed = analyze_posts_with_ai(normalized, person_name=person_name)

    json_path = save_json(analyzed, f"{output_prefix}.json")
    csv_path = save_csv(analyzed, f"{output_prefix}.csv")
    report_path = generate_text_report(analyzed, f"{output_prefix}_report.txt")

    print(f"Saved JSON to {json_path}")
    print(f"Saved CSV to {csv_path}")
    print(f"Saved report to {report_path}")


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LinkedIn Mention Extraction System")
    parser.add_argument("--person-name", required=True, help="Name of the person/founder to search for.")
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Number of months back to include (default: 6).",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="output",
        help="Prefix for output files (default: output).",
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["serpapi", "google"],
        default="serpapi",
        help="Search backend to use: 'serpapi' (requires SERPAPI_KEY env var) or 'google'. Default: serpapi.",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> None:
    # Load environment variables from .env if present
    load_dotenv()
    args = parse_args(argv)
    run_pipeline(
        person_name=args.person_name,
        months=args.months,
        output_prefix=args.output_prefix,
        source=args.source,
    )


if __name__ == "__main__":
    main()

