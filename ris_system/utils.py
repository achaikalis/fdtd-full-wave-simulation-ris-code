"""Shared helpers for the RIS reproduction codebase."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

MM_TO_UM = 1000.0
UM_TO_MM = 1.0 / MM_TO_UM
S_PER_M_TO_S_PER_UM = 1e-6


def mm_to_um(value: float) -> float:
    return float(value) * MM_TO_UM


def um_to_mm(value: float) -> float:
    return float(value) * UM_TO_MM


def s_per_m_to_s_per_um(value: float) -> float:
    return float(value) * S_PER_M_TO_S_PER_UM


def hz_to_wavelength_um(freq_hz: float) -> float:
    return 299_792_458.0 / float(freq_hz) * 1e6


def centered_positions(count: int, pitch_um: float) -> list[float]:
    if count <= 0:
        return []
    offset = (count - 1) * pitch_um / 2.0
    return [index * pitch_um - offset for index in range(count)]


def validate_positive(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return float(value)


def validate_nonnegative(value: float, name: str) -> float:
    if value < 0:
        raise ValueError(f"{name} must be nonnegative.")
    return float(value)


def ensure_length_3(values: Sequence[float], name: str) -> tuple[float, float, float]:
    if len(values) != 3:
        raise ValueError(f"{name} must have length 3.")
    return float(values[0]), float(values[1]), float(values[2])


def ensure_path(path: str | Path) -> Path:
    return Path(path)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class NamedQuantity:
    name: str
    value: float
