from __future__ import annotations

import argparse
from pathlib import Path

from .aggregation import summarise_portfolio, summarise_segment_expected_loss
from .config import DEFAULT_OUTPUT_FILES, INPUT_DIR, OUTPUT_DIR, PROCESSED_DIR
from .data_loader import load_input_tables
from .expected_loss import build_expected_loss_dataset
from .pricing import apply_pricing, summarise_pricing
from .stress_testing import run_stress_tests
from .utils import ensure_directories, save_dataframe


def run_pipeline(
    input_dir: str | Path | None = None,
    processed_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    refresh_demo_inputs: bool = False,
    persist: bool = True,
) -> dict:
    input_path = Path(input_dir) if input_dir is not None else INPUT_DIR
    processed_path = Path(processed_dir) if processed_dir is not None else PROCESSED_DIR
    output_path = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    ensure_directories(input_path, processed_path, output_path)

    inputs = load_input_tables(input_dir=input_path, refresh_demo=refresh_demo_inputs)
    expected_loss_df = build_expected_loss_dataset(inputs["portfolio"], inputs["pd_final"], inputs["lgd_final"])
    segment_summary = summarise_segment_expected_loss(expected_loss_df)
    portfolio_summary = summarise_portfolio(expected_loss_df)
    pricing_df = apply_pricing(expected_loss_df)
    pricing_summary = summarise_pricing(pricing_df)
    stress_summary = run_stress_tests(expected_loss_df, inputs["downturn_overlays"])

    if persist:
        save_dataframe(expected_loss_df, output_path / DEFAULT_OUTPUT_FILES["loan_level_el"].name)
        save_dataframe(segment_summary, output_path / DEFAULT_OUTPUT_FILES["segment_summary"].name)
        save_dataframe(portfolio_summary, output_path / DEFAULT_OUTPUT_FILES["portfolio_summary"].name)
        save_dataframe(pricing_summary, output_path / DEFAULT_OUTPUT_FILES["pricing_table"].name)
        save_dataframe(stress_summary, output_path / DEFAULT_OUTPUT_FILES["stress_results"].name)
        save_dataframe(expected_loss_df, processed_path / "expected_loss_dataset.csv")
        save_dataframe(pricing_df, processed_path / "pricing_dataset.csv")

    return {
        "inputs": inputs,
        "loan_level_el": expected_loss_df,
        "segment_summary": segment_summary,
        "portfolio_summary": portfolio_summary,
        "pricing_table": pricing_summary,
        "stress_results": stress_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Expected Loss Engine pipeline.")
    parser.add_argument(
        "--refresh-demo-inputs",
        action="store_true",
        help="Regenerate the synthetic input files before running the pipeline.",
    )
    args = parser.parse_args()

    result = run_pipeline(refresh_demo_inputs=args.refresh_demo_inputs, persist=True)
    total_ead = float(result["loan_level_el"]["ead"].sum())
    total_el = float(result["loan_level_el"]["expected_loss"].sum())
    print(f"Facilities processed: {len(result['loan_level_el'])}")
    print(f"Portfolio EAD: {total_ead:,.2f}")
    print(f"Portfolio expected loss: {total_el:,.2f}")
    print(f"Output files written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

