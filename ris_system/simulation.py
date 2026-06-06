"""Simulation assembly and cost estimation for the RIS reproduction workflow."""

from __future__ import annotations

from dataclasses import dataclass, replace

import tidy3d as td
from tidy3d import web

from .config import SimulationConfig
from .convergence import ConvergenceChecker
from .geometry import GeometryFactory
from .materials import MaterialFactory
from .monitors import MonitorFactory
from .sources import SourceFactory


@dataclass(frozen=True)
class SimulationCase:
    """Simulation case metadata."""

    label: str
    capacitance_pf: float
    simulation: td.Simulation


@dataclass(frozen=True)
class CostStrategy:
    """Cost-reduction variant for a simulation."""

    label: str
    grid_min_steps_per_wvl: int | None = None
    run_time_s: float | None = None
    symmetry: tuple[int, int, int] | None = None


@dataclass(frozen=True)
class CostEstimate:
    """Estimated cost for one simulation variant."""

    label: str
    task_name: str
    estimated_cost: float
    grid_min_steps_per_wvl: int
    run_time_s: float
    symmetry: tuple[int, int, int]


@dataclass(frozen=True)
class CostEstimationReport:
    """Baseline and candidate cost estimates."""

    baseline: CostEstimate
    candidates: tuple[CostEstimate, ...]

    @property
    def best(self) -> CostEstimate:
        return min(self.candidates, key=lambda candidate: candidate.estimated_cost)

    def summary(self) -> str:
        lines = ["Cost estimation summary:"]
        for candidate in self.candidates:
            lines.append(
                f"- {candidate.label}: {candidate.estimated_cost:.3f} FlexCredits "
                f"(min_steps={candidate.grid_min_steps_per_wvl}, "
                f"run_time={candidate.run_time_s:.3e} s, symmetry={candidate.symmetry})"
            )
        lines.append(
            f"Cheapest strategy: {self.best.label} at {self.best.estimated_cost:.3f} FlexCredits"
        )
        return "\n".join(lines)


class SimulationBuilder:
    """Build and run Tidy3D simulations for the configured RIS design."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.materials = MaterialFactory(config)
        self.geometry = GeometryFactory(config, self.materials)
        self.sources = SourceFactory(config)
        self.monitors = MonitorFactory(config)
        self.last_simulation_data = None

    def _boundary_spec(self, source: td.PlaneWave) -> td.BoundarySpec:
        """Create Bloch boundaries for x/z and PML along y for angled plane waves."""
        medium = td.Medium(permittivity=1.0)
        bloch_x = td.Boundary.bloch_from_source(
            source=source,
            domain_size=self.config.domain.size_um[0],
            axis=0,
            medium=medium,
        )
        bloch_z = td.Boundary.bloch_from_source(
            source=source,
            domain_size=self.config.domain.size_um[2],
            axis=2,
            medium=medium,
        )
        pml_y = td.Boundary.pml(num_layers=self.config.domain.pml_layers)
        return td.BoundarySpec(x=bloch_x, y=pml_y, z=bloch_z)

    def build_simulation(self, case_label: str = "low_capacitance") -> td.Simulation:
        capacitance_pf = self._case_to_capacitance(case_label)
        bundle = self.geometry.build_bundle(capacitance_pf)
        source = self.sources.build_source()
        sim = td.Simulation(
            center=(0.0, 0.0, 0.0),
            size=self.config.domain.size_um,
            grid_spec=td.GridSpec.auto(
                min_steps_per_wvl=self.config.domain.grid_min_steps_per_wvl,
                wavelength=self.config.frequency.wavelength_um,
            ),
            run_time=self.config.domain.run_time_s,
            structures=bundle.structures,
            sources=(source,),
            monitors=self.monitors.build_monitors(),
            lumped_elements=bundle.lumped_elements,
            boundary_spec=self._boundary_spec(source),
            symmetry=self.config.domain.symmetry,
            shutoff=self.config.domain.shutoff,
            courant=self.config.domain.courant,
            subpixel=True,
            medium=td.Medium(permittivity=1.0),
            plot_length_units=self.config.domain.plot_length_units,
            structure_priority_mode="conductor",
        )
        ConvergenceChecker(self.config).validate_simulation(sim)
        return sim

    def _case_to_capacitance(self, case_label: str) -> float:
        mapping = {
            "baseline": 0.0,
            "pec_reference": 0.0,
            "low_capacitance": self.config.ris.varactor_states_pf[0],
            "high_capacitance": self.config.ris.varactor_states_pf[1],
            "0.1pf": self.config.ris.varactor_states_pf[0],
            "1.0pf": self.config.ris.varactor_states_pf[1],
        }
        return mapping.get(case_label.lower(), self.config.ris.varactor_states_pf[0])

    def estimate_cost(self, simulation: td.Simulation, task_name: str) -> float:
        job = web.Job(simulation=simulation, task_name=task_name, verbose=False)
        return float(web.estimate_cost(job.task_id))

    def run_simulation(self, simulation: td.Simulation, task_name: str):
        self.last_simulation_data = web.run(
            simulation,
            task_name=task_name,
            path=f"results/{task_name}.hdf5",
            verbose=True,
        )
        return self.last_simulation_data


class CostEstimator:
    """Estimate and compare cost-saving simulation variants."""

    def _strategy_plan(self, config: SimulationConfig) -> tuple[CostStrategy, ...]:
        current_steps = config.domain.grid_min_steps_per_wvl
        reduced_steps = max(8, int(round(current_steps * 0.6)))
        combined_steps = max(8, int(round(current_steps * 0.72)))
        shorter_runtime = max(config.domain.run_time_s * 0.5, config.domain.run_time_s * 0.25)

        strategies: list[CostStrategy] = [
            CostStrategy(label="Baseline"),
            CostStrategy(label="Reduced resolution", grid_min_steps_per_wvl=reduced_steps),
            CostStrategy(label="Shorter run time", run_time_s=shorter_runtime),
            CostStrategy(
                label="Combined",
                grid_min_steps_per_wvl=combined_steps,
                run_time_s=shorter_runtime,
            ),
        ]

        if any(config.domain.symmetry):
            strategies.append(CostStrategy(label="Symmetry", symmetry=config.domain.symmetry))

        return tuple(strategies)

    def _build_variant_builder(
        self,
        builder: SimulationBuilder,
        strategy: CostStrategy,
    ) -> SimulationBuilder:
        domain = builder.config.domain
        if strategy.grid_min_steps_per_wvl is not None:
            domain = replace(domain, grid_min_steps_per_wvl=strategy.grid_min_steps_per_wvl)
        if strategy.run_time_s is not None:
            domain = replace(domain, run_time_s=strategy.run_time_s)
        if strategy.symmetry is not None:
            domain = replace(domain, symmetry=strategy.symmetry)
        return SimulationBuilder(replace(builder.config, domain=domain))

    def _build_cost_estimate(
        self,
        simulation: td.Simulation,
        label: str,
        task_name: str,
        grid_min_steps_per_wvl: int,
        run_time_s: float,
        symmetry: tuple[int, int, int],
    ) -> CostEstimate:
        job = web.Job(simulation=simulation, task_name=task_name, verbose=False)
        cost = float(web.estimate_cost(job.task_id))
        return CostEstimate(
            label=label,
            task_name=task_name,
            estimated_cost=cost,
            grid_min_steps_per_wvl=grid_min_steps_per_wvl,
            run_time_s=run_time_s,
            symmetry=symmetry,
        )

    def estimate(self, simulation: td.Simulation, task_name: str = "ris_task") -> float:
        job = web.Job(simulation=simulation, task_name=task_name, verbose=False)
        return float(web.estimate_cost(job.task_id))

    def estimate_plan(
        self,
        builder: SimulationBuilder,
        case_label: str = "low_capacitance",
        task_name_prefix: str = "ris",
    ) -> CostEstimationReport:
        baseline_simulation = builder.build_simulation(case_label=case_label)
        baseline = self._build_cost_estimate(
            baseline_simulation,
            label="Baseline",
            task_name=f"{task_name_prefix}_{case_label}_baseline",
            grid_min_steps_per_wvl=builder.config.domain.grid_min_steps_per_wvl,
            run_time_s=builder.config.domain.run_time_s,
            symmetry=builder.config.domain.symmetry,
        )

        candidates = [baseline]
        for strategy in self._strategy_plan(builder.config):
            if strategy.label == "Baseline":
                continue
            variant_builder = self._build_variant_builder(builder, strategy)
            variant_simulation = variant_builder.build_simulation(case_label=case_label)
            strategy_task_name = (
                f"{task_name_prefix}_{case_label}_{strategy.label.lower().replace(' ', '_')}"
            )
            candidates.append(
                self._build_cost_estimate(
                    variant_simulation,
                    label=strategy.label,
                    task_name=strategy_task_name,
                    grid_min_steps_per_wvl=strategy.grid_min_steps_per_wvl
                    if strategy.grid_min_steps_per_wvl is not None
                    else builder.config.domain.grid_min_steps_per_wvl,
                    run_time_s=strategy.run_time_s
                    if strategy.run_time_s is not None
                    else builder.config.domain.run_time_s,
                    symmetry=strategy.symmetry
                    if strategy.symmetry is not None
                    else builder.config.domain.symmetry,
                )
            )

        return CostEstimationReport(baseline=baseline, candidates=tuple(candidates))
