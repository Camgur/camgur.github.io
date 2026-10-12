#!/usr/bin/env python3
"""Safely retrieve usage metrics for a ChemRxiv preprint.

Target DOI: 10.26434/chemrxiv.15002480

Usage:
    python scripts/update_metrics.py
    python scripts/update_metrics.py --diagnose

Diagnostic mode prints the matched record's field names and exits
without changing the published metrics file.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

DOI = "10.26434/chemrxiv.15002480"
API_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items"
OUTPUT = Path("data/chemrxiv-metrics.json")

TIMEOUT = 30

# These field names must be confirmed against the actual API response.
# Do not add a field until its meaning is verified.
VIEW_KEYS = ("viewsCount", "views_count", "viewCount", "view_count")

# Deliberately do not map readCount to downloads without verification.
DOWNLOAD_KEYS = (
    "downloadsCount",
    "downloads_count",
    "downloadCount",
    "download_count",
)


def normalize_doi(value):
    """Normalize a DOI for exact comparison."""
    if not isinstance(value, str):
        return ""

    value = value.strip().lower()

    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break

    return value.rstrip("/")


def dictionaries(value):
    """Yield dictionaries recursively from nested JSON."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from dictionaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from dictionaries(child)


def record_dois(record):
    """Return DOI-like values found on a record."""
    keys = (
        "doi",
        "DOI",
        "itemDoi",
        "itemDOI",
        "identifier",
    )

    return [
        record[key]
        for key in keys
        if isinstance(record.get(key), str)
    ]


def find_matching_record(payload):
    """Find exactly one record matching the configured DOI."""
    target = normalize_doi(DOI)
    matches = []

    # The API search response has documented an itemHits collection.
    # Recursive inspection also supports a single-record JSON response.
    for record in dictionaries(payload):
        if any(
            normalize_doi(value) == target
            for value in record_dois(record)
        ):
            matches.append(record)

    # Deduplicate identical dictionaries in case the response nests
    # a result more than once.
    unique = []
    seen = set()

    for record in matches:
        fingerprint = json.dumps(record, sort_keys=True, default=str)
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(record)

    if len(unique) != 1:
        raise RuntimeError(
            f"Expected exactly one record for {DOI}; "
            f"found {len(unique)}. Use --diagnose to inspect the response."
        )

    return unique[0]


def get_count(record, candidate_keys, label):
    """Return a validated count only if exactly one field is present."""
    present = [
        (key, record[key])
        for key in candidate_keys
        if key in record
    ]

    if len(present) != 1:
        names = [key for key, _ in present]
        raise RuntimeError(
            f"Cannot uniquely identify {label}. "
            f"Candidate fields found: {names or 'none'}. "
            "Inspect the API schema before configuring this metric."
        )

    key, value = present[0]

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError(
            f"Invalid {label} value in field {key}: {value!r}"
        )

    return value


def fetch_record():
    """Query ChemRxiv and return the exact matching record."""
    headers = {
        "Accept": "application/json",
        "User-Agent": "camgur-research-portfolio/1.0",
    }

    response = requests.get(
        API_URL,
        params={
            "term": DOI,
            "limit": 50,
        },
        headers=headers,
        timeout=TIMEOUT,
    )

    if response.status_code == 403:
        raise RuntimeError(
            "ChemRxiv returned HTTP 403. The endpoint may be blocking "
            "automated requests. No metrics were updated."
        )

    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "ChemRxiv did not return valid JSON. "
            "No metrics were updated."
        ) from exc

    return find_matching_record(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Print matched record field names without updating metrics.",
    )
    args = parser.parse_args()

    record = fetch_record()

    if args.diagnose:
        print("Matched DOI:", DOI)
        print("Top-level fields in matched record:")
        print(json.dumps(sorted(record.keys()), indent=2))
        print("\nNested record structure:")
        print(json.dumps(record, indent=2, default=str)[:12000])
        print(
            "\nDiagnostic only: no metrics file was written."
        )
        return

    views = get_count(record, VIEW_KEYS, "views")
    downloads = get_count(record, DOWNLOAD_KEYS, "downloads")

    result = {
        "doi": DOI,
        "version": 1,
        "views": views,
        "downloads": downloads,
        "verified": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": API_URL,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Updated {OUTPUT}")
    print(f"Views: {views}")
    print(f"Downloads: {downloads}")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
