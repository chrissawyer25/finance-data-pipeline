import requests

HEADERS = {"User-Agent": "chris@email.com"}  # Replace with your real email

COMPANIES = {
    "Apple":     "0000320193",
    "Microsoft": "0000789019",
    "Google":    "0001652044",
    "Amazon":    "0001018724",
    "Meta":      "0001326801"
}

# Common revenue-related keywords to search for
KEYWORDS = ["revenue", "Revenue", "Sales", "sales"]

for company, cik in COMPANIES.items():
    print(f"\n--- {company} ---")
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    gaap_keys = list(data["facts"]["us-gaap"].keys())

    matches = [k for k in gaap_keys if any(kw in k for kw in KEYWORDS)]
    for m in matches:
        print(f"  {m}")