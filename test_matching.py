
import pandas as pd
from matching import analyse_fund

# Load the original AQ reference dataset
aq_df = pd.read_csv(
    r"C:\Users\divya\aq-prototype\data\aim_companies.csv"
)

# Pick one real company from each AQ category
sample_holdings = []

for category, value in [
    ("Green", 400000),
    ("Orange", 300000),
    ("Red", 200000)
]:
    company = aq_df[aq_df["Category"] == category].iloc[0]

    sample_holdings.append({
        "Company": company["Company Name"],
        "ISIN": company["ISIN Code"],
        "Market Value": value
    })

# Add one deliberately unknown ISIN to test unmatched handling
sample_holdings.append({
    "Company": "Unmatched test company",
    "ISIN": "ZZZZZZZZZZZ1",
    "Market Value": 100000
})

holdings_df = pd.DataFrame(sample_holdings)

# Run the matching engine
result = analyse_fund(
    holdings_df=holdings_df,
    aq_df=aq_df,
    isin_column="ISIN",
    market_value_column="Market Value"
)

print("\n--- FUND AQ TEST ---")
print("\nExposure summary:")
print(result["summary"].to_string(index=False))

print("\nAQ coverage:", round(result["aq_coverage_pct"], 2), "%")
print("Matched holdings:", result["matched_count"])
print("Unmatched holdings:", result["unmatched_count"])
print("Total equity value:", result["total_equity_value"])

print("\nDetailed matching:")
print(
    result["holdings"][
        ["Company", "ISIN", "AQ Classification", "Match Status"]
    ].to_string(index=False)
)