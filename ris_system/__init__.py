"""Public package interface for the RIS reproduction codebase."""

from .config import (  # noqa
    DomainConfig,
    FrequencyConfig,
    MonitorConfig,
    RISArrayConfig,
    SimulationConfig,
    SourceConfig,
    build_default_config,
)

from .convergence import ConvergenceChecker, ValidationReport
from .data import load_case_data, resolve_sim_data
from .materials import MaterialFactory
from .postprocess import AnalysisResult, PostProcessor
from .simulation import (
    CostEstimate,
    CostEstimationReport,
    CostEstimator,
    CostStrategy,
    SimulationBuilder,
    SimulationCase,
)
from .visualization import Plotter
from .workflow import (
    build_case_simulations,
    build_no_ris_simulation,
    run_case_simulations,
    run_no_ris_reference,
)

__all__ = [
    "Plotter",
    "CostEstimate",
    "CostEstimationReport",
    "CostStrategy",
    "DomainConfig",
    "SourceConfig",
    "CostEstimator",
    "MonitorConfig",
    "PostProcessor",
    "AnalysisResult",
    "RISArrayConfig",
    "FrequencyConfig",
    "MaterialFactory",
    "SimulationConfig",
    "SimulationCase",
    "ValidationReport",
    "ConvergenceChecker",
    "SimulationBuilder",
    "build_case_simulations",
    "build_default_config",
    "build_no_ris_simulation",
    "load_case_data",
    "resolve_sim_data",
    "run_case_simulations",
    "run_no_ris_reference",
]
