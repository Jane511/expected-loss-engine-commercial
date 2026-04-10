# Methodology - Expected-Loss-Engine-Australia

1. Load or generate synthetic demo data.
2. Standardise borrower, facility, exposure, collateral, and financial fields.
3. Build utilisation, margin, DSCR, leverage, liquidity, working-capital, and collateral coverage features.
4. Run the `el` engine.
5. Validate and export CSV outputs.

## Output contract

- `outputs/tables/expected_loss_by_facility.csv`
- `outputs/tables/expected_loss_by_borrower.csv`
- `outputs/tables/expected_loss_by_segment.csv`
- `outputs/tables/portfolio_expected_loss.csv`
- `outputs/tables/scenario_weighted_ecl.csv`
