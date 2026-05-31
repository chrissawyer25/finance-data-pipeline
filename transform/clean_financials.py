import pandas as pd
import os

# --- Load raw data ---
raw_path = os.path.join(os.path.dirname(__file__), "..", "extract", "raw_financials.csv")
df = pd.read_csv(raw_path)

# --- Pivot: rows = (company, year), columns = metrics ---
pivoted = df.pivot_table(
    index=["company", "year"],
    columns="metric",
    values="value",
    aggfunc="last"
).reset_index()

pivoted.columns.name = None  # clean up column index name

# --- Rename columns for clarity ---
pivoted.rename(columns={
    "Revenues":                          "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",  # Google/Meta label
    "GrossProfit":                       "gross_profit",
    "OperatingIncomeLoss":               "operating_income",
    "NetIncomeLoss":                     "net_income",
    "Assets":                            "total_assets",
    "LiabilitiesAndStockholdersEquity":  "total_liabilities_equity"
}, inplace=True)

# Consolidate revenue column if both exist
if "revenue" not in pivoted.columns:
    pivoted["revenue"] = None

# --- Ensure all expected columns exist (fill missing with None) ---
expected = ["revenue", "gross_profit", "operating_income", "net_income",
            "total_assets", "total_liabilities_equity"]

for col in expected:
    if col not in pivoted.columns:
        pivoted[col] = None

# --- Convert to numeric ---
for col in expected:
    pivoted[col] = pd.to_numeric(pivoted[col], errors="coerce")

# --- Convert values from raw dollars to billions (easier to read) ---
for col in expected:
    pivoted[col] = pivoted[col] / 1_000_000_000

# --- Calculate KPIs ---

# Margin %
pivoted["gross_margin_pct"]     = (pivoted["gross_profit"]     / pivoted["revenue"] * 100).round(2)
pivoted["operating_margin_pct"] = (pivoted["operating_income"] / pivoted["revenue"] * 100).round(2)
pivoted["net_margin_pct"]       = (pivoted["net_income"]       / pivoted["revenue"] * 100).round(2)

# YoY Revenue Growth %
pivoted = pivoted.sort_values(["company", "year"])
pivoted["revenue_growth_pct"] = (
    pivoted.groupby("company")["revenue"]
    .pct_change() * 100
).round(2)

# Return on Assets %
pivoted["return_on_assets_pct"] = (pivoted["net_income"] / pivoted["total_assets"] * 100).round(2)

# --- Round dollar figures to 2 decimal places ---
for col in expected:
    pivoted[col] = pivoted[col].round(2)

# --- Reorder columns cleanly ---
final_cols = [
    "company", "year",
    "revenue", "gross_profit", "operating_income", "net_income",
    "total_assets", "total_liabilities_equity",
    "gross_margin_pct", "operating_margin_pct", "net_margin_pct",
    "revenue_growth_pct", "return_on_assets_pct"
]

# Only keep columns that exist
final_cols = [c for c in final_cols if c in pivoted.columns]
pivoted = pivoted[final_cols]

# --- Filter to last 5 years per company ---
pivoted = pivoted[pivoted["year"] >= pivoted["year"].max() - 4]

# --- Save output ---
out_path = os.path.join(os.path.dirname(__file__), "clean_financials.csv")
pivoted.to_csv(out_path, index=False)

print(f"Done! {len(pivoted)} rows saved to clean_financials.csv\n")
print(pivoted.to_string(index=False))