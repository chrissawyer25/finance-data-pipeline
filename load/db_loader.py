import pandas as pd
import sqlite3
import os

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSFORM_DIR = os.path.join(BASE_DIR, "..", "transform")
DB_PATH = os.path.join(BASE_DIR, "financials.db")
CSV_PATH = os.path.join(TRANSFORM_DIR, "clean_financials.csv")

def create_tables(conn):
    """Create tables if they don't exist"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financials (
            id                        INTEGER PRIMARY KEY AUTOINCREMENT,
            company                   TEXT    NOT NULL,
            year                      INTEGER NOT NULL,
            revenue                   REAL,
            gross_profit              REAL,
            operating_income          REAL,
            net_income                REAL,
            total_assets              REAL,
            total_liabilities_equity  REAL,
            gross_margin_pct          REAL,
            operating_margin_pct      REAL,
            net_margin_pct            REAL,
            revenue_growth_pct        REAL,
            return_on_assets_pct      REAL,
            UNIQUE(company, year)
        )
    """)
    conn.commit()
    print("Tables ready.")


def load_data(conn, df):
    """Insert rows, replace if company+year already exists"""
    rows_loaded = 0
    rows_skipped = 0

    for _, row in df.iterrows():
        try:
            conn.execute("""
                INSERT OR REPLACE INTO financials (
                    company, year,
                    revenue, gross_profit, operating_income, net_income,
                    total_assets, total_liabilities_equity,
                    gross_margin_pct, operating_margin_pct, net_margin_pct,
                    revenue_growth_pct, return_on_assets_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["company"],
                int(row["year"]),
                row.get("revenue"),
                row.get("gross_profit"),
                row.get("operating_income"),
                row.get("net_income"),
                row.get("total_assets"),
                row.get("total_liabilities_equity"),
                row.get("gross_margin_pct"),
                row.get("operating_margin_pct"),
                row.get("net_margin_pct"),
                row.get("revenue_growth_pct"),
                row.get("return_on_assets_pct"),
            ))
            rows_loaded += 1
        except Exception as e:
            print(f"  Skipped row ({row.get('company')}, {row.get('year')}): {e}")
            rows_skipped += 1

    conn.commit()
    print(f"Loaded {rows_loaded} rows. Skipped {rows_skipped} rows.")


def run_sample_queries(conn):
    """Run a few SQL queries to verify the data looks right"""

    print("\n--- Top 5 rows ---")
    df = pd.read_sql("SELECT * FROM financials LIMIT 5", conn)
    print(df.to_string(index=False))

    print("\n--- Most recent year net margins by company ---")
    df = pd.read_sql("""
        SELECT company, year, revenue, net_income, net_margin_pct
        FROM financials
        WHERE year = (SELECT MAX(year) FROM financials)
        ORDER BY net_margin_pct DESC
    """, conn)
    print(df.to_string(index=False))

    print("\n--- Average revenue growth % per company ---")
    df = pd.read_sql("""
        SELECT company,
               ROUND(AVG(revenue_growth_pct), 2) AS avg_revenue_growth_pct
        FROM financials
        WHERE revenue_growth_pct IS NOT NULL
        GROUP BY company
        ORDER BY avg_revenue_growth_pct DESC
    """, conn)
    print(df.to_string(index=False))

    print("\n--- Highest operating margins across all years ---")
    df = pd.read_sql("""
        SELECT company, year, revenue, operating_margin_pct
        FROM financials
        WHERE operating_margin_pct IS NOT NULL
        ORDER BY operating_margin_pct DESC
        LIMIT 10
    """, conn)
    print(df.to_string(index=False))


def main():
    print(f"Loading data from: {CSV_PATH}")
    print(f"Database path:     {DB_PATH}\n")

    # Load CSV
    df = pd.read_csv(CSV_PATH)
    print(f"Read {len(df)} rows from clean_financials.csv")

    # Connect to SQLite (creates file if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)

    # Create tables
    create_tables(conn)

    # Load data
    load_data(conn, df)

    # Verify with sample queries
    run_sample_queries(conn)

    conn.close()
    print(f"\nDone. Database saved to: {DB_PATH}")


if __name__ == "__main__":
    main()