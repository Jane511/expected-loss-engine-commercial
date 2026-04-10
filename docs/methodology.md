# Methodology

## Core Formula

```text
Expected Loss = PD x LGD x EAD
```

## Portfolio Input Layer

The portfolio file represents one row per facility and includes:

- facility and borrower identifiers
- product type and loan type
- industry and region
- facility limit and drawn balance
- security type and property metrics where relevant
- borrower financial metrics such as revenue, EBITDA, and DSCR
- monitoring indicators such as arrears and watchlist status

## PD

The engine expects a final-layer PD file named `facility_pd_final_combined.csv`. In demo mode, the file is generated from the synthetic portfolio and includes:

- score and score band
- risk grade
- final 12-month PD
- model stream and metadata

## LGD

The engine expects a final-layer LGD file named `lgd_final.csv`. In demo mode, the file is generated using product and collateral logic with additive overlays for:

- leverage
- industry risk
- score-band alignment
- DSCR weakness
- conduct quality

## EAD

EAD is recalculated inside this repo:

- term loans use current drawn balance as exposure
- revolving facilities use drawn balance plus a credit conversion factor on undrawn availability
- CCF buckets are mapped as strong 30%, average 50%, weak 75%

## Aggregation

Expected loss is first created at facility level, then aggregated by:

- product type
- industry
- region
- risk grade

The portfolio summary rolls this further into a product-level view with a total-portfolio row.

