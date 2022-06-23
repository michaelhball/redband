import enum
from typing import Any, List, Mapping, Union

MISSING: Any = "???"

JSON = Union[str, int, float, bool, None, Mapping[str, 'JSON'], List['JSON']]


@enum.unique
class SpecialKeys(enum.Enum):
    """Special keys in configs used by instantiate."""

    TARGET = "target__"
    PARTIAL = "partial__"
    RECURSIVE = "recursive__"
