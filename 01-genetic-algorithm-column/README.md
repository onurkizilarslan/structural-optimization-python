# Genetic algorithm · RC column

[Collection](../README.md) · [Türkçe](README.tr.md) · [Detailed Turkish model notes](OKU.md)

## Design problem

A 3 m column with a prescribed 2,000 kN axial demand. Width/depth: 300–600 mm; 588 combinations. Capacity, reinforcement ratio and simplified spacing constraints.

**Variables and objective:** Discrete width, depth, reinforcement count and diameter. Minimize concrete and longitudinal-steel material cost.

```text
C = 3000 V_c + 35 m_s
```

Concrete/steel examples use hypothetical currency units (PB), not current prices. Internal structural units are documented in [OKU.md](OKU.md). The algorithm implementations are educational variants; read the model notes for operators, constraint handling, random seeds and evaluation budgets.

## Run

From the repository root, with Python 3.11 or later:

```bash
cd 01-genetic-algorithm-column
python -m pip install -r requirements.txt
python kolon_optimizasyonu.py
```

Run within this lesson folder. Python identifiers and detailed teaching notes retain their original Turkish names. Outputs overwrite existing result files. After changing inputs, regenerate plots; explanatory Markdown numbers do not update automatically.

## Verification

```bash
python kolon_optimizasyonu.py
```

This lesson has no separate unit-test suite. Its executable compares ten seeded GA runs against all 588 combinations. The collection validation runner additionally checks the generated CSV files.

## Scope and references

Axial capacity only; no moment interaction, slenderness, seismic detailing or second-order analysis. These are educational models, not construction-ready or code-compliant structural designs.

Detailed equations, assumptions, source references, results and exercises are in [OKU.md](OKU.md). Read [provenance](../PROVENANCE.md) and [license status](../LICENSE_STATUS.md).
