# Source of truth for RedBand's version
__version__ = "0.0.1"
from redband.base import BaseConfig, EntrypointConfig, InstantiableConfig
from redband.entrypoint import entrypoint
from redband.instantiate import instantiate
from redband.merge import merge

__all__ = ["__version__", "entrypoint", "instantiate", "merge", "BaseConfig", "EntrypointConfig", "InstantiableConfig"]
