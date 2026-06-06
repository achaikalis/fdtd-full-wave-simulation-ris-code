"""Notebook-level orchestration helpers for the RIS reproduction workflow."""

from __future__ import annotations

from pathlib import Path

import tidy3d as td
from tidy3d import web

from .config import SimulationConfig
from .monitors import MonitorFactory
from .simulation import SimulationBuilder
from .sources import SourceFactory


def build_case_simulations(
    builder: SimulationBuilder,
    case_labels: tuple[str, ...] = ("low_capacitance", "high_capacitance"),
) -> dict[str, td.Simulation]:
    """Build all requested capacitance-state simulations."""
    return {
        case_label: builder.build_simulation(case_label=case_label)
        for case_label in case_labels
    }


def run_case_simulations(
    builder: SimulationBuilder,
    case_labels: tuple[str, ...] = ("low_capacitance", "high_capacitance"),
    results_dir: str | Path = Path("results"),
    run_job: bool = True,
) -> tuple[dict[str, td.SimulationData], dict[str, float]]:
    """Estimate and optionally run the requested RIS simulations."""
    run_case_data: dict[str, td.SimulationData] = {}
    run_estimated_costs: dict[str, float] = {}
    results_dir = Path(results_dir)

    for run_case_label in case_labels:
        run_simulation = builder.build_simulation(case_label=run_case_label)
        run_task_name = run_case_label
        result_path = results_dir / f"{run_task_name}.hdf5"

        job = web.Job(
            simulation=run_simulation,
            task_name=run_task_name,
            verbose=False,
        )
        estimated_run_cost = web.estimate_cost(job.task_id)
        run_estimated_costs[run_case_label] = estimated_run_cost

        print(f"Case: {run_case_label}")
        print(f"Job task id: {job.task_id}")
        print(f"Estimated run cost: {estimated_run_cost:.3f} FlexCredits")

        if run_job:
            run_case_data[run_case_label] = web.run(
                run_simulation,
                task_name=run_task_name,
                path=str(result_path),
                verbose=True,
            )
            print(f"Saved simulation data to {result_path}")
        else:
            print("Set run_job = True to launch the simulation and save the HDF5 result.")

    return run_case_data, run_estimated_costs


def build_no_ris_simulation(config: SimulationConfig) -> td.Simulation:
    """Build a reference simulation without the RIS structures."""
    source_factory = SourceFactory(config)
    monitor_factory = MonitorFactory(config)
    reference_monitor = td.FieldMonitor(
        center=(0.0, -5_000.0, 0.0),
        size=(50_000.0, 0.0, 50_000.0),
        fields=list(config.monitors.fields),
        freqs=[config.frequency.center_hz],
        colocate=True,
        name="reference_plane",
    )
    source = source_factory.build_source()
    boundary_spec = td.BoundarySpec(
        x=td.Boundary.bloch_from_source(
            source=source,
            domain_size=config.domain.size_um[0],
            axis=0,
            medium=td.Medium(permittivity=1.0),
        ),
        y=td.Boundary.pml(num_layers=config.domain.pml_layers),
        z=td.Boundary.bloch_from_source(
            source=source,
            domain_size=config.domain.size_um[2],
            axis=2,
            medium=td.Medium(permittivity=1.0),
        ),
    )
    return td.Simulation(
        center=(0.0, 0.0, 0.0),
        size=config.domain.size_um,
        grid_spec=td.GridSpec.auto(
            min_steps_per_wvl=config.domain.grid_min_steps_per_wvl,
            wavelength=config.frequency.wavelength_um,
        ),
        run_time=config.domain.run_time_s,
        structures=(),
        sources=(source,),
        monitors=(*monitor_factory.build_point_monitors(), reference_monitor),
        lumped_elements=(),
        boundary_spec=boundary_spec,
        symmetry=config.domain.symmetry,
        shutoff=config.domain.shutoff,
        courant=config.domain.courant,
        subpixel=True,
        medium=td.Medium(permittivity=1.0),
        plot_length_units=config.domain.plot_length_units,
        structure_priority_mode="conductor",
    )


def run_no_ris_reference(
    config: SimulationConfig,
    results_dir: str | Path = Path("results"),
    run_reference_job: bool = True,
    reference_task_name: str = "no_ris",
) -> tuple[td.Simulation, td.SimulationData | None]:
    """Build, estimate, and optionally run the no-RIS reference simulation."""
    results_dir = Path(results_dir)
    reference_result_path = results_dir / f"{reference_task_name}.hdf5"
    reference_simulation = build_no_ris_simulation(config)
    reference_job = web.Job(
        simulation=reference_simulation,
        task_name=reference_task_name,
        verbose=False,
    )
    print(f"Reference task id: {reference_job.task_id}")

    if run_reference_job:
        no_ris_data = web.run(
            reference_simulation,
            task_name=reference_task_name,
            path=str(reference_result_path),
            verbose=True,
        )
        print(f"Saved reference data to {reference_result_path}")
    else:
        no_ris_data = None
        print(
            "Set run_reference_job = True to launch the reference simulation "
            "and save the HDF5 result."
        )

    return reference_simulation, no_ris_data
