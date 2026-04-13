from pathlib import Path

from src.pipeline import run_pipeline


def test_demo_pipeline_outputs():
    root = Path("tests") / "_artifacts_demo"
    result = run_pipeline(
        input_dir=root / "data" / "input",
        processed_dir=root / "data" / "processed",
        output_dir=root / "outputs" / "tables",
        refresh_demo_inputs=True,
        persist=True,
    )

    assert not result["loan_level_el"].empty
    assert not result["ifrs9_el"].empty
    assert not result["concentration_summary"].empty
    assert result["validation_report"]["status"].all()
    assert (root / "outputs" / "tables" / "loan_level_el.csv").exists()
    assert (root / "outputs" / "tables" / "ifrs9_stage_summary.csv").exists()
    assert (root / "outputs" / "tables" / "pipeline_validation_report.csv").exists()
