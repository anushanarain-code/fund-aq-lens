
import streamlit as st
import pandas as pd
from matching import analyse_fund
from datetime import date

st.set_page_config(
    page_title="Fund AQ Lens",
    page_icon="🌱",
    layout="wide"
)

st.title("Fund AQ Lens")
st.subheader("Ahimsa Investment Movement | Research & Analysis Studio")

st.write(
    "A research tool for examining the AQ classification "
    "of equity holdings within mutual fund portfolios."
)

st.info(
    "This is a research and analysis prototype. "
    "It does not provide investment recommendations or financial advice."
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Fund AQ Lens")
st.sidebar.write("Research prototype | Version 0.1")
st.sidebar.caption("Exact ISIN matching only")

# --------------------------------------------------
# TABS
# --------------------------------------------------

overview_tab, analysis_tab, methodology_tab = st.tabs(
    ["Overview", "Fund Analysis", "Methodology"]
)

# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

with overview_tab:

    st.header("Overview")

    st.write(
        "Fund AQ Lens examines the exposure of mutual fund "
        "equity portfolios to companies classified under AIM's "
        "Green, Orange and Red AQ categories."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("AQ categories", "3")
    col2.metric("Matching method", "Exact ISIN")
    col3.metric("Proposed coverage threshold", "85%")

    st.markdown("### What the tool does")

    st.markdown(
        """
        - Imports the AIM AQ company reference dataset.
        - Imports mutual fund equity holdings.
        - Matches companies using exact ISINs.
        - Calculates market-value weighted AQ exposure.
        - Identifies unmatched and not-yet-rated holdings.
        - Calculates AQ coverage.
        """
    )

# --------------------------------------------------
# FUND ANALYSIS
# --------------------------------------------------

with analysis_tab:

    st.header("Fund Analysis")

    st.write(
        "Upload the AIM reference dataset and a mutual fund "
        "equity-holdings file to begin."
    )

    st.warning(
        "For this prototype, upload equity holdings only. "
        "Exclude debt, cash and other non-equity assets from "
        "the holdings file so that the exposure denominator "
        "represents total equity market value."
    )

    st.markdown("### 1. Upload the AQ reference dataset")

    aq_file = st.file_uploader(
        "AIM AQ company reference file",
        type=["csv", "xlsx"],
        key="aq_upload"
    )
    aq_sheet = None

    if aq_file is not None and aq_file.name.lower().endswith(".xlsx"):
        excel_file = pd.ExcelFile(aq_file)

        aq_sheet = st.selectbox(
            "Select AQ reference worksheet",
            excel_file.sheet_names,
            index=next(
                (
                    i for i, name in enumerate(excel_file.sheet_names)
                    if name.strip().lower() == "companies"
                ),
                0
            )
        )
    st.markdown("### 2. Upload mutual fund holdings")

    holdings_file = st.file_uploader(
        "Mutual fund equity holdings file",
        type=["csv", "xlsx"],
        key="holdings_upload"
    )

    def read_uploaded_file(uploaded_file, sheet_name=None):
        if uploaded_file.name.lower().endswith(".csv"):
            return pd.read_csv(uploaded_file)

        return pd.read_excel(
           uploaded_file,
           sheet_name=sheet_name if sheet_name else 0
        )

    if aq_file is not None:

        try:
            aq_df = read_uploaded_file(aq_file, aq_sheet)
            st.write("Selected worksheet:", aq_sheet)
            st.write("Data dimensions:", aq_df.shape)
            st.write("Column names:", list(aq_df.columns))
            st.success(
                f"AQ reference loaded: {len(aq_df)} records"
            )

            with st.expander("Preview AQ reference data"):
                st.dataframe(aq_df.head(10), use_container_width=True)

        except Exception as error:
            st.error(f"Could not read AQ reference file: {error}")
            aq_df = None

    else:
        aq_df = None

    if holdings_file is not None:

        try:
            holdings_df = read_uploaded_file(holdings_file)

            st.success(
                f"Holdings file loaded: {len(holdings_df)} records"
            )

            with st.expander("Preview mutual fund holdings"):
                st.dataframe(
                    holdings_df.head(10),
                    use_container_width=True
                )

        except Exception as error:
            st.error(f"Could not read holdings file: {error}")
            holdings_df = None

    else:
        holdings_df = None

    # --------------------------------------------------
    # COLUMN SELECTION AND ANALYSIS
    # --------------------------------------------------

    if aq_df is not None and holdings_df is not None:

        st.markdown("### 3. Identify the required columns")

        holding_columns = list(holdings_df.columns)

        isin_options = [
            column for column in holding_columns
            if "isin" in str(column).lower()
        ]

        value_options = [
            column for column in holding_columns
            if any(
                term in str(column).lower()
                for term in ["market value", "marketvalue", "value"]
            )
        ]

        default_isin = (
            isin_options[0] if isin_options else holding_columns[0]
        )

        default_value = (
            value_options[0]
            if value_options
            else holding_columns[min(1, len(holding_columns) - 1)]
        )

        col1, col2 = st.columns(2)

        with col1:
            isin_column = st.selectbox(
                "Select the ISIN column",
                holding_columns,
                index=holding_columns.index(default_isin)
            )

        with col2:
            market_value_column = st.selectbox(
                "Select the market value column",
                holding_columns,
                index=holding_columns.index(default_value)
            )

        fund_name = st.text_input(
            "Fund name (optional)",
            placeholder="Enter mutual fund scheme name"
        )

        reporting_date = st.date_input(
            "Holdings reporting date",
            value=date.today()
        )

        st.caption(
            "The reporting date should reflect the date of the "
            "holdings disclosure, rather than today's date, "
            "where these differ."
        )

        if st.button("Run Fund AQ Analysis", type="primary"):

            try:

                results = analyse_fund(
                    holdings_df=holdings_df,
                    aq_df=aq_df,
                    isin_column=isin_column,
                    market_value_column=market_value_column
                )

                st.session_state["fund_aq_results"] = results
                st.session_state["fund_aq_name"] = fund_name
                st.session_state["fund_aq_date"] = reporting_date
                st.session_state["aq_filename"] = aq_file.name
                st.session_state["holdings_filename"] = holdings_file.name

            except Exception as error:
                st.error(f"Analysis could not be completed: {error}")

    # --------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------

    if "fund_aq_results" in st.session_state:

        results = st.session_state["fund_aq_results"]

        st.divider()
        st.header("Fund AQ Analysis Results")

        if st.session_state["fund_aq_name"]:
            st.subheader(st.session_state["fund_aq_name"])

        st.caption(
            f"Holdings reporting date: "
            f"{st.session_state['fund_aq_date']}"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "AQ Coverage",
            f"{results['aq_coverage_pct']:.1f}%"
        )

        col2.metric(
            "Matched holdings",
            results["matched_count"]
        )

        col3.metric(
            "Unmatched holdings",
            results["unmatched_count"]
        )

        col4.metric(
            "Total equity value",
            f"₹{results['total_equity_value']:,.0f}"
        )

        if results["aq_coverage_pct"] >= 85:
            st.success(
                "AQ coverage meets the proposed 85% research threshold."
            )
        else:
            st.warning(
                "AQ coverage is below the proposed 85% research threshold. "
                "Interpret the results with caution."
            )

        st.markdown("### AQ Exposure")

        summary = results["summary"].copy()

        summary["Market Value"] = summary["Market Value"].map(
            lambda value: f"₹{value:,.2f}"
        )

        summary["Exposure (%)"] = summary["Exposure (%)"].map(
            lambda value: f"{value:.2f}%"
        )

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True
        )

        chart_data = results["summary"].set_index(
            "AQ Classification"
        )[["Exposure (%)"]]

        st.bar_chart(chart_data)

        st.markdown("### Detailed Holdings and Matching")

        detailed = results["holdings"].copy()

        display_columns = (
            list(holdings_df.columns)
            + ["AQ Classification", "Match Status"]
        )

        display_columns = list(dict.fromkeys(display_columns))

        st.dataframe(
            detailed[display_columns],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### Unmatched Holdings")

        unmatched = detailed[
            detailed["Match Status"] != "Matched"
        ]

        if unmatched.empty:
            st.success("All holdings were matched.")
        else:
            st.write(
                "These holdings have not received an AQ classification "
                "through the reference dataset."
            )

            st.dataframe(
                unmatched[display_columns],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("### Download Analysis")

        csv_data = results["holdings"][display_columns].to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download detailed matching report",
            data=csv_data,
            file_name="fund_aq_matching_report.csv",
            mime="text/csv"
        )

        summary_download = results["summary"].to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download AQ exposure summary",
            data=summary_download,
            file_name="fund_aq_exposure_summary.csv",
            mime="text/csv"
        )

        st.caption(
            f"AQ reference source: "
            f"{st.session_state.get('aq_filename', 'Not recorded')} | "
            f"Holdings source: "
            f"{st.session_state.get('holdings_filename', 'Not recorded')}"
        )

# --------------------------------------------------
# METHODOLOGY
# --------------------------------------------------

with methodology_tab:

    st.header("Methodology")

    st.markdown(
        """
        **1. Reference dataset**

        AIM's company-level AQ classifications are used as the
        reference source. Existing Green, Orange and Red
        classifications are preserved.

        **2. Matching**

        Holdings are matched using exact ISIN identifiers.
        The prototype does not use fuzzy company-name matching.

        **3. Exposure calculation**

        Exposure is calculated as the market value of holdings
        in each AQ category divided by total equity market value.

        **4. Unmatched holdings**

        Holdings without a valid reference match are labelled
        Not Yet Rated. They are not assigned an inferred category.

        **5. AQ coverage**

        AQ coverage is the proportion of total equity market value
        represented by holdings matched to the AQ reference dataset.

        The 85% threshold is a proposed research threshold for
        this prototype, not an official AIM standard.

        **6. Limitations**

        Results depend on the accuracy, completeness and reporting
        date of the source holdings and AQ reference files.
        """
    )

    st.warning(
        "Fund AQ Lens is a research prototype. It does not assess "
        "future performance, recommend investments or provide "
        "financial advice."
    )
