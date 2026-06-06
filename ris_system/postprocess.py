"""Post-processing helpers for the RIS reproduction workflow."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SimulationConfig


@dataclass(frozen=True)
class AnalysisResult:
    case_label: str
    dominant_frequency_hz: float | None
    peak_amplitude: float | None
    rms_amplitude: float | None
    spectra: dict[str, tuple[np.ndarray, np.ndarray]]
    notes: tuple[str, ...]

    def summary(self) -> str:
        parts = [f"Case: {self.case_label}"]
        if self.dominant_frequency_hz is not None:
            parts.append(f"Dominant frequency: {self.dominant_frequency_hz / 1e9:.3f} GHz")
        if self.peak_amplitude is not None:
            parts.append(f"Peak amplitude: {self.peak_amplitude:.3e}")
        if self.rms_amplitude is not None:
            parts.append(f"RMS amplitude: {self.rms_amplitude:.3e}")
        if self.notes:
            parts.append("Notes: " + "; ".join(self.notes))
        return " | ".join(parts)


class PostProcessor:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def _extract_array(self, data, name: str):
        candidate = data[name] if hasattr(data, "__getitem__") else getattr(data, name, None)
        if candidate is None:
            return None
        if hasattr(candidate, "values"):
            return np.asarray(candidate.values)
        if hasattr(candidate, "Ez"):
            field_candidate = candidate.Ez
            if hasattr(field_candidate, "values"):
                return np.asarray(field_candidate.values)
            return np.asarray(field_candidate)
        return np.asarray(candidate)

    def _pick_time_series(self, monitor_data):
        for component_name in self.config.monitors.fields:
            if hasattr(monitor_data, component_name):
                component = getattr(monitor_data, component_name)
                if hasattr(component, "coords"):
                    if "t" in component.coords:
                        return np.asarray(component.coords["t"])
                    if "time" in component.coords:
                        return np.asarray(component.coords["time"])
        return None

    def _dominant_frequency(self, signal: np.ndarray, time_s: np.ndarray) -> float | None:
        if signal.ndim == 0 or time_s.size < 2:
            return None
        dt = float(time_s[1] - time_s[0])
        signal = np.asarray(signal).reshape(-1)
        if np.iscomplexobj(signal):
            spectrum = np.fft.fft(signal)
            frequencies = np.fft.fftfreq(signal.size, dt)
            positive = frequencies >= 0.0
            spectrum = spectrum[positive]
            frequencies = frequencies[positive]
        else:
            spectrum = np.fft.rfft(signal)
            frequencies = np.fft.rfftfreq(signal.size, dt)
        return float(frequencies[int(np.argmax(np.abs(spectrum)))])

    def analyze(self, sim_data, case_label: str = "ris_case") -> AnalysisResult:
        notes: list[str] = []
        dominant_frequency_hz = None
        peak_amplitude = None
        rms_amplitude = None
        spectra: dict[str, tuple[np.ndarray, np.ndarray]] = {}

        for monitor_name in self.config.monitors.point_names:
            monitor_data = sim_data[monitor_name] if hasattr(sim_data, "__getitem__") else getattr(sim_data, monitor_name, None) # noqa: E501
            if monitor_data is None:
                continue

            candidate = self._extract_array(monitor_data, "Ez")
            if candidate is None:
                continue

            flattened = np.asarray(candidate).reshape(-1)
            peak_amplitude = float(np.max(np.abs(flattened)))
            rms_amplitude = float(np.sqrt(np.mean(np.abs(flattened) ** 2)))
            time_series = self._pick_time_series(monitor_data)
            if time_series is not None:
                dominant_frequency_hz = self._dominant_frequency(flattened, time_series)
            break

        if peak_amplitude is None:
            notes.append("No point-monitor data found in the returned dataset.")

        if hasattr(sim_data, self.config.monitors.field_plane_name):
            notes.append("Plane monitor data is available for field map inspection.")

        return AnalysisResult(
            case_label=case_label,
            dominant_frequency_hz=dominant_frequency_hz,
            peak_amplitude=peak_amplitude,
            rms_amplitude=rms_amplitude,
            spectra=spectra,
            notes=tuple(notes),
        )
