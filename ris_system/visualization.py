"""Plotting and report helpers for the RIS reproduction workflow."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401

from .config import SimulationConfig
from .data import load_case_data
from .postprocess import AnalysisResult
from .simulation import SimulationBuilder

plt.style.use(["ieee", "science", "no-latex"])


class Plotter:
    """Helper for layout, cross-section, metric, and comparison plots."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.builder = SimulationBuilder(config)

    def plot_layout(self, case_label: str = "low_capacitance"):
        simulation = self.builder.build_simulation(case_label=case_label)
        fig, ax = plt.subplots(figsize=(9, 6))
        simulation.plot(y=0.0, ax=ax)
        simulation.plot_grid(y=0.0, ax=ax)
        ax.set_title(f"RIS layout - {case_label}")
        return fig

    def plot_cross_section(self, case_label: str = "low_capacitance"):
        simulation = self.builder.build_simulation(case_label=case_label)
        fig, ax = plt.subplots(figsize=(9, 6))
        simulation.plot(x=0.0, ax=ax)
        simulation.plot_grid(x=0.0, ax=ax)
        ax.set_title(f"RIS cross section - {case_label}")
        return fig

    def save_overview(
        self,
        simulation,
        output_dir: str | Path = Path("reports"),
        case_label: str = "low_capacitance",
    ) -> tuple[Path, Path]:
        """Save layout and cross-section overview plots for a simulation."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        layout_fig, layout_ax = plt.subplots(figsize=(9, 6))
        simulation.plot(y=0.0, ax=layout_ax)
        simulation.plot_grid(y=0.0, ax=layout_ax)
        layout_ax.set_title(f"RIS layout - {case_label}")
        layout_path = self.save_svg_plot(
            layout_fig,
            output_stem=f"{case_label}_layout",
            output_dir=output_dir,
        )
        plt.close(layout_fig)

        cross_section_fig, cross_section_ax = plt.subplots(figsize=(9, 6))
        simulation.plot(x=0.0, ax=cross_section_ax)
        simulation.plot_grid(x=0.0, ax=cross_section_ax)
        cross_section_ax.set_title(f"RIS cross section - {case_label}")
        cross_section_path = self.save_svg_plot(
            cross_section_fig,
            output_stem=f"{case_label}_cross_section",
            output_dir=output_dir,
        )
        plt.close(cross_section_fig)

        return layout_path, cross_section_path

    def save_metrics(self, result: AnalysisResult, output_dir: Path, case_label: str) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{case_label}_metrics.txt"
        output_path.write_text(result.summary())
        return output_path

    def save_run_outputs(
        self,
        sim_data,
        output_dir: str | Path = Path("reports"),
        case_label: str = "low_capacitance",
    ) -> list[Path]:
        """Save point-probe Ey traces and the |E| field map for one completed run."""
        output_paths: list[Path] = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for monitor_name in self.config.monitors.point_names:
            try:
                monitor_data = sim_data[monitor_name]
            except (KeyError, TypeError):
                print(f"Missing point monitor data: {monitor_name}")
                continue

            trace = monitor_data.Ey
            time_coord = "t" if "t" in trace.coords else "time"
            trace_values = np.asarray(trace.values).reshape(-1)
            time_values_ns = np.asarray(trace.coords[time_coord]).reshape(-1) * 1e9

            fig, ax = plt.subplots(figsize=(9, 4.5))
            ax.plot(time_values_ns, trace_values.real, label=case_label)
            ax.set_title(f"{monitor_name} electric field - {case_label}")
            ax.set_xlabel("Time (ns)")
            ax.set_ylabel("Ey (V/m)")
            ax.set_xlim(0.0, 4.0)
            ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.8)
            ax.legend(loc="best", frameon=True, fancybox=True, framealpha=0.95)
            output_paths.append(
                self.save_svg_plot(
                    fig,
                    output_stem=f"{case_label}_{monitor_name}_Ey",
                    output_dir=output_dir,
                )
            )
            plt.close(fig)

        field_monitor_name = self.config.monitors.field_plane_name
        try:
            sim_data[field_monitor_name]
        except (KeyError, TypeError):
            print(f"Missing field monitor data: {field_monitor_name}")
            return output_paths

        ax = sim_data.plot_field(
            field_monitor_name=field_monitor_name,
            field_name="E",
            f=self.config.frequency.center_hz,
            val="abs",
            eps_alpha=0.2,
            phase=0,
        )
        zoom_half_width_um = min(25_000.0, self.config.ris.aperture_um / 4.0)
        ax.set_xlim(-zoom_half_width_um, zoom_half_width_um)
        ax.set_ylim(-zoom_half_width_um, zoom_half_width_um)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.8)
        ax.set_title(f"|E| field distribution - {case_label}")
        output_paths.append(
            self.save_svg_plot(
                ax.figure,
                output_stem=f"{case_label}_field_distribution_abs_E",
                output_dir=output_dir,
            )
        )
        plt.close(ax.figure)

        return output_paths

    def save_svg_plot(
        self,
        fig,
        output_stem: str,
        output_dir: str | Path = Path("reports"),
    ) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{output_stem}.svg"
        fig.savefig(output_path, format="svg", bbox_inches="tight")
        print(f"Saved SVG plot to {output_path}")
        return output_path

    def plot_point_comparison(
        self,
        title: str,
        monitor_name: str,
        output_stem: str,
        sim_data_cases=None,
        no_ris_data=None,
        results_dir: str | Path = Path("results"),
        reports_dir: str | Path = Path("reports"),
    ) -> None:
        """Plot PEC, 0.1 pF, and 1.0 pF traces for one monitor."""
        case_labels = ("pec_reference", "low_capacitance", "high_capacitance")
        case_names = ("PEC surface", "0.1 pF", "1.0 pF")
        fig, ax = plt.subplots(figsize=(9, 4.5))

        for case_label_value, case_name in zip(case_labels, case_names):
            sim_data_case = load_case_data(
                case_label_value,
                sim_data_cases=sim_data_cases,
                no_ris_data=no_ris_data,
                results_dir=results_dir,
            )
            if sim_data_case is None:
                continue
            monitor_data = sim_data_case[monitor_name]
            trace = monitor_data.Ey
            time_coord = "t" if "t" in trace.coords else "time"
            trace_values = np.asarray(trace.values).reshape(-1)
            time_values_ns = np.asarray(trace.coords[time_coord]).reshape(-1) * 1e9
            ax.plot(
                time_values_ns,
                trace_values.real,
                label=case_name,
            )

        ax.set_title(title)
        ax.set_xlabel("Time (ns)")
        ax.set_ylabel("Ey (V/m)")
        ax.set_xlim(0.0, 4.0)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.8)
        ax.legend(loc="best", frameon=True, fancybox=True, framealpha=0.95)
        self.save_svg_plot(fig, output_stem=output_stem, output_dir=reports_dir)
        plt.show()

    def plot_field_plane(
        self,
        case_label_value: str,
        monitor_name: str,
        title: str,
        output_stem: str,
        sim_data_cases=None,
        no_ris_data=None,
        results_dir: str | Path = Path("results"),
        reports_dir: str | Path = Path("reports"),
    ) -> None:
        """Plot one 2D electric-field plane from a shared HDF5 result."""
        sim_data_case = load_case_data(
            case_label_value,
            sim_data_cases=sim_data_cases,
            no_ris_data=no_ris_data,
            results_dir=results_dir,
        )
        if sim_data_case is None:
            return
        ax = sim_data_case.plot_field(
            field_monitor_name=monitor_name,
            field_name="E",
            f=self.config.frequency.center_hz,
            val="abs",
            eps_alpha=0.2,
            phase=0,
        )
        zoom_half_width_um = min(25_000.0, self.config.ris.aperture_um / 4.0)
        ax.set_xlim(-zoom_half_width_um, zoom_half_width_um)
        ax.set_ylim(-zoom_half_width_um, zoom_half_width_um)
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.8)
        ax.set_title(title)
        self.save_svg_plot(ax.figure, output_stem=output_stem, output_dir=reports_dir)
        plt.show()
