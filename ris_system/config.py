"""Configuration schema for the RIS reproduction workflow."""

from __future__ import annotations

from dataclasses import dataclass, field

from .utils import centered_positions, hz_to_wavelength_um, mm_to_um


@dataclass(frozen=True)
class FrequencyConfig:
    """Frequency sweep configuration for the RIS simulation."""

    min_hz: float = 0.8e9
    max_hz: float = 8.4e9
    center_hz: float = 4.6e9
    samples: int = 121

    @property
    def bandwidth_hz(self) -> float:
        return self.max_hz - self.min_hz

    @property
    def wavelength_um(self) -> float:
        return hz_to_wavelength_um(self.center_hz)

    def freqs_hz(self) -> list[float]:
        if self.samples <= 1:
            return [self.center_hz]
        step = self.bandwidth_hz / (self.samples - 1)
        return [self.min_hz + idx * step for idx in range(self.samples)]


@dataclass(frozen=True)
class DomainConfig:
    """Simulation domain, boundary, solver, and runtime settings."""

    size_um: tuple[float, float, float] = (220_000.0, 110_000.0, 220_000.0)
    pml_layers: int = 20
    grid_min_steps_per_wvl: int = 20
    courant: float = 0.95
    target_dt_ps: float = 1.5
    shutoff: float = 1e-5
    run_time_s: float = 100.0 / 4.6e9
    symmetry: tuple[int, int, int] = (0, 0, 0)
    plot_length_units: str = "um"

    @property
    def half_size_um(self) -> tuple[float, float, float]:
        return tuple(value / 2.0 for value in self.size_um)


@dataclass(frozen=True)
class RISArrayConfig:
    """Configuration for RIS array geometry and lumped varactor states."""

    rows: int = 10
    cols: int = 10
    pitch_mm: float = 110.0 / 9.0
    patch_size_mm: float = 10.0
    patch_thickness_um: float = 35.0
    substrate_thickness_mm: float = 1.0
    substrate_relative_permittivity: float = 4.4
    substrate_conductivity_s_m: float = 0.0025
    ground_thickness_um: float = 35.0
    varactor_count: int = 180
    varactor_cell_size_um: float = 1_000.0
    varactor_states_pf: tuple[float, float] = (0.1, 1.0)

    @property
    def patch_size_um(self) -> float:
        return mm_to_um(self.patch_size_mm)

    @property
    def pitch_um(self) -> float:
        return mm_to_um(self.pitch_mm)

    @property
    def substrate_thickness_um(self) -> float:
        return mm_to_um(self.substrate_thickness_mm)

    @property
    def aperture_um(self) -> float:
        return (self.cols - 1) * self.pitch_um + self.patch_size_um

    @property
    def x_positions_um(self) -> list[float]:
        return centered_positions(self.cols, self.pitch_um)

    @property
    def z_positions_um(self) -> list[float]:
        return centered_positions(self.rows, self.pitch_um)


@dataclass(frozen=True)
class SourceConfig:
    """Plane-wave source settings."""

    num_freqs: int = 3
    pol_angle_rad: float = 1.57
    angle_theta_rad: float = 0.78
    angle_phi_rad: float = 0.78
    direction: str = "+"
    use_fixed_angle: bool = True
    polarization_cases: tuple[tuple[str, float], ...] = (
        ("vertical", 1.57),
        ("horizontal", 0.0),
    )
    source_center_offset_um: float = 10_000.0


@dataclass(frozen=True)
class MonitorConfig:
    """Monitor settings for point probes and a field plane."""

    point_names: tuple[str, str, str] = ("P1", "P2", "P3")
    point_positions_um: tuple[tuple[float, float, float], ...] = (
        (-100_000.0, 45_000.0, -100_000.0),
        (-100_000.0, 45_000.0, -10_000.0),
        (100_000.0, 45_000.0, 100_000.0),
    )
    field_plane_name: str = "RIS Surface"
    field_freq_samples: int = 3
    field_plane_height_um: float = 0.0
    field_plane_margin_um: float = 5_000.0
    fields: tuple[str, ...] = ("Ex", "Ey", "Ez", "Hx", "Hy", "Hz")


@dataclass(frozen=True)
class SimulationConfig:
    """Top-level configuration for the RIS simulation workflow."""

    frequency: FrequencyConfig = field(default_factory=FrequencyConfig)
    domain: DomainConfig = field(default_factory=DomainConfig)
    ris: RISArrayConfig = field(default_factory=RISArrayConfig)
    source: SourceConfig = field(default_factory=SourceConfig)
    monitors: MonitorConfig = field(default_factory=MonitorConfig)

    @property
    def array_extent_um(self) -> float:
        return self.ris.aperture_um


def build_default_config() -> SimulationConfig:
    """Create the default RIS simulation configuration."""
    return SimulationConfig()
