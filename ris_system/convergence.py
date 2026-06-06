"""Validation and convergence checks for the RIS reproduction workflow."""

from __future__ import annotations

from dataclasses import dataclass, field

import tidy3d as td

from .config import SimulationConfig


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    messages: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


class ConvergenceChecker:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def _check_domain_margin(self) -> list[str]:
        messages: list[str] = []
        x_half, y_half, z_half = self.config.domain.half_size_um
        aperture_half = self.config.ris.aperture_um / 2.0
        min_clearance = min(x_half - aperture_half, z_half - aperture_half)
        if min_clearance <= self.config.ris.substrate_thickness_um:
            messages.append("Domain is too small for the RIS aperture and PML margin.")
        else:
            messages.append("Domain clearance check passed.")
        if y_half <= self.config.ris.substrate_thickness_um + self.config.ris.ground_thickness_um:
            messages.append("Propagation axis clearance is too small for source placement.")
        return messages

    def _check_monitor_positions(self) -> list[str]:
        messages: list[str] = []
        x_half, y_half, z_half = self.config.domain.half_size_um
        for name, point in zip(self.config.monitors.point_names, self.config.monitors.point_positions_um): # noqa: E501
            x, y, z = point
            inside = (-x_half <= x <= x_half) and (-y_half <= y <= y_half) and (-z_half <= z <= z_half) # noqa: E501
            if inside:
                messages.append(f"Monitor {name} is inside the simulation domain.")
            else:
                messages.append(f"Monitor {name} is outside the simulation domain.")
        return messages

    def _check_runtime(self) -> list[str]:
        messages: list[str] = []
        period_s = 1.0 / self.config.frequency.center_hz
        paper_periods = 100
        paper_runtime_s = paper_periods * period_s
        if self.config.domain.run_time_s < paper_runtime_s:
            messages.append(
                f"Run time may be short for the paper's "
                f"{paper_periods}-period budget."
            )
        else:
            messages.append(
                f"Run time is consistent with the paper's "
                f"{paper_periods}-period budget."
            )
        messages.append(
            f"Paper temporal-step target is {self.config.domain.target_dt_ps:.3g} ps."
        )
        return messages

    def validate_configuration(self) -> ValidationReport:
        messages = []
        warnings = []
        messages.extend(self._check_domain_margin())
        messages.extend(self._check_monitor_positions())
        messages.extend(self._check_runtime())
        ok = not any("too small" in message or "outside" in message for message in messages)
        if self.config.source.use_fixed_angle:
            warnings.append("Fixed-angle plane-wave mode should be paired with periodic boundaries.") # noqa: E501
        return ValidationReport(ok=ok, messages=tuple(messages), warnings=tuple(warnings))

    def validate_simulation(self, simulation: td.Simulation) -> ValidationReport:
        try:
            simulation.validate_pre_upload(source_required=True)
            messages = ("Simulation pre-upload validation passed.",)
            return ValidationReport(ok=True, messages=messages, warnings=tuple())
        except Exception as exc:  # pragma: no cover - validation path
            return ValidationReport(ok=False, messages=(f"Simulation validation failed: {exc}",), warnings=tuple()) # noqa: E501
