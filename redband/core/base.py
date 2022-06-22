from _collections_abc import dict_keys
from typing import Any, List, Type

from pydantic import BaseModel

from redband.core.constants import MISSING


class BaseConfig(BaseModel):
    """The base config class that all configs extend."""

    # TODO: add save, load methods
    # TODO: document why we need this even here, for non-instantiable configs
    _recursive_: bool = True

    def __getitem__(self, attr_name: str) -> Any:
        return getattr(self, attr_name)

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


class MyConfig(BaseConfig):
    doot: str = "skoot"
    skoot: int


class MyChildConfig(MyConfig):
    doot = "poot"


if __name__ == "__main__":

    my_config = MyChildConfig(skoot=5)
    print(my_config.keys())
    print(type(my_config.keys()))
    # print(type(my_config.skoot))

    # print(my_config.pop("doot"))
    # print(my_config)

    # new_config = MyConfig()
    # print(new_config)
