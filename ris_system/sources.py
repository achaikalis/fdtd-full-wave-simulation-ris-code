"""Source construction for the RIS reproduction workflow."""

from __future__ import annotations

import tidy3d as td

from .config import SimulationConfig


class SourceFactory:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def build_source(self) -> td.PlaneWave:
        source_center = (
            0.0,
            -self.config.domain.size_um[1] / 2.0 + self.config.source.source_center_offset_um,
            0.0,
        )
        pulse = td.GaussianPulse(
            freq0=self.config.frequency.center_hz,
            fwidth=self.config.frequency.bandwidth_hz,
        )
        kwargs = {
            "center": source_center,
            "size": (td.inf, 0.0, td.inf),
            "source_time": pulse,
            "direction": self.config.source.direction,
            "pol_angle": self.config.source.pol_angle_rad,
            "num_freqs": self.config.source.num_freqs,
            "name": "incident_plane_wave",
        }
        if self.config.source.use_fixed_angle:
            kwargs["angle_theta"] = self.config.source.angle_theta_rad
            kwargs["angle_phi"] = self.config.source.angle_phi_rad
        return td.PlaneWave(**kwargs)
