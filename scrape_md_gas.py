#!/usr/bin/env python3
"""
AAA Maryland Gas Price Scraper
Scrapes Maryland average gas prices from the AAA state averages page
(which renders server-side without requiring JavaScript).
Appends results to a CSV file for historical tracking.
"""

import csv
import os
import sys
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

URL = "https://gasprices.aaa.com/state-gas-price-averages/"
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


def parse_maryland(soup: BeautifulSoup) -> dict:
    """Find Maryland row in the state averages table."""
    table = soup.find("table")
    if not table:
        return {}

    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        state_name = cells[0].get_text(strip=True)
        if "Maryland" in state_name and len(cells) >= 5:
            return {
                "regular":   parse_price(cells[1].get_text()),
                "mid_grade": parse_price(cells[2].get_text()),
                "premium":   parse_price(cells[3].get_text()),
                "diesel":    parse_price(cells[4].get_text()),
            }
    return {}


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

    prices = parse_maryland(soup)
    if not prices:
        print("ERROR: Could not find Maryland row in the state averages table.", file=sys.stderr)
        sys.exit(1)

    row = {
        "scraped_date": str(date.today()),
        "location": "Maryland (Statewide)",
        **prices,
    }

    append_to_csv([row], OUTPUT_FILE)

    print(f"  Saved to {OUTPUT_FILE}")
    print(f"  Maryland | Regular: ${row['regular']} | Mid: ${row['mid_grade']} | "
          f"Premium: ${row['premium']} | Diesel: ${row['diesel']}")


if __name__ == "__main__":
    main()
