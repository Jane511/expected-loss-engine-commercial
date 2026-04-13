# Commercial Expected Loss & Decisioning Engine Project

This repository is the expected loss integration layer in the commercial credit-risk stack. It combines upstream PD, LGD, and EAD outputs, with optional industry reference data, to produce loan-level expected loss measures, portfolio summaries, IFRS 9 style tables, and downstream pricing or stress inputs. The project is positioned as the bridge between component risk models and downstream portfolio analytics for both bank-aligned frameworks and practical lending environments.

## What this repo is

This project demonstrates how separate commercial credit-risk components can be brought together into one practical expected loss workflow. It is built for portfolio review and recruiter inspection, so the data is synthetic, the logic is transparent, and the outputs are shaped for downstream reuse in both structured risk assessment and lending decision support.

## Where it sits in the stack

Upstream inputs:
- `PD-and-scorecard-commercial`
- `LGD-commercial`
- `EAD-CCF-commercial`
- optional reference context from `industry-analysis`

Downstream consumers:
- `stress-testing-commercial`
- `RAROC-pricing-and-return-hurdle`
- `portfolio-monitor-commercial`
- `RWA-capital-commercial`

## How this is used in practice

This project can be applied in:

### Bank / Institutional context

- Expected loss estimation for portfolio risk assessment, impairment-style views, and stress inputs
- Loan-level and segment-level loss measurement for structured risk review
- Reusable EL contract for monitoring, pricing, and capital workflows

### Non-bank / Fintech context

- Loss estimation to support origination strategy, pricing, and risk-adjusted decisioning
- Customer and facility segmentation using expected loss and concentration views
- Portfolio performance tracking with a consistent loss metric across products or cohorts

## Example input files (already in the repo)

- `data/input/portfolio_input.csv`: facility/borrower portfolio base used to join components
- `data/input/facility_pd_final_combined.csv`: facility PD final layer contract
- `data/input/lgd_final.csv`: LGD contract used to build expected loss
- `data/input/downturn_overlays.csv`: simple overlay table used for scenario-weighted ECL examples
- `data/raw/demo_portfolio.csv`: lightweight demo extract for quick reviewer context

## Example output files (already in the repo)

- `outputs/reports/pipeline_summary.md`: run summary and file index
- `outputs/tables/loan_level_el.csv`: facility-level expected loss output contract
- `outputs/tables/segment_expected_loss_summary.csv`: segment aggregation for portfolio packs
- `outputs/tables/ifrs9_ecl_by_facility.csv`: IFRS 9 style ECL view (simplified)
- `outputs/tables/input_source_report.csv`: traceability report for which inputs drove each output
- `outputs/tables/pipeline_validation_report.csv`: reviewer-friendly validation checks
- `outputs/charts/el_waterfall.png`: quick visual showing which components drive EL movement

## Example business use case

A portfolio team has borrower PD, LGD assumptions, and exposure measures but needs one consistent “loan-level expected loss” dataset to drive stress tests, pricing packs, monitoring, and capital discussion. This repo produces that EL contract and the portfolio summaries that downstream repos can reuse without re-implementing component logic.

## How these outputs feed downstream repos

- `stress-testing-commercial`: uses `outputs/tables/loan_level_el.csv` (and segment summaries) as the base expected loss view before applying scenario assumptions.
- `RAROC-pricing-and-return-hurdle`: uses `outputs/tables/pricing_table.csv` and `outputs/tables/loan_level_el.csv` to translate EL into cost-of-risk inputs for hurdle pricing.
- `portfolio-monitor-commercial`: uses `outputs/tables/ifrs9_ecl_by_facility.csv` and scenario-weighted tables as the impairment / staging foundation.
- `RWA-capital-commercial`: uses expected loss and stress outputs as context for capital overlays and reporting.

## Key outputs

- `outputs/tables/loan_level_el.csv`
- `outputs/tables/segment_expected_loss_summary.csv`
- `outputs/tables/portfolio_summary.csv`
- `outputs/tables/pricing_table.csv`
- `outputs/tables/stress_test_results.csv`
- `outputs/tables/ifrs9_ecl_by_facility.csv`
- `outputs/tables/concentration_summary.csv`
- `outputs/tables/input_source_report.csv`
- `outputs/tables/pipeline_validation_report.csv`

## Repo structure

- `data/`: staged input bundles, processed working tables, and external reference files
- `src/`: reusable expected loss, pricing, staging, and pipeline logic
- `scripts/`: wrapper scripts for pipeline execution
- `docs/`: methodology, assumptions, pricing logic, stress notes, and validation material
- `notebooks/`: reviewer-facing walkthrough notebooks
- `outputs/`: exported tables, charts, reports, and sample artifacts
- `tests/`: validation and regression checks

## How to run

Quick start:

```powershell
pip install -r requirements.txt
python -m src.pipeline
```

After the run, start with:

- `outputs/reports/pipeline_summary.md`
- `outputs/tables/portfolio_summary.csv`
- `outputs/tables/pipeline_validation_report.csv`

Run validation tests:

```powershell
python -m pytest
```

```powershell
python -m src.pipeline
```

Compatibility alias:

```powershell
python -m src.codex_run_pipeline
```

## Testing and validation

- `tests/test_pipeline.py` runs the pipeline end-to-end and checks that core output files are written.
- `outputs/tables/pipeline_validation_report.csv` captures reconciliations and sanity checks in a reviewer-friendly table.

## Limitations / Demo-Only Note

- All inputs are synthetic or public-style demo data.
- The integration logic is designed to be explainable and reusable rather than to mirror a production impairment engine exactly.
- Downstream tables are intentionally flat and portable so the repo can demonstrate stack integration without relying on workspace-specific conventions.
