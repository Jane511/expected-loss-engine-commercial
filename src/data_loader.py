from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    AS_OF_DATE,
    DEFAULT_INPUT_FILES,
    INDUSTRY_SETTINGS,
    INPUT_DIR,
    N_FACILITIES,
    PRODUCT_SETTINGS,
    RANDOM_SEED,
    REGION_FACTORS,
    RISK_GRADE_PD_LOOKUP,
    RISK_GRADE_TO_SCORE_BAND,
    STRESS_SCENARIOS,
)
from .utils import ensure_directories, save_dataframe


def _resolve_input_dir(input_dir: str | Path | None) -> Path:
    return Path(input_dir) if input_dir is not None else INPUT_DIR


def _assign_risk_grade(risk_score: float) -> str:
    if risk_score < 0.22:
        return "RG1"
    if risk_score < 0.30:
        return "RG2"
    if risk_score < 0.40:
        return "RG3"
    if risk_score < 0.54:
        return "RG4"
    return "RG5"


def _borrower_strength(risk_grade: str, watchlist_flag: int, arrears_days: int) -> str:
    if watchlist_flag or arrears_days >= 45 or risk_grade in {"RG4", "RG5"}:
        return "weak"
    if risk_grade == "RG3":
        return "average"
    return "strong"


def _security_bucket(product_type: str, security_type: str) -> str:
    if product_type == "Property Backed Loan":
        return "residential" if "Residential" in security_type else "commercial"
    if product_type == "Overdraft / Revolving Working Capital":
        return "unsecured" if security_type == "Unsecured" else "secured"
    if security_type == "Unsecured":
        return "unsecured"
    if security_type == "Receivables Security":
        return "partially_secured"
    return "secured"


def _base_lgd(product_type: str, security_bucket: str) -> float:
    if product_type == "Property Backed Loan":
        return 0.20 if security_bucket == "residential" else 0.28
    if product_type == "Overdraft / Revolving Working Capital":
        return 0.55 if security_bucket == "secured" else 0.68
    if security_bucket == "secured":
        return 0.42
    if security_bucket == "partially_secured":
        return 0.50
    return 0.60


def _build_portfolio_dataset(n_facilities: int = N_FACILITIES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    product_names = tuple(PRODUCT_SETTINGS.keys())
    product_weights = np.array([0.40, 0.32, 0.28], dtype=float)
    industry_names = tuple(INDUSTRY_SETTINGS.keys())
    region_names = tuple(REGION_FACTORS.keys())

    records: list[dict] = []
    borrower_mod = max(1, n_facilities // 2)
    for facility_number in range(1, n_facilities + 1):
        product_type = rng.choice(product_names, p=product_weights / product_weights.sum())
        product_settings = PRODUCT_SETTINGS[product_type]

        industry = rng.choice(industry_names)
        industry_settings = INDUSTRY_SETTINGS[industry]
        region = rng.choice(region_names)

        quality = rng.normal(loc=0.0, scale=1.0)
        industry_factor = float(industry_settings["risk_factor"])
        product_factor = float(product_settings["risk_factor"])
        region_factor = float(REGION_FACTORS[region])

        security_type = rng.choice(
            product_settings["security_types"],
            p=np.array(product_settings["security_weights"], dtype=float),
        )
        limit_amount = round(rng.uniform(*product_settings["limit_range"]), 2)
        drawn_pct = float(rng.uniform(*product_settings["drawn_range"]))
        drawn_balance = round(limit_amount * drawn_pct, 2)
        loan_term_months = int(rng.choice(product_settings["term_options"]))

        revenue_low, revenue_high = industry_settings["revenue_range"]
        annual_revenue = round(
            np.clip(
                rng.uniform(revenue_low, revenue_high) * (1.0 + quality * 0.12),
                revenue_low * 0.60,
                revenue_high * 1.20,
            ),
            2,
        )
        margin_low, margin_high = industry_settings["ebitda_margin_range"]
        ebitda_margin = float(np.clip(rng.uniform(margin_low, margin_high) + quality * 0.015, 0.04, 0.30))
        ebitda = round(annual_revenue * ebitda_margin, 2)

        dscr = float(
            np.clip(
                1.55 + quality * 0.22 - product_factor * 0.55 - industry_factor * 0.35 + rng.normal(0, 0.08),
                0.75,
                2.50,
            )
        )
        arrears_days = int(
            np.clip(
                round(rng.normal(8 + product_factor * 55 + industry_factor * 30 + max(-quality, 0) * 20, 14)),
                0,
                120,
            )
        )

        property_value = np.nan
        current_lvr = np.nan
        if product_type == "Property Backed Loan":
            current_lvr = float(
                np.clip(
                    0.54 + product_factor * 0.20 + industry_factor * 0.08 + max(-quality, 0) * 0.06 + rng.normal(0, 0.05),
                    0.38,
                    0.92,
                )
            )
            property_value = round(drawn_balance / max(current_lvr, 0.25), 2)

        watchlist_flag = int(
            arrears_days >= 60
            or dscr < 1.00
            or (product_type == "Property Backed Loan" and current_lvr >= 0.82)
            or rng.random() < (0.03 + industry_factor * 0.03 + max(-quality, 0) * 0.06)
        )

        risk_score = float(
            np.clip(
                0.12
                + product_factor * 0.45
                + industry_factor * 0.35
                + max(1.25 - dscr, 0) * 0.28
                + (arrears_days / 120.0) * 0.22
                + watchlist_flag * 0.12
                + (max((current_lvr if not np.isnan(current_lvr) else 0.62) - 0.65, 0) * 0.20)
                + max(region_factor, 0) * 0.20
                + rng.normal(0, 0.025),
                0.05,
                0.95,
            )
        )
        internal_risk_grade = _assign_risk_grade(risk_score)
        borrower_strength = _borrower_strength(internal_risk_grade, watchlist_flag, arrears_days)
        risk_addon = {"RG1": 0.000, "RG2": 0.005, "RG3": 0.011, "RG4": 0.020, "RG5": 0.035}[internal_risk_grade]
        interest_rate = round(product_settings["interest_base"] + risk_addon + rng.normal(0, 0.004), 4)

        borrower_number = ((facility_number - 1) % borrower_mod) + 1
        records.append(
            {
                "facility_id": f"FAC-{facility_number:05d}",
                "borrower_id": f"BOR-{borrower_number:04d}",
                "borrower_name": f"Borrower {borrower_number:04d}",
                "product_type": product_type,
                "industry": industry,
                "region": region,
                "limit_amount": limit_amount,
                "drawn_balance": drawn_balance,
                "interest_rate": interest_rate,
                "loan_type": product_settings["loan_type"],
                "security_type": security_type,
                "loan_term_months": loan_term_months,
                "property_value": property_value,
                "current_lvr": round(current_lvr, 4) if not np.isnan(current_lvr) else np.nan,
                "annual_revenue": annual_revenue,
                "ebitda": ebitda,
                "dscr": round(dscr, 3),
                "arrears_days": arrears_days,
                "internal_risk_grade": internal_risk_grade,
                "watchlist_flag": watchlist_flag,
                "borrower_strength": borrower_strength,
            }
        )

    return pd.DataFrame.from_records(records)


def _build_pd_final_dataset(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    out = portfolio_df[
        [
            "facility_id",
            "borrower_id",
            "borrower_name",
            "product_type",
            "industry",
            "security_type",
            "internal_risk_grade",
            "watchlist_flag",
            "arrears_days",
            "current_lvr",
        ]
    ].copy()

    out["pd_model_stream"] = np.where(out["product_type"] == "Property Backed Loan", "property", "cashflow")
    out["property_segment"] = np.where(out["product_type"] == "Property Backed Loan", out["security_type"], pd.NA)
    out["risk_grade"] = out["internal_risk_grade"]
    out["score_band"] = out["risk_grade"].map(RISK_GRADE_TO_SCORE_BAND)
    score_base = out["risk_grade"].map({"RG1": 780, "RG2": 730, "RG3": 675, "RG4": 610, "RG5": 545})
    score_adjustment = (out["watchlist_flag"] * -25) + np.clip(out["arrears_days"] - 15, 0, 90) * -0.55
    out["score"] = (score_base + score_adjustment).clip(420, 820).round(0).astype(int)

    pd_multiplier = (
        1.0
        + out["watchlist_flag"] * 0.18
        + (out["arrears_days"] >= 30).astype(float) * 0.10
        + (out["product_type"] == "Overdraft / Revolving Working Capital").astype(float) * 0.12
        - (out["product_type"] == "Property Backed Loan").astype(float) * 0.08
        + out["industry"].map(lambda value: INDUSTRY_SETTINGS[value]["risk_factor"]) * 0.35
        + np.where(out["current_lvr"].fillna(0) >= 0.80, 0.08, 0.00)
    )
    out["pd_final"] = (out["risk_grade"].map(RISK_GRADE_PD_LOOKUP) * pd_multiplier).clip(0.005, 0.35).round(4)
    out["default_horizon_months"] = 12
    out["pd_model_name"] = np.where(out["pd_model_stream"] == "property", "property_logistic_scorecard", "cashflow_logistic_scorecard")
    out["pd_model_version"] = "v1.0"
    out["as_of_date"] = AS_OF_DATE

    return out[
        [
            "facility_id",
            "borrower_id",
            "borrower_name",
            "product_type",
            "pd_model_stream",
            "industry",
            "property_segment",
            "score",
            "score_band",
            "risk_grade",
            "pd_final",
            "default_horizon_months",
            "pd_model_name",
            "pd_model_version",
            "as_of_date",
        ]
    ]


def _build_lgd_final_dataset(portfolio_df: pd.DataFrame, pd_df: pd.DataFrame) -> pd.DataFrame:
    merged = portfolio_df.merge(pd_df[["facility_id", "score_band"]], on="facility_id", how="left")
    conduct_classification = np.select(
        [
            (merged["watchlist_flag"] == 1) | (merged["arrears_days"] >= 60),
            merged["arrears_days"] >= 15,
        ],
        ["Red", "Amber"],
        default="Green",
    )

    security_bucket = merged.apply(lambda row: _security_bucket(row["product_type"], row["security_type"]), axis=1)
    lgd_base = [_base_lgd(product_type, bucket) for product_type, bucket in zip(merged["product_type"], security_bucket, strict=False)]
    lgd_adj_lvr = np.where(merged["current_lvr"].fillna(0) >= 0.80, 0.06, np.where(merged["current_lvr"].fillna(0) >= 0.65, 0.03, 0.00))
    industry_factor = merged["industry"].map(lambda value: INDUSTRY_SETTINGS[value]["risk_factor"])
    lgd_adj_industry = np.where(industry_factor >= 0.20, 0.02, np.where(industry_factor >= 0.16, 0.01, 0.00))
    lgd_adj_pd_band = merged["score_band"].map({"A": -0.03, "B": -0.01, "C": 0.00, "D": 0.02, "E": 0.05}).fillna(0.00)
    lgd_adj_pd_band = np.where(merged["product_type"] == "Property Backed Loan", 0.00, lgd_adj_pd_band)
    lgd_adj_dscr = np.where(merged["dscr"] < 1.10, 0.03, np.where(merged["dscr"] < 1.25, 0.01, 0.00))
    lgd_adj_conduct = pd.Series(conduct_classification).map({"Green": 0.00, "Amber": 0.01, "Red": 0.03}).to_numpy()
    downturn_scalar = np.where(merged["product_type"] == "Property Backed Loan", 1.08, 1.10)

    lgd_adjusted = np.array(lgd_base) + lgd_adj_lvr + lgd_adj_industry + lgd_adj_pd_band + lgd_adj_dscr + lgd_adj_conduct
    lgd_downturn = lgd_adjusted * downturn_scalar
    lgd_final = np.clip(lgd_downturn, 0.08, 0.95)
    property_type = np.where(
        merged["product_type"] == "Property Backed Loan",
        np.where(merged["security_type"] == "Residential Investment Property", "Residential", "Commercial"),
        pd.NA,
    )

    return pd.DataFrame(
        {
            "loan_id": merged["facility_id"],
            "source_product": merged["product_type"],
            "source_loan_id": merged["facility_id"],
            "product_type": merged["product_type"],
            "security_type": security_bucket,
            "property_type": property_type,
            "property_value": merged["property_value"],
            "current_lvr": merged["current_lvr"],
            "loan_stage": pd.NA,
            "industry": merged["industry"],
            "ead": merged["drawn_balance"],
            "pd_score_band": merged["score_band"],
            "dscr": merged["dscr"],
            "conduct_classification": conduct_classification,
            "lgd_base": np.round(lgd_base, 4),
            "lgd_adj_lvr": np.round(lgd_adj_lvr, 4),
            "lgd_adj_stage": 0.0,
            "lgd_adj_industry": np.round(lgd_adj_industry, 4),
            "lgd_adj_pd_band": np.round(lgd_adj_pd_band, 4),
            "lgd_adj_dscr": np.round(lgd_adj_dscr, 4),
            "lgd_adj_conduct": np.round(lgd_adj_conduct, 4),
            "lgd_adjusted": np.round(lgd_adjusted, 4),
            "downturn_scalar": np.round(downturn_scalar, 4),
            "lgd_downturn": np.round(lgd_downturn, 4),
            "lgd_final": np.round(lgd_final, 4),
        }
    )


def _build_downturn_overlay_table() -> pd.DataFrame:
    return pd.DataFrame(STRESS_SCENARIOS)


def build_demo_input_tables(n_facilities: int = N_FACILITIES, seed: int = RANDOM_SEED) -> dict[str, pd.DataFrame]:
    portfolio_df = _build_portfolio_dataset(n_facilities=n_facilities, seed=seed)
    pd_df = _build_pd_final_dataset(portfolio_df)
    lgd_df = _build_lgd_final_dataset(portfolio_df, pd_df)
    overlays_df = _build_downturn_overlay_table()
    return {
        "portfolio": portfolio_df,
        "pd_final": pd_df,
        "lgd_final": lgd_df,
        "downturn_overlays": overlays_df,
    }


def stage_demo_inputs(
    input_dir: str | Path | None = None,
    overwrite: bool = False,
    n_facilities: int = N_FACILITIES,
    seed: int = RANDOM_SEED,
) -> dict[str, Path]:
    target_dir = _resolve_input_dir(input_dir)
    ensure_directories(target_dir)
    file_map = {
        "portfolio": target_dir / DEFAULT_INPUT_FILES["portfolio"].name,
        "pd_final": target_dir / DEFAULT_INPUT_FILES["pd_final"].name,
        "lgd_final": target_dir / DEFAULT_INPUT_FILES["lgd_final"].name,
        "downturn_overlays": target_dir / DEFAULT_INPUT_FILES["downturn_overlays"].name,
    }
    if overwrite or any(not path.exists() for path in file_map.values()):
        tables = build_demo_input_tables(n_facilities=n_facilities, seed=seed)
        save_dataframe(tables["portfolio"], file_map["portfolio"])
        save_dataframe(tables["pd_final"], file_map["pd_final"])
        save_dataframe(tables["lgd_final"], file_map["lgd_final"])
        save_dataframe(tables["downturn_overlays"], file_map["downturn_overlays"])
    return file_map


def load_input_tables(input_dir: str | Path | None = None, refresh_demo: bool = False) -> dict[str, pd.DataFrame]:
    file_map = stage_demo_inputs(input_dir=input_dir, overwrite=refresh_demo)
    return {
        "portfolio": pd.read_csv(file_map["portfolio"]),
        "pd_final": pd.read_csv(file_map["pd_final"]),
        "lgd_final": pd.read_csv(file_map["lgd_final"]),
        "downturn_overlays": pd.read_csv(file_map["downturn_overlays"]),
    }

