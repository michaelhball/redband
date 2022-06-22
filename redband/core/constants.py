import enum
from typing import Any

MISSING: Any = "???"


@enum.unique
class SpecialKeys(enum.Enum):
    """Special keys in configs used by instantiate."""

    TARGET = "_target_"
    PARTIAL = "_partial_"
    RECURSIVE = "_recursive_"
