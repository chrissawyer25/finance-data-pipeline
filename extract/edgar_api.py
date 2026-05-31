import requests
import pandas as pd

# --- Config ---
HEADERS = {"User-Agent": "chris@email.com"}  # Replace with your real email

COMPANIES = {
    "Apple":     "0000320193",
    "Microsoft": "0000789019",
    "Google":    "0001652044",
    "Amazon":    "0001018724",
    "Meta":      "0001326801"
}

# Try these in order — first one with 10-K data wins
REVENUE_LABELS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
]

# --- Helper: pull a specific metric from already-fetched company data ---
def get_metric(cik, metric, company_data):
    try:
        facts = company_data["facts"]["us-gaap"][metric]["units"]["USD"]
        df = pd.DataFrame(facts)

        # Only annual 10-K filings
        df = df[df["form"] == "10-K"]
        if df.empty:
            return pd.DataFrame()

        df = df[["end", "val"]].copy()
        df.rename(columns={"end": "date", "val": "value"}, inplace=True)
        df["year"] = pd.to_datetime(df["date"]).dt.year
        df = df.sort_values("date").drop_duplicates(subset="year", keep="last")
        df = df[df["year"] >= df["year"].max() - 4]
        df = df[["year", "date", "value"]].reset_index(drop=True)
        return df

    except KeyError:
        return pd.DataFrame()


# --- Helper: try all revenue labels, return first with data ---
def get_revenue(cik, company_data):
    for label in REVENUE_LABELS:
        df = get_metric(cik, label, company_data)
        if not df.empty:
            print(f"  Revenue: using '{label}'")
            df["metric"] = "revenue"
            return df
    print(f"  Revenue: no data found for CIK {cik}")
    return pd.DataFrame()


# --- Main ---
def extract_all():
    OTHER_METRICS = {
        "GrossProfit":                      "gross_profit",
        "OperatingIncomeLoss":              "operating_income",
        "NetIncomeLoss":                    "net_income",
        "Assets":                           "total_assets",
        "LiabilitiesAndStockholdersEquity": "total_liabilities_equity"
    }

    all_data = []

    for company, cik in COMPANIES.items():
        print(f"\nPulling data for {company}...")

        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"  Failed to fetch {company}")
            continue
        company_data = response.json()

        # Revenue
        df = get_revenue(cik, company_data)
        if not df.empty:
            df["company"] = company
            df["cik"] = cik
            all_data.append(df)

        # All other metrics
        for edgar_label, clean_name in OTHER_METRICS.items():
            df = get_metric(cik, edgar_label, company_data)
            if not df.empty:
                df["metric"] = clean_name
                df["company"] = company
                df["cik"] = cik
                print(f"  {clean_name}: OK")
                all_data.append(df)
            else:
                print(f"  {clean_name}: not found")

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
    print("\nSample output:")
    print(df.head(20))