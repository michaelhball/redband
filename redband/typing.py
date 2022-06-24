from typing import Any, Dict, List, Mapping, Union

DictStrAny = Dict[str, Any]
JSON = Union[str, int, float, bool, None, Mapping[str, "JSON"], List["JSON"]]
