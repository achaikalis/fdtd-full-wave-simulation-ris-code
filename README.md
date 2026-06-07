# Implementation of the paper "FDTD Full Wave Simulations of Reconfigurable  Intelligent Surfaces"

An independent Python code implementation of the RIS simulation setup described by Colella et al. using Tidy3D. The code builds the RIS geometry, material stack, lumped varactor states, monitors, cost estimates, plots, and TikZ design diagrams.

## Setup

```bash
uv sync
```

## Validate

```bash
uv run ruff check .
uv run python main.py --mode validate
```

## Running main.py

Run the workflow through `uv` so the project dependencies from `pyproject.toml`
are available:

```bash
uv run python main.py [--mode MODE] [--case CASE] [--output-dir DIR]
```

Arguments:

- `--mode`: workflow step to execute. Defaults to `validate`.
- `--case`: case label used when building the baseline simulation. Defaults to
  `low_capacitance`. The configured capacitance cases are `low_capacitance` and
  `high_capacitance`; unrecognized labels use the low-capacitance simulation
  settings while preserving the label in generated output names.
- `--output-dir`: directory for exported plots and reports. Defaults to
  `reports`.

Available modes:

- `validate`: validate the default configuration, estimate cost, and export
  overview plots without submitting a simulation.
- `estimate`: validate the configuration, estimate cost, and export overview
  plots. This currently follows the same local-only path as `validate`.
- `inspect`: build and inspect/export overview plots even if validation reports
  issues.
- `run`: validate, estimate cost, submit the selected simulation to Tidy3D, and
  save run outputs.
- `analyze`: analyze simulation data already loaded in the current process. When
  run directly from the command line, no previous simulation data is loaded, so
  run `--mode run` first from an integrated workflow before using this path.

Examples:

```bash
# Validate the default low-capacitance case and write plots to reports/.
uv run python main.py

# Estimate and export overview plots for the high-capacitance case.
uv run python main.py --mode estimate --case high_capacitance

# Write validation/overview outputs to a custom directory.
uv run python main.py --mode validate --output-dir reports/local_check

# Submit the high-capacitance simulation to Tidy3D.
uv run python main.py --mode run --case high_capacitance --output-dir reports/high_capacitance
```

## Main Outputs

- `ris_system/`: simulation configuration, geometry, materials, sources, monitors, post-processing, and visualization helpers.
- `tikz/`: source TikZ diagrams plus generated PDF/SVG/PNG previews.
- `reports/`: local generated plots.
- `results/`: local Tidy3D HDF5 outputs.

## Diagrams

Regenerate a TikZ PDF from the `tikz/` directory:

```bash
xelatex -interaction=nonstopmode -halt-on-error ris_layout_tikz.tex
xelatex -interaction=nonstopmode -halt-on-error ris_simulation_setup_tikz.tex
```
## References

```bibtex
@misc{colella_fdtd_2023,
	title = {{FDTD} {Full} {Wave} {Simulations} of {Reconfigurable} {Intelligent} {Surfaces}},
	url = {http://arxiv.org/abs/2309.12414},
	doi = {10.48550/arXiv.2309.12414},
	abstract = {This paper presents the analysis of metasurfaces, here called reconfigurable intelligent surface. The analysis is performed by numerical simulations that implement the finitedifference time-domain method. The metasurface has been modeled by metallic patches interconnected by varactor diodes. The electromagnetic source consists of randomly generated plane wave. This kind of analysis allows us to investigate the response of the metasurface when it is hit by a random source.},
	language = {en},
	urldate = {2026-05-27},
	publisher = {arXiv},
	author = {Colella, Emanuel and Bastianelli, Luca and Primiani, Valter Mariani and Moglie, Franco},
	month = sep,
	year = {2023},
	note = {arXiv:2309.12414 [physics.app-ph]},
	keywords = {Physics - Applied Physics, Unread},
	annote = {Comment: Accepted in EMC Europe 2023},
	annote = {Comment: Accepted in EMC Europe 2023},
	annote = {Comment: Accepted in EMC Europe 2023},
}
```

## Licenses

This is not the original code from the authors.

The implementation is released under the MIT License.
