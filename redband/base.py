from _collections_abc import dict_keys
import yaml
from typing import Any, List, Type

from pydantic import BaseModel

from redband.constants import MISSING
from redband.util import load_pickle


class BaseConfig(BaseModel):
    """The base config class that all configs extend."""

    # TODO: add save, load methods
    # TODO: document why we need this even here, for non-instantiable configs
    _recursive_: bool = True

    def __getitem__(self, attr_name: str) -> Any:
        return getattr(self, attr_name)

    # TODO: add set item function here

    # TODO: add copy function here

    @property
    def name(self) -> str:
        return type(self).__name__

    @property
    def keys(self) -> dict_keys:
        return self.dict().keys()

    def pop(self, attr_name: str) -> Any:
        """TODO: documentation"""
        attr_value = self[attr_name]
        delattr(self, attr_name)
        return attr_value

    def key_is_missing(self, key: str) -> bool:
        """TODO: documentation"""
        return is_missing(self[key])

    def to_yaml(self, sort_keys: bool = False) -> str:
        """Returns a YAML dump of this config, optionally sorting keys alphabetically."""
        # TODO: test this for more complex data types
        # TODO: add ability to include config names in the YAML (i.e. not only resolved values)
        return yaml.dump(
            self.dict(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=sort_keys,
        )

    @classmethod
    def from_pickle(cls, file_path: str) -> "BaseConfig":
        """#TODO: docstring"""
        # TODO: is this the best way to validate that the typing is correct? Can I explicitly merge it somehow to make sure?
        _loaded = load_pickle(file_path)
        assert isinstance(_loaded, cls), f"The `file_path` you are loading from must contain a {cls.__name__} instance"
        return _loaded

    def to_pickle(self, file_path: str):
        pass


class InstantiableConfig(BaseConfig):
    """The base config class for all configs that instantiate a class or callable."""

    _target_: str
    _partial_: bool = False

    # TODO: add `instantiate` method (might be hard to avoid circular imports)


class ListConfig(List[Type[BaseConfig]]):
    ...


def is_config_node(node: Any) -> bool:
    return isinstance(node, BaseConfig)


def is_instantiable_node(node: Any) -> bool:
    return isinstance(node, InstantiableConfig)


def is_target_node(node: Any) -> bool:
    return is_dict_config(node) and "_target_" in node


def is_dict_config(node: Any) -> bool:
    return isinstance(node, BaseConfig) or issubclass(node, InstantiableConfig)


def is_list_config(node: Any) -> bool:
    return isinstance(node, ListConfig)


def is_missing(value: Any) -> bool:
    return isinstance(value, str) and value == MISSING
