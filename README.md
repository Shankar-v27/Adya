# LinkedIn Mention Extraction System

This project implements an automated system to extract LinkedIn posts that mention **Adya AI** and/or a specific person within the last six months, and generates a structured dataset and report.

## Features

- Discover posts that mention:
  - `Adya AI`
  - The configured person name
  - Or both together
- Extract for each post:
  - Author name
  - Author profile link (when available from the search result)
  - Post content snippet (from search result)
  - Post URL
  - Post date (parsed when present)
  - Number of reactions (optional / best-effort)
  - Number of comments (optional / best-effort)
  - Hashtags (best-effort from content)
  - Mention type (`Founder`, `Adya AI`, or `Both`)
- Filter by:
  - Time range (last 6 months)
  - Relevance (must contain required terms)
  - Duplicates (by URL / content)
- Store results in:
  - JSON file
  - CSV file
- Generate a simple tabular report.

> Note: Direct scraping of LinkedIn pages is heavily rate-limited and against their terms of service. This reference implementation uses **Google search result pages targeting LinkedIn** and basic HTML parsing for educational purposes only. For production use, you should rely on approved APIs or data providers.

## Project Structure

- `main.py` – CLI entrypoint to run the full pipeline.
- `core/extraction.py` – Search + extraction logic (via SerpAPI or Google search HTML).
- `core/filtering.py` – Time range, relevance, and duplicate filtering.
- `core/ai_analysis.py` – AI post-analysis module using Claude / heuristic fallback.
- `core/storage.py` – Saving results to JSON and CSV.
- `core/reporting.py` – Generating a simple report.
- `requirements.txt` – Python dependencies.

## Installation

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your SerpAPI key in an environment variable (recommended way):

- On PowerShell (current session):

```bash
$env:SERPAPI_KEY = "YOUR_SERPAPI_KEY_HERE"
```

- On Linux/macOS (bash/zsh):

```bash
export SERPAPI_KEY="YOUR_SERPAPI_KEY_HERE"
```

4. (Optional but recommended) Set your Claude / Anthropic API key for the AI analysis module:

- On PowerShell:

```bash
$env:ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_KEY_HERE"
```

- On Linux/macOS:

```bash
export ANTHROPIC_API_KEY="YOUR_ANTHROPIC_KEY_HERE"
```

## Usage

Run the pipeline from the project root:

```bash
python main.py --person-name "Founder Name" --months 6 --output-prefix "adya_mentions" --source serpapi
```

Arguments:

- `--person-name` – Name of the person/founder to look for.
- `--months` – How many months back to include (default: 6).
- `--output-prefix` – Prefix for output files (default: `output`).
- `--source` – Search backend: `serpapi` (default, requires `SERPAPI_KEY`) or `google`.

Outputs:

- `<prefix>.json` – Raw structured data.
- `<prefix>.csv` – Tabular dataset.
- `<prefix>_report.txt` – Simple human-readable report.

## Disclaimer

This code is for educational and demo purposes only. When working with real user data and third-party platforms:

- Always follow the platform's terms of service.
- Respect robots.txt and rate limits.
- Ensure compliance with privacy and data protection regulations.

