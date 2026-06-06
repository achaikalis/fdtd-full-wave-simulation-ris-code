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
## References

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

## Licenses

This is not the original code from the authors.

The implementation is released under the MIT License.