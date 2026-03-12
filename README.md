# Maryland Gas Price Scraper

Scrapes daily average gas prices for Maryland (statewide + all metro areas) from [AAA Gas Prices](https://gasprices.aaa.com/?state=MD) and appends them to a CSV file. Runs automatically via GitHub Actions every day at 10 AM ET.

## Data collected

- **Statewide Maryland average**
- **Metro areas:** Salisbury, Baltimore, Hagerstown, Washington (MD), Cumberland, Bowie-St. Charles, Annapolis, Frederick

### Columns

| Column | Description |
|---|---|
| `scraped_date` | Date the script ran (YYYY-MM-DD) |
| `price_as_of` | Date AAA last updated the price |
| `location` | Statewide or metro name |
| `regular` | Regular unleaded avg price ($) |
| `mid_grade` | Mid-grade avg price ($) |
| `premium` | Premium avg price ($) |
| `diesel` | Diesel avg price ($) |

## Setup

### 1. Create a GitHub repository

```bash
git init md-gas-prices
cd md-gas-prices
# Copy all files here
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/md-gas-prices.git
git push -u origin main
```

### 2. Enable GitHub Actions write permissions

In your repo: **Settings → Actions → General → Workflow permissions**
→ select **Read and write permissions** → Save.

### 3. That's it!

The workflow runs daily at 10 AM ET. You can also trigger it manually via
**Actions → Daily MD Gas Price Scraper → Run workflow**.

## Run locally

```bash
pip install -r requirements.txt
python scrape_md_gas.py
# Output saved to data/md_gas_prices.csv
```

## CSV location

`data/md_gas_prices.csv` — committed to the repo after each run, giving you a full git-tracked history.
