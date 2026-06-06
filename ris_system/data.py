"""Result loading helpers for RIS workflow data."""

from __future__ import annotations

from pathlib import Path

import tidy3d as td


def resolve_sim_data(
    active_label: str,
    active_data_by_case: dict[str, td.SimulationData] | None,
    results_dir: str | Path = Path("results"),
) -> td.SimulationData | None:
    """Resolve simulation data from memory first, then from an HDF5 file."""
    if active_data_by_case is not None and active_label in active_data_by_case:
        return active_data_by_case[active_label]

    data_path = Path(results_dir) / f"{active_label}.hdf5"
    if data_path.exists():
        return td.SimulationData.from_file(fname=str(data_path))

    return None


def load_case_data(
    case_label: str,
    sim_data_cases: dict[str, td.SimulationData] | None = None,
    no_ris_data: td.SimulationData | None = None,
    results_dir: str | Path = Path("results"),
    verbose: bool = True,
) -> td.SimulationData | None:
    """Load a case result, matching the notebook's in-memory/HDF5 fallback order."""
    if isinstance(sim_data_cases, dict) and case_label in sim_data_cases:
        return sim_data_cases[case_label]

    if case_label in {"pec_reference", "no_ris"} and no_ris_data is not None:
        return no_ris_data

    data_path = Path(results_dir) / f"{case_label}.hdf5"
    if not data_path.exists() and case_label == "pec_reference":
        data_path = Path(results_dir) / "no_ris.hdf5"
    if not data_path.exists():
        if verbose:
            print(f"Missing data file: {data_path}")
        return None
    return td.SimulationData.from_file(fname=str(data_path))
