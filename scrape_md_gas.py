#!/usr/bin/env python3
"""
AAA Maryland Gas Price Scraper
Scrapes current average gas prices for Maryland and all metro areas,
appends results to a CSV file for historical tracking.
"""

import csv
import os
import sys
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

URL = "https://gasprices.aaa.com/?state=MD"
OUTPUT_FILE = "data/md_gas_prices.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CSV_COLUMNS = [
    "scraped_date",
    "price_as_of",
    "location",
    "regular",
    "mid_grade",
    "premium",
    "diesel",
]


def fetch_page(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_price(text: str) -> str:
    """Strip $ and whitespace, return clean price string or empty."""
    return text.strip().lstrip("$").strip() if text else ""


def parse_price_as_of(soup: BeautifulSoup) -> str:
    """Extract the 'Price as of' date shown on the page."""
    for tag in soup.find_all(string=True):
        if "Price as of" in tag:
            # grab the text right after this node
            parent = tag.parent
            text = parent.get_text(" ", strip=True)
            if "Price as of" in text:
                parts = text.split("Price as of")
                if len(parts) > 1:
                    return parts[-1].strip()
    return str(date.today())


def parse_state_table(soup: BeautifulSoup) -> dict:
    """Parse the statewide Maryland average prices table."""
    h1 = soup.find("h1", string=lambda s: s and "Maryland average gas prices" in s)
    if not h1:
        return {}

    table = h1.find_next("table")
    if not table:
        return {}

    rows = table.find_all("tr")
    prices = {}
    for row in rows:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        label = cells[0].get_text(strip=True)
        if label == "Current Avg." and len(cells) >= 5:
            prices = {
                "regular": parse_price(cells[1].get_text()),
                "mid_grade": parse_price(cells[2].get_text()),
                "premium": parse_price(cells[3].get_text()),
                "diesel": parse_price(cells[4].get_text()),
            }
            break
    return prices


def parse_metro_tables(soup: BeautifulSoup) -> list[dict]:
    """Parse each metro area's current average prices."""
    metro_section = soup.find("h2", string=lambda s: s and "metro average" in s.lower())
    if not metro_section:
        return []

    results = []
    # Each metro is an h3 followed by a table
    for h3 in metro_section.find_all_next("h3"):
        metro_name = h3.get_text(strip=True)
        # Stop if we've hit the next major section
        if metro_name.lower().startswith("state gas"):
            break

        table = h3.find_next("table")
        if not table:
            continue

        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            label = cells[0].get_text(strip=True)
            if label == "Current Avg." and len(cells) >= 5:
                results.append({
                    "location": metro_name,
                    "regular": parse_price(cells[1].get_text()),
                    "mid_grade": parse_price(cells[2].get_text()),
                    "premium": parse_price(cells[3].get_text()),
                    "diesel": parse_price(cells[4].get_text()),
                })
                break

    return results


def append_to_csv(rows: list[dict], filepath: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main():
    print(f"[{datetime.now().isoformat()}] Fetching {URL} ...")
    soup = fetch_page(URL)

    scraped_date = str(date.today())
    price_as_of = parse_price_as_of(soup)
    print(f"  Price as of: {price_as_of}")

    # Statewide
    state_prices = parse_state_table(soup)
    if not state_prices:
        print("ERROR: Could not parse statewide prices table.", file=sys.stderr)
        sys.exit(1)

    rows = [{"scraped_date": scraped_date, "price_as_of": price_as_of,
             "location": "Maryland (Statewide)", **state_prices}]

    # Metro areas
    metro_rows = parse_metro_tables(soup)
    for m in metro_rows:
        rows.append({"scraped_date": scraped_date, "price_as_of": price_as_of, **m})

    append_to_csv(rows, OUTPUT_FILE)

    print(f"  Saved {len(rows)} rows to {OUTPUT_FILE}")
    for r in rows:
        print(f"  {r['location']}: Regular=${r['regular']} Mid=${r['mid_grade']} "
              f"Premium=${r['premium']} Diesel={r['diesel']}")


if __name__ == "__main__":
    main()
