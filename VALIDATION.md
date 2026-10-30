# Validation record

Packaging validation: 30 October 2026.

Environment: Python 3.12.14, NumPy 2.3.5, Matplotlib 3.10.8.

Command: `python validate.py` from the repository root.

| Lesson | Checks run | Outcome |
|---|---|---|
| GA column | Full default execution in a temporary folder; CSV row counts | Passed; 588 candidates, 10 seeded runs |
| ACO beam | 6 existing unit tests | Passed |
| PSO truss | 7 existing unit tests | Passed |
| DE beam | 7 existing unit tests | Passed |
| SA frame | 8 existing unit tests | Passed |
| NSGA-II truss | 8 existing unit tests | Passed |

Total: 36 existing unit tests plus a GA execution/output check. The GA run reported 328 feasible candidates and all ten seeds matched its enumeration minimum. No new assertion was added for the optimizer's success rate; the runner checks successful execution and output row counts.

All original Python source files and stored CSV/JSON/PNG results are retained byte-for-byte from the six lesson ZIP packages. Only lesson folder references in OKU.md were updated, and collection entry pages were added. README relative links were checked locally.

The original stored numerical results and figures were not all regenerated during this packaging pass. Existing tests include analytical checks, finite searches and reduced seeded algorithm runs; inspect each test file for exact coverage. This is model verification, not independent engineering certification or a claim of standards compliance. No GitHub Actions run is claimed.

To repeat: install dependencies in a clean environment and run `python validate.py`. Full experiments and figures are reproduced using each lesson's README commands. Minimum dependency versions are broad compatibility requirements; only the environment above was exercised in this packaging pass.
