from __future__ import annotations

from pathlib import Path

from src.pipeline import run_pipeline


def test_pipeline_generates_required_outputs() -> None:
    artifacts_root = Path("tests") / "_artifacts"
    result = run_pipeline(
        input_dir=artifacts_root / "input",
        processed_dir=artifacts_root / "processed",
        output_dir=artifacts_root / "output",
        refresh_demo_inputs=True,
        persist=True,
    )

    assert not result["loan_level_el"].empty
    assert not result["segment_summary"].empty
    assert not result["portfolio_summary"].empty
    assert not result["pricing_table"].empty
    assert not result["stress_results"].empty
    assert (artifacts_root / "output" / "loan_level_el.csv").exists()
    assert (artifacts_root / "output" / "portfolio_summary.csv").exists()
    assert set(result["stress_results"]["scenario"]) == {"base", "mild", "severe"}
    assert (result["loan_level_el"]["expected_loss"] >= 0).all()
