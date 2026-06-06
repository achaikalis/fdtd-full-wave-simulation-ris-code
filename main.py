"""Entry point for the Tidy3D RIS reproduction workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from ris_system import (
    ConvergenceChecker,
    CostEstimator,
    Plotter,
    PostProcessor,
    SimulationBuilder,
    SimulationConfig,
    build_default_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RIS reproduction workflow using Tidy3D only.",
    )
    parser.add_argument(
        "--mode",
        choices=("validate", "estimate", "run", "analyze", "inspect"),
        default="validate",
        help="Workflow mode to execute.",
    )
    parser.add_argument(
        "--case",
        default="low_capacitance",
        help="Case label used for the baseline simulation build.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory used for exported plots and reports.",
    )
    return parser.parse_args()


def run_workflow(
    config: SimulationConfig,
    mode: str,
    case_label: str,
    output_dir: Path,
) -> int:
    convergence = ConvergenceChecker(config)
    report = convergence.validate_configuration()
    for message in report.messages:
        print(message)

    if not report.ok and mode != "inspect":
        return 1

    builder = SimulationBuilder(config)
    simulation = builder.build_simulation(case_label=case_label)

    cost_estimator = CostEstimator()
    cost_report = cost_estimator.estimate_plan(builder, case_label=case_label)
    print(cost_report.summary())
    print(f"Estimated maximum cost: {cost_report.baseline.estimated_cost:.3f} FlexCredits")
    print(
        f"Estimated minimum cost: {cost_report.best.estimated_cost:.3f} FlexCredits "
        f"({cost_report.best.label})"
    )

    if mode in {"validate", "estimate", "inspect"}:
        plotter = Plotter(config)
        plotter.save_overview(simulation, output_dir=output_dir, case_label=case_label)
        return 0

    if mode == "run":
        simulation_data = builder.run_simulation(simulation, task_name=f"ris_{case_label}")
        plotter = Plotter(config)
        plotter.save_run_outputs(
            simulation_data,
            output_dir=output_dir,
            case_label=case_label,
        )
        print("Simulation submitted successfully.")
        return 0

    if mode == "analyze":
        if builder.last_simulation_data is None:
            print("No simulation data available. Run the simulation first.")
            return 1
        post = PostProcessor(config)
        result = post.analyze(builder.last_simulation_data)
        plotter = Plotter(config)
        plotter.save_metrics(result, output_dir=output_dir, case_label=case_label)
        print(result.summary())
        return 0

    return 0


def main() -> int:
    args = parse_args()
    config = build_default_config()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    return run_workflow(config, args.mode, args.case, args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
