import pandas as pd
import re

AQ_CATEGORIES = ["Green", "Orange", "Red"]


def normalise_isin(value):
    """Standardise ISINs without attempting fuzzy matching."""
    if pd.isna(value):
        return None

    value = str(value).strip().upper()
    return value if value else None


def validate_isin(value):
    """
    Check the basic structure of an ISIN.
    This does not verify the ISIN checksum or existence.
    """
    isin = normalise_isin(value)

    if isin is None:
        return "Missing ISIN"

    pattern = r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"

    if not re.fullmatch(pattern, isin):
        return "Invalid ISIN format"

    return "Valid ISIN format"


def analyse_fund(
    holdings_df,
    aq_df,
    isin_column,
    market_value_column
):
    """
    Match equity holdings against the AIM AQ reference dataset.

    The market value denominator includes all rows supplied.
    Therefore, supply equity holdings only, excluding debt and cash.
    """

    required_aq_columns = ["ISIN Code", "Category"]
    required_holdings_columns = [
        isin_column,
        market_value_column
    ]

    for column in required_aq_columns:
        if column not in aq_df.columns:
            raise ValueError(
                f"AQ reference file is missing: {column}"
            )

    for column in required_holdings_columns:
        if column not in holdings_df.columns:
            raise ValueError(
                f"Holdings file is missing: {column}"
            )

    aq = aq_df.copy()
    holdings = holdings_df.copy()

    # Standardise reference ISINs
    aq["_ISIN"] = aq["ISIN Code"].apply(normalise_isin)

    if aq["_ISIN"].isna().any():
        raise ValueError("AQ reference contains missing ISINs.")

    if aq["_ISIN"].duplicated().any():
        raise ValueError(
            "AQ reference contains duplicate ISINs. "
            "Resolve these before analysis."
        )

    # Validate source classifications
    aq["_AQ_Category"] = aq["Category"].astype("string").str.strip()

    invalid_categories = (
        aq["_AQ_Category"].isna()
        | ~aq["_AQ_Category"].isin(AQ_CATEGORIES)
    )

    if invalid_categories.any():
        raise ValueError(
            "AQ reference contains missing or unexpected categories. "
            "Review the source before analysis."
        )

    # Standardise fund holdings
    holdings["_ISIN"] = holdings[isin_column].apply(
        normalise_isin
    )
    # Validate the structure of each holdings ISIN
    holdings["ISIN Validation"] = holdings[isin_column].apply(
        validate_isin
    )
    market_values = (
        holdings[market_value_column]
        .astype("string")
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip()
    )

    holdings["_Market_Value"] = pd.to_numeric(
        market_values,
        errors="coerce"
    )

    if holdings["_Market_Value"].isna().any():
        raise ValueError(
            "Some market values are missing or non-numeric. "
            "Resolve these before calculating exposure."
        )

    if (holdings["_Market_Value"] < 0).any():
        raise ValueError(
            "Negative market values found. "
            "Review the holdings file."
        )

    total_equity_value = holdings["_Market_Value"].sum()

    if total_equity_value <= 0:
        raise ValueError(
            "Total equity market value must be greater than zero."
        )

    # Exact ISIN matching only
    reference = aq[["_ISIN", "_AQ_Category"]]

    result = holdings.merge(
        reference,
        on="_ISIN",
        how="left",
        validate="many_to_one"
    )

    # Explicitly distinguish unmatched holdings
    result["AQ Classification"] = result["_AQ_Category"].fillna(
        "Not Yet Rated"
    )

    result["Match Status"] = "Unmatched"

    result.loc[
        result["_ISIN"].isna(),
        "Match Status"
        ] = "Missing ISIN"

    result.loc[
        result["_AQ_Category"].notna(),
        "Match Status"
    ] = "Matched"

    result.loc[
        result["ISIN Validation"] == "Invalid ISIN format",
        "Match Status"
    ] = "Invalid ISIN"

    # Exposure by classification
    categories = AQ_CATEGORIES + ["Not Yet Rated"]

    exposure = (
        result.groupby("AQ Classification")["_Market_Value"]
        .sum()
        .reindex(categories, fill_value=0)
    )

    summary = pd.DataFrame({
        "AQ Classification": categories,
        "Market Value": exposure.values,
        "Exposure (%)": (
            exposure.values / total_equity_value * 100
        )
    })

    rated_value = exposure[AQ_CATEGORIES].sum()

    coverage_pct = (
        rated_value / total_equity_value * 100
    )

    return {
        "holdings": result,
        "summary": summary,
        "total_equity_value": total_equity_value,
        "rated_value": rated_value,
        "unrated_value": exposure["Not Yet Rated"],
        "aq_coverage_pct": coverage_pct,
        "holding_count": len(result),
        "matched_count": int(result["_AQ_Category"].notna().sum()),
        "unmatched_count": int(result["_AQ_Category"].isna().sum())
    }