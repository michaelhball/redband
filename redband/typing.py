from typing import Any, Dict, List, Mapping, Union

from pydantic.fields import ModelField

DictStrAny = Dict[str, Any]
JSON = Union[str, int, float, bool, None, Mapping[str, "JSON"], List["JSON"]]
ConfigFields = Dict[str, ModelField]
