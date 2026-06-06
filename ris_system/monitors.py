"""Monitor construction for the RIS reproduction workflow."""

from __future__ import annotations

import tidy3d as td

from .config import SimulationConfig


class MonitorFactory:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def build_point_monitors(self) -> tuple[td.FieldTimeMonitor, ...]:
        monitors: list[td.FieldTimeMonitor] = []
        for name, center in zip(
            self.config.monitors.point_names,
            self.config.monitors.point_positions_um,
        ):
            monitors.append(
                td.FieldTimeMonitor(
                    center=center,
                    size=(0.0, 0.0, 0.0),
                    fields=list(self.config.monitors.fields),
                    start=0.0,
                    stop=self.config.domain.run_time_s,
                    interval=1,
                    colocate=True,
                    name=name,
                )
            )
        return tuple(monitors)

    def build_field_monitor(self) -> td.FieldMonitor:
        aperture = self.config.ris.aperture_um + 2.0 * self.config.monitors.field_plane_margin_um
        freq_step = max(
            1,
            self.config.frequency.samples // self.config.monitors.field_freq_samples,
        )
        return td.FieldMonitor(
            center=(0.0, self.config.monitors.field_plane_height_um, 0.0),
            size=(aperture, 0.0, aperture),
            fields=list(self.config.monitors.fields),
            freqs=self.config.frequency.freqs_hz()[::freq_step],
            colocate=True,
            name=self.config.monitors.field_plane_name,
        )

    def build_monitors(self) -> tuple[td.Monitor, ...]:
        return (*self.build_point_monitors(), self.build_field_monitor())
