"""Material and lumped-element factories for the RIS reproduction workflow."""

from __future__ import annotations

from dataclasses import dataclass

import tidy3d as td
import tidy3d.rf as rf

from .config import SimulationConfig
from .utils import s_per_m_to_s_per_um


@dataclass(frozen=True)
class MaterialSet:
    substrate: td.AbstractMedium
    conductor: td.AbstractMedium


class MaterialFactory:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def build_substrate(self) -> td.Medium:
        return td.Medium(
            permittivity=self.config.ris.substrate_relative_permittivity,
            conductivity=s_per_m_to_s_per_um(self.config.ris.substrate_conductivity_s_m),
            name="substrate",
        )

    def build_conductor(self) -> td.AbstractMedium:
        pec_cls = getattr(td, "PECMedium", None)
        if pec_cls is not None:
            return pec_cls(name="pec")
        return td.Medium(permittivity=1e9, conductivity=0.0, name="pec_approx")

    def build_material_set(self) -> MaterialSet:
        return MaterialSet(
            substrate=self.build_substrate(),
            conductor=self.build_conductor(),
        )

    def build_varactor_network(self, capacitance_pf: float) -> rf.RLCNetwork:
        return rf.RLCNetwork(
            resistance=2.0,
            inductance=0.05e-9,
            capacitance=capacitance_pf * 1e-12,
            network_topology="series",
        )

    def build_varactor_element(
        self,
        name: str,
        center: tuple[float, float, float],
        size: tuple[float, float, float],
        voltage_axis: int,
        capacitance_pf: float,
    ) -> rf.LinearLumpedElement:
        return rf.LinearLumpedElement(
            name=name,
            center=center,
            size=size,
            voltage_axis=voltage_axis,
            network=self.build_varactor_network(capacitance_pf),
            dist_type="on",
        )
