import enum


@enum.unique
class SpecialKeys(enum.Enum):
    """Special keys in configs used by instantiate."""

    GROUP = "group__"
    NAME = "name__"
    TARGET = "target__"
    PARTIAL = "partial__"
    RECURSIVE = "recursive__"
