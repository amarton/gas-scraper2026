#!/usr/bin/env python3
"""
AAA Maryland Gas Price Scraper
Scrapes statewide + all metro area average gas prices for Maryland.
Appends results to a CSV file for historical tracking.
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
    return text.strip().lstrip("$").strip() if text else ""


def parse_current_row(table) -> dict | None:
    """Extract the 'Current Avg.' row from a prices table."""
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if cells and cells[0].get_text(strip=True) == "Current Avg." and len(cells) >= 5:
            return {
                "regular":   parse_price(cells[1].get_text()),
                "mid_grade": parse_price(cells[2].get_text()),
                "premium":   parse_price(cells[3].get_text()),
                "diesel":    parse_price(cells[4].get_text()),
            }
    return None


def scrape(soup: BeautifulSoup) -> list[dict]:
    scraped_date = str(date.today())
    rows = []

    # --- Statewide: find the h1 then the next table ---
    h1 = soup.find("h1")
    if h1:
        table = h1.find_next("table")
        if table:
            prices = parse_current_row(table)
            if prices:
                rows.append({"scraped_date": scraped_date,
                             "location": "Maryland (Statewide)", **prices})

    # --- Metro areas: every h3 inside the metro section ---
    metro_h2 = soup.find("h2", string=lambda s: s and "metro" in s.lower())
    if metro_h2:
        for h3 in metro_h2.find_next_siblings():
            # Stop when we hit the next h2
            if h3.name == "h2":
                break
            if h3.name == "h3":
                metro_name = h3.get_text(strip=True)
                table = h3.find_next("table")
                if table:
                    prices = parse_current_row(table)
                    if prices:
                        rows.append({"scraped_date": scraped_date,
                                     "location": metro_name, **prices})

    return rows


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

    rows = scrape(soup)

    if not rows:
        print("ERROR: No price data found.", file=sys.stderr)
        sys.exit(1)

    append_to_csv(rows, OUTPUT_FILE)

    print(f"  Saved {len(rows)} rows to {OUTPUT_FILE}\n")
    print(f"  {'Location':<30} {'Regular':>8} {'Mid':>8} {'Premium':>8} {'Diesel':>8}")
    print(f"  {'-'*66}")
    for r in rows:
        print(f"  {r['location']:<30} {r['regular']:>8} {r['mid_grade']:>8} "
              f"{r['premium']:>8} {r['diesel']:>8}")


if __name__ == "__main__":
    main()
