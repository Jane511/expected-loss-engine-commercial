# Expected Loss Engine for SME and Property Lending

This project builds an end-to-end Expected Loss Engine that combines Probability of Default (PD), Loss Given Default (LGD), and Exposure at Default (EAD) to calculate facility-level and portfolio-level credit losses. It extends the core loss calculation into pricing support and stress testing so the repo reads like a compact bank-style risk engine rather than a disconnected collection of notebooks.

The repo is self-contained and runnable with synthetic demo inputs. It is also structured so the local demo files can be replaced with final-layer outputs from the sibling PD, LGD, and industry-risk projects in the broader `credit-risk-portfolio_bank` workspace.

## Project Objective

The engine demonstrates how a lender can:

- calculate expected loss at individual facility level
- aggregate risk by product, industry, region, and grade
- translate expected loss into pricing hurdle support
- test how expected loss changes under mild and severe stress scenarios

Core formula:

```text
Expected Loss = PD x LGD x EAD
```

## Repo Structure

```text
4. Expected Loss Engine/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── input/
│   ├── processed/
│   └── output/
├── docs/
│   ├── project_overview.md
│   ├── methodology.md
│   ├── pricing_logic.md
│   ├── stress_testing.md
│   └── limitations.md
├── notebooks/
│   ├── 01_portfolio_setup.ipynb
│   ├── 02_ead_calculation.ipynb
│   ├── 03_expected_loss_calculation.ipynb
│   ├── 04_portfolio_aggregation.ipynb
│   ├── 05_pricing_analysis.ipynb
│   └── 06_stress_testing.ipynb
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   ├── ead_engine.py
│   ├── expected_loss.py
│   ├── aggregation.py
│   ├── pricing.py
│   ├── stress_testing.py
│   ├── pipeline.py
│   └── utils.py
└── tests/
    ├── test_ead_engine.py
    └── test_pipeline.py
```

## Inputs

The pipeline expects four input files under `data/input/`:

- `portfolio_input.csv`
- `facility_pd_final_combined.csv`
- `lgd_final.csv`
- `downturn_overlays.csv`

If any of these files are missing, the repo generates deterministic demo inputs automatically. That makes the project runnable from a clean checkout while keeping file names aligned to the final-layer handoff expected from the sibling repos.

## Outputs

Running the pipeline produces:

- `data/output/loan_level_el.csv`
- `data/output/segment_expected_loss_summary.csv`
- `data/output/portfolio_summary.csv`
- `data/output/pricing_table.csv`
- `data/output/stress_test_results.csv`

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the full pipeline:

```bash
python -m src.pipeline
```

Regenerate the demo inputs first:

```bash
python -m src.pipeline --refresh-demo-inputs
```

Run tests:

```bash
pytest
```

## Methodology Summary

- `PD`: loaded from `facility_pd_final_combined.csv`
- `LGD`: loaded from `lgd_final.csv`
- `EAD`: recalculated inside this repo using funded and revolving-facility logic
- `EL`: calculated at facility level, then rolled up into segment and portfolio summaries
- `Pricing`: required margin = EL rate + funding cost + operating cost + target return
- `Stress testing`: scenario multipliers are applied to PD, LGD, and revolving-facility CCFs

## Integration With Sibling Repos

The broader workspace already includes:

- `1.2 PD and Score Card_Cashflow & Property backed Lending`
- `2. APRA LGD Model`
- `9.Industry Risk Analysis_Australia`

To switch from demo mode to cross-repo integration, replace the four local input files in `data/input/` with:

- the PD repo's `facility_pd_final_combined.csv`
- the LGD repo's `lgd_final.csv`
- a portfolio dataset aligned to those facility identifiers
- a stress overlay table aligned to the desired scenario design

## Interview Framing

Use this line:

```text
I built an Expected Loss Engine that integrates PD, LGD, and EAD at facility level, aggregates the results to portfolio level, and extends the loss framework into pricing and stress testing.
```

