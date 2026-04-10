from __future__ import annotations

import pandas as pd

from .ead_engine import add_ead_columns


PD_COLUMNS = [
    "facility_id",
    "pd_model_stream",
    "score",
    "score_band",
    "risk_grade",
    "pd_final",
    "default_horizon_months",
    "pd_model_name",
    "pd_model_version",
    "as_of_date",
]

LGD_COLUMNS = [
    "facility_id",
    "conduct_classification",
    "lgd_base",
    "lgd_adj_lvr",
    "lgd_adj_stage",
    "lgd_adj_industry",
    "lgd_adj_pd_band",
    "lgd_adj_dscr",
    "lgd_adj_conduct",
    "lgd_adjusted",
    "downturn_scalar",
    "lgd_downturn",
    "lgd_final",
]


def _prepare_lgd_inputs(lgd_df: pd.DataFrame) -> pd.DataFrame:
    out = lgd_df.copy()
    if "facility_id" not in out.columns and "loan_id" in out.columns:
        out = out.rename(columns={"loan_id": "facility_id"})
    missing = [column for column in LGD_COLUMNS if column not in out.columns]
    if missing:
        raise ValueError(f"LGD input is missing required columns: {missing}")
    return out[LGD_COLUMNS]


def build_expected_loss_dataset(
    portfolio_df: pd.DataFrame,
    pd_df: pd.DataFrame,
    lgd_df: pd.DataFrame,
) -> pd.DataFrame:
    pd_missing = [column for column in PD_COLUMNS if column not in pd_df.columns]
    if pd_missing:
        raise ValueError(f"PD input is missing required columns: {pd_missing}")
    if "facility_id" not in portfolio_df.columns:
        raise ValueError("Portfolio input must include facility_id")

    merged = portfolio_df.merge(pd_df[PD_COLUMNS], on="facility_id", how="left", validate="one_to_one")
    merged = merged.merge(_prepare_lgd_inputs(lgd_df), on="facility_id", how="left", validate="one_to_one")

    if merged["pd_final"].isna().any():
        missing_ids = merged.loc[merged["pd_final"].isna(), "facility_id"].head(5).tolist()
        raise ValueError(f"Missing PD rows for facility_id values such as: {missing_ids}")
    if merged["lgd_final"].isna().any():
        missing_ids = merged.loc[merged["lgd_final"].isna(), "facility_id"].head(5).tolist()
        raise ValueError(f"Missing LGD rows for facility_id values such as: {missing_ids}")

    merged = add_ead_columns(merged)
    merged["expected_loss"] = (merged["pd_final"] * merged["lgd_final"] * merged["ead"]).round(2)
    merged["el_rate"] = (merged["expected_loss"] / merged["ead"].replace(0, pd.NA)).fillna(0.0).round(6)

    ordered_columns = [
        "facility_id",
        "borrower_id",
        "borrower_name",
        "product_type",
        "industry",
        "region",
        "loan_type",
        "security_type",
        "loan_term_months",
        "limit_amount",
        "drawn_balance",
        "undrawn_amount",
        "ccf_bucket",
        "ccf_applied",
        "ead",
        "interest_rate",
        "score",
        "score_band",
        "risk_grade",
        "pd_model_stream",
        "pd_final",
        "lgd_final",
        "expected_loss",
        "el_rate",
        "annual_revenue",
        "ebitda",
        "dscr",
        "arrears_days",
        "watchlist_flag",
        "internal_risk_grade",
        "borrower_strength",
        "conduct_classification",
        "default_horizon_months",
        "pd_model_name",
        "pd_model_version",
        "as_of_date",
        "lgd_base",
        "lgd_adj_lvr",
        "lgd_adj_stage",
        "lgd_adj_industry",
        "lgd_adj_pd_band",
        "lgd_adj_dscr",
        "lgd_adj_conduct",
        "lgd_adjusted",
        "downturn_scalar",
        "lgd_downturn",
    ]
    return merged[ordered_columns]

