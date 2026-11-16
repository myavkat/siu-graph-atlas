#!/usr/bin/env python3
"""Collect SIU conference papers (2020-2026) from OpenAlex.

Source: OpenAlex conference source S4363607818
("Signal Processing and Communications Applications Conference (SIU)").
License: OpenAlex data is CC0.

No API key is needed. Cursor paging needs a key, so this script uses
page-based paging, which is still open. Keep the request rate low: the
free budget is shared per IP.

Run from the repository root:

    python3 src/collect_siu.py

Output: data/siu_papers_2020_2026.csv
Columns: paper_id, doi, year, title, abstract, keywords (JSON array).
Only works of type "conference-paper" are written. Front matter, errata,
and author indexes from the proceedings are excluded.

The committed CSV is a snapshot from 2026-11-12. A fresh run can differ
after OpenAlex updates a record.

The keywords are OpenAlex keywords, not the author index terms from
IEEE Xplore. They are a provisional keyword layer. Merge the author
index terms by DOI when the IEEE Xplore API key is available.
"""

import csv
import json
import pathlib
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

SOURCE_ID = "S4363607818"
FROM_DATE = "2020-01-01"
TO_DATE = "2026-12-31"
PAGE_SIZE = 200
SELECT = "id,doi,title,publication_year,type,abstract_inverted_index,keywords"
API = "https://api.openalex.org/works"
USER_AGENT = "complex-networks-course-project/0.1"
OUT_DIR = pathlib.Path(__file__).resolve().parents[1] / "data"
OUT_CSV = OUT_DIR / "siu_papers_2020_2026.csv"

# Proceedings front matter is typed as "conference-paper" in OpenAlex.
FRONT_MATTER = re.compile(
    r"^(?:siu\s+\d{4}\s+)?"
    r"(?:\[?front cover\]?|cover page|author list|author index|foreword|index)$",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    """Fix PDF artifacts: ligatures, soft hyphens, non-breaking spaces."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def fetch_page(page: int) -> dict:
    query = urllib.parse.urlencode(
        {
            "filter": (
                f"primary_location.source.id:{SOURCE_ID},"
                f"from_publication_date:{FROM_DATE},"
                f"to_publication_date:{TO_DATE}"
            ),
            "sort": "publication_date:desc",
            "per_page": PAGE_SIZE,
            "page": page,
            "select": SELECT,
        }
    )
    url = f"{API}?{query}"
    for attempt in range(4):
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            print(f"  HTTP {error.code} on page {page}, retry {attempt + 1}")
            time.sleep(3 + 4 * attempt)
    raise RuntimeError(f"Could not fetch page {page}")


def abstract_from_inverted_index(inverted: dict | None) -> str:
    if not inverted:
        return ""
    positions = sorted((position, word) for word, places in inverted.items() for position in places)
    return " ".join(word for _, word in positions)


def collect() -> list[dict]:
    records: list[dict] = []
    page = 1
    while True:
        payload = fetch_page(page)
        results = payload["results"]
        records.extend(results)
        total = payload["meta"]["count"]
        print(f"  page {page}: {len(records)}/{total}")
        if not results or len(records) >= total:
            break
        page += 1
        time.sleep(0.3)
    return records


def write_csv(records: list[dict]) -> tuple[int, int]:
    rows = []
    skipped_front_matter = 0
    for record in records:
        if record.get("type") != "conference-paper":
            continue
        title = normalize(record.get("title") or "")
        if FRONT_MATTER.match(title):
            skipped_front_matter += 1
            continue
        rows.append(
            {
                "paper_id": record.get("id", "").rsplit("/", 1)[-1],
                "doi": record.get("doi", ""),
                "year": record.get("publication_year", ""),
                "title": title,
                "abstract": normalize(
                    abstract_from_inverted_index(record.get("abstract_inverted_index"))
                ),
                "keywords": json.dumps(
                    [
                        normalize(keyword["display_name"])
                        for keyword in record.get("keywords") or []
                    ],
                    ensure_ascii=False,
                ),
            }
        )
    rows.sort(key=lambda row: (row["year"], row["doi"]))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows), skipped_front_matter


def main() -> None:
    print("Collecting SIU works from OpenAlex...")
    records = collect()
    count, skipped = write_csv(records)
    print(f"Wrote {count} papers to {OUT_CSV}")
    print(f"Excluded {skipped} front-matter items")
    by_year: dict[int, int] = {}
    for record in records:
        if record.get("type") != "conference-paper":
            continue
        title = normalize(record.get("title") or "")
        if FRONT_MATTER.match(title):
            continue
        year = record.get("publication_year")
        by_year[year] = by_year.get(year, 0) + 1
    print("Papers per year:", dict(sorted(by_year.items())))


if __name__ == "__main__":
    main()
