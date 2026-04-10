# Project Overview

This repo is the portfolio-wide layer that sits after PD and LGD model development. It takes facility-level risk inputs, recalculates EAD using product logic, computes expected loss at facility level, then rolls the results into portfolio reporting, pricing support, and scenario stress testing.

The design goal is practical credit-risk workflow coverage rather than model-theory depth in isolation. A credit officer, portfolio manager, or private credit underwriter should be able to see how the same facility-level loss engine can support both day-to-day underwriting and book-level oversight.

## Products Covered

- SME Cash Flow Term Loan
- Property Backed Loan
- Overdraft / Revolving Working Capital

## Why This Repo Matters

- It translates model outputs into decision-ready loss metrics.
- It shows product-specific EAD logic rather than assuming funded balance equals exposure for every facility.
- It links loss estimation to pricing and stress testing, which is how the metric is actually used in lending institutions.

