# Tidy3D RIS Reproduction

Python workflow for reproducing the RIS simulation setup described by Colella et al. using Tidy3D. The code builds the RIS geometry, material stack, lumped varactor states, monitors, cost estimates, plots, and TikZ design diagrams.

## Setup

```bash
uv sync
```

## Validate

```bash
uv run ruff check .
uv run python main.py --mode validate
```

## Main Outputs

- `ris_system/`: simulation configuration, geometry, materials, sources, monitors, post-processing, and visualization helpers.
- `tikz/`: source TikZ diagrams plus generated PDF/SVG/PNG previews.
- `reports/`: local generated plots, ignored by Git.
- `results/`: local Tidy3D HDF5 outputs, ignored by Git.

## Diagrams

Regenerate a TikZ PDF from the `tikz/` directory:

```bash
xelatex -interaction=nonstopmode -halt-on-error ris_layout_tikz.tex
xelatex -interaction=nonstopmode -halt-on-error ris_simulation_setup_tikz.tex
```
