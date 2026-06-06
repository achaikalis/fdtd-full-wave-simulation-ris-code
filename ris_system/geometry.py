"""Geometry assembly for the RIS reproduction workflow."""

from __future__ import annotations

from dataclasses import dataclass

import tidy3d as td

from .config import SimulationConfig
from .materials import MaterialFactory


@dataclass(frozen=True)
class GeometryBundle:
    structures: tuple[td.Structure, ...]
    lumped_elements: tuple[td.ComponentBase, ...]
    cross_section: dict[str, tuple[float, float, float] | float]


class GeometryFactory:
    def __init__(self, config: SimulationConfig, materials: MaterialFactory):
        self.config = config
        self.materials = materials

    def _patch_centers(self) -> list[tuple[float, float, float]]:
        y_center = self.config.ris.patch_thickness_um / 2.0
        centers: list[tuple[float, float, float]] = []
        for x in self.config.ris.x_positions_um:
            for z in self.config.ris.z_positions_um:
                centers.append((x, y_center, z))
        return centers

    def build_substrate(self) -> td.Structure:
        return td.Structure(
            geometry=td.Box(
                center=(0.0, -self.config.ris.substrate_thickness_um / 2.0, 0.0),
                size=(
                    self.config.ris.aperture_um,
                    self.config.ris.substrate_thickness_um,
                    self.config.ris.aperture_um,
                ),
            ),
            medium=self.materials.build_substrate(),
        )

    def build_ground_plane(self) -> td.Structure:
        y_center = (
            -self.config.ris.substrate_thickness_um - self.config.ris.ground_thickness_um / 2.0
        )
        return td.Structure(
            geometry=td.Box(
                center=(0.0, y_center, 0.0),
                size=(
                    self.config.ris.aperture_um,
                    self.config.ris.ground_thickness_um,
                    self.config.ris.aperture_um,
                ),
            ),
            medium=self.materials.build_conductor(),
        )

    def build_patches(self) -> tuple[td.Structure, ...]:
        structures: list[td.Structure] = []
        for index, (x_pos, y_pos, z_pos) in enumerate(self._patch_centers()):
            structures.append(
                td.Structure(
                    geometry=td.Box(
                        center=(x_pos, y_pos, z_pos),
                        size=(
                            self.config.ris.patch_size_um,
                            self.config.ris.patch_thickness_um,
                            self.config.ris.patch_size_um,
                        ),
                    ),
                    medium=self.materials.build_conductor(),
                )
            )
        return tuple(structures)

    def build_varactors(self, capacitance_pf: float) -> tuple[td.ComponentBase, ...]:
        lumped_elements: list[td.ComponentBase] = []
        patch_y = self.config.ris.patch_thickness_um / 2.0
        cell_um = self.config.ris.varactor_cell_size_um
        counter = 0

        x_positions = self.config.ris.x_positions_um
        z_positions = self.config.ris.z_positions_um

        for row_index, z_pos in enumerate(z_positions):
            for col_index in range(self.config.ris.cols - 1):
                counter += 1
                x_left = x_positions[col_index]
                x_right = x_positions[col_index + 1]
                center = ((x_left + x_right) / 2.0, patch_y, z_pos)
                size = (cell_um, 0.0, cell_um)
                lumped_elements.append(
                    self.materials.build_varactor_element(
                        name=f"var_x_{counter}",
                        center=center,
                        size=size,
                        voltage_axis=0,
                        capacitance_pf=capacitance_pf,
                    )
                )

        for col_index, x_pos in enumerate(x_positions):
            for row_index in range(self.config.ris.rows - 1):
                counter += 1
                z_bottom = z_positions[row_index]
                z_top = z_positions[row_index + 1]
                center = (x_pos, patch_y, (z_bottom + z_top) / 2.0)
                size = (cell_um, 0.0, cell_um)
                lumped_elements.append(
                    self.materials.build_varactor_element(
                        name=f"var_z_{counter}",
                        center=center,
                        size=size,
                        voltage_axis=2,
                        capacitance_pf=capacitance_pf,
                    )
                )

        return tuple(lumped_elements[: self.config.ris.varactor_count])

    def build_bundle(self, capacitance_pf: float) -> GeometryBundle:
        substrate = self.build_substrate()
        ground_plane = self.build_ground_plane()
        patches = self.build_patches()
        lumped_elements = self.build_varactors(capacitance_pf)
        cross_section = {
            "aperture_um": self.config.ris.aperture_um,
            "substrate_thickness_um": self.config.ris.substrate_thickness_um,
            "patch_size_um": self.config.ris.patch_size_um,
            "patch_thickness_um": self.config.ris.patch_thickness_um,
            "ground_y_um": (
                -self.config.ris.substrate_thickness_um
                - self.config.ris.ground_thickness_um / 2.0
            ),
        }
        return GeometryBundle(
            structures=(substrate, ground_plane, *patches),
            lumped_elements=lumped_elements,
            cross_section=cross_section,
        )
