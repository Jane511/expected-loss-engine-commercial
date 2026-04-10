from __future__ import annotations

import pandas as pd

from .ead_engine import add_ead_columns
from .utils import weighted_average


def run_stress_tests(df: pd.DataFrame, scenario_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    base_total_el: float | None = None

    for scenario in scenario_df.itertuples(index=False):
        stressed = add_ead_columns(df, ccf_multiplier=float(scenario.ccf_multiplier))
        stressed["pd_stress"] = (stressed["pd_final"] * float(scenario.pd_multiplier)).clip(0, 1)
        stressed["lgd_stress"] = (stressed["lgd_final"] * float(scenario.lgd_multiplier)).clip(0, 1)
        stressed["ead_stress"] = stressed["ead"]
        stressed["el_stress"] = (stressed["pd_stress"] * stressed["lgd_stress"] * stressed["ead_stress"]).round(2)

        total_el = float(stressed["el_stress"].sum())
        if scenario.scenario == "base":
            base_total_el = total_el

        records.append(
            {
                "scenario": scenario.scenario,
                "pd_multiplier": float(scenario.pd_multiplier),
                "lgd_multiplier": float(scenario.lgd_multiplier),
                "ccf_multiplier": float(scenario.ccf_multiplier),
                "total_ead": round(float(stressed["ead_stress"].sum()), 2),
                "total_el": round(total_el, 2),
                "average_pd": round(weighted_average(stressed["pd_stress"], stressed["ead_stress"]), 6),
                "average_lgd": round(weighted_average(stressed["lgd_stress"], stressed["ead_stress"]), 6),
                "el_rate": round(total_el / float(stressed["ead_stress"].sum()), 6),
                "scenario_description": getattr(scenario, "scenario_description", ""),
            }
        )

    result = pd.DataFrame.from_records(records)
    if base_total_el is None and not result.empty:
        base_total_el = float(result.loc[0, "total_el"])
    result["change_vs_base"] = (result["total_el"] - float(base_total_el)).round(2)
    result["pct_change_vs_base"] = (
        (result["total_el"] - float(base_total_el)) / float(base_total_el) if base_total_el else 0.0
    ).round(6)
    return result

