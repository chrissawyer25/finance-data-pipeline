import requests
import pandas as pd

# --- Config ---
HEADERS = {"User-Agent": "chris@email.com"}  # EDGAR requires a user-agent header

COMPANIES = {
    "Apple":     "0000320193",
    "Microsoft": "0000789019",
    "Google":    "0001652044",
    "Amazon":    "0001018724",
    "Meta":      "0001326801"
}

# --- Helper: pull a specific financial metric from EDGAR ---
def get_metric(cik, metric):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Failed to fetch data for CIK {cik}")
        return pd.DataFrame()

    data = response.json()

    try:
        # Most metrics live under us-gaap
        facts = data["facts"]["us-gaap"][metric]["units"]["USD"]
        df = pd.DataFrame(facts)

        # Keep only annual 10-K filings
        df = df[df["form"] == "10-K"]

        # Keep relevant columns
        df = df[["end", "val", "accn", "form"]].copy()
        df.rename(columns={"end": "date", "val": "value"}, inplace=True)

        # Drop duplicates keeping most recent filing per year
        df["year"] = pd.to_datetime(df["date"]).dt.year
        df = df.sort_values("date").drop_duplicates(subset="year", keep="last")

        # Keep last 5 years
        df = df[df["year"] >= df["year"].max() - 4]
        df = df[["year", "date", "value"]].reset_index(drop=True)
        df["metric"] = metric

        return df

    except KeyError:
        print(f"Metric '{metric}' not found for CIK {cik}")
        return pd.DataFrame()


# --- Main: pull metrics for all companies ---
def extract_all():
    metrics = [
        "Revenues",               # Revenue / Net Sales
        "GrossProfit",            # Gross Profit
        "OperatingIncomeLoss",    # Operating Income
        "NetIncomeLoss",          # Net Income
        "Assets",                 # Total Assets
        "LiabilitiesAndStockholdersEquity"  # Total Liabilities + Equity
    ]

    all_data = []

    for company, cik in COMPANIES.items():
        print(f"Pulling data for {company}...")
        for metric in metrics:
            df = get_metric(cik, metric)
            if not df.empty:
                df["company"] = company
                df["cik"] = cik
                all_data.append(df)

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined = combined[["company", "cik", "year", "date", "metric", "value"]]
        combined.to_csv("raw_financials.csv", index=False)
        print(f"\nDone! {len(combined)} rows saved to raw_financials.csv")
        return combined
    else:
        print("No data extracted.")
        return pd.DataFrame()


if __name__ == "__main__":
    df = extract_all()
    print(df.head(20))