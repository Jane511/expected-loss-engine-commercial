from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CCF_LOOKUP


def _risk_grade_series(df: pd.DataFrame) -> pd.Series:
    if "risk_grade" in df.columns:
        return df["risk_grade"].astype(str)
    return df["internal_risk_grade"].astype(str)


def _is_revolving(df: pd.DataFrame) -> pd.Series:
    if "loan_type" in df.columns:
        return df["loan_type"].astype(str).str.lower().eq("revolving")
    return df["product_type"].astype(str).str.contains("Overdraft", case=False, na=False)


def assign_ccf_bucket(df: pd.DataFrame) -> pd.Series:
    risk_grade = _risk_grade_series(df)
    watchlist = df.get("watchlist_flag", pd.Series(0, index=df.index)).fillna(0).astype(int)
    arrears = df.get("arrears_days", pd.Series(0, index=df.index)).fillna(0)
    revolving = _is_revolving(df)

    weak = revolving & ((watchlist == 1) | (arrears >= 30) | risk_grade.isin(["RG4", "RG5"]))
    average = revolving & ~weak & risk_grade.eq("RG3")

    bucket = pd.Series("not_applicable", index=df.index, dtype="object")
    bucket.loc[revolving] = "strong"
    bucket.loc[average] = "average"
    bucket.loc[weak] = "weak"
    return bucket


def add_ead_columns(df: pd.DataFrame, ccf_multiplier: float = 1.0) -> pd.DataFrame:
    out = df.copy()
    revolving = _is_revolving(out)
    out["undrawn_amount"] = (out["limit_amount"] - out["drawn_balance"]).clip(lower=0.0)
    out["ccf_bucket"] = assign_ccf_bucket(out)
    out["ccf_base"] = out["ccf_bucket"].map(CCF_LOOKUP).fillna(0.0)
    out["ccf_applied"] = np.where(revolving, np.minimum(out["ccf_base"] * ccf_multiplier, 1.0), 0.0)
    out["ead"] = np.where(
        revolving,
        out["drawn_balance"] + out["undrawn_amount"] * out["ccf_applied"],
        out["drawn_balance"],
    )
    out["ead"] = out["ead"].round(2)
    return out

