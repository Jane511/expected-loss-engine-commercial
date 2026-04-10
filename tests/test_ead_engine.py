from __future__ import annotations

import pandas as pd

from src.ead_engine import add_ead_columns


def test_term_loan_ead_equals_drawn_balance() -> None:
    df = pd.DataFrame(
        [
            {
                "facility_id": "FAC-00001",
                "product_type": "SME Cash Flow Term Loan",
                "loan_type": "term",
                "limit_amount": 500_000.0,
                "drawn_balance": 420_000.0,
                "internal_risk_grade": "RG2",
                "watchlist_flag": 0,
                "arrears_days": 0,
            }
        ]
    )
    result = add_ead_columns(df)
    assert result.loc[0, "ead"] == 420_000.0
    assert result.loc[0, "ccf_applied"] == 0.0


def test_revolving_ead_uses_weak_ccf_for_watchlist_exposure() -> None:
    df = pd.DataFrame(
        [
            {
                "facility_id": "FAC-00002",
                "product_type": "Overdraft / Revolving Working Capital",
                "loan_type": "revolving",
                "limit_amount": 1_000_000.0,
                "drawn_balance": 400_000.0,
                "internal_risk_grade": "RG5",
                "watchlist_flag": 1,
                "arrears_days": 45,
            }
        ]
    )
    result = add_ead_columns(df)
    assert result.loc[0, "ccf_bucket"] == "weak"
    assert result.loc[0, "ccf_applied"] == 0.75
    assert result.loc[0, "ead"] == 850_000.0

