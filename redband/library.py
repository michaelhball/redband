import importlib
import pkgutil
from typing import Dict, List, Optional, Type, Union

from redband.base import BaseConfig, REDBAND_CONFIG_CLASSES


class Singleton(type):
    def __init__(cls, name, bases, dict) -> "Singleton":
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance


ConfigTypeOrSubclass = Type[BaseConfig]
ConfigGroup = Dict[str, Union[Type[BaseConfig], "ConfigGroup"]]
ConfigTypeOrList = Union[ConfigTypeOrSubclass, List[ConfigTypeOrSubclass]]


class ConfigLibrary(object, metaclass=Singleton):
    """A Singleton class object that represents a complete collection available to the user.
    Configs should be registered to the ConfigLibrary once, on startup, and can then be
    accessed from anywhere within that execution.
    """

    configs: Dict[str, ConfigGroup] = {}

    def add(self, config: ConfigTypeOrList):
        """#TODO: docstring"""

        _cur_config_group = self.configs
        for g in config._group().split("."):
            if g not in _cur_config_group:
                _cur_config_group[g] = {}
            _cur_config_group = _cur_config_group[g]
        _cur_config_group[config._name()] = config

    def get_config_group(self, group: str) -> ConfigGroup:
        """Returns a dict of the configs that have been added to the library
        under the given group.

        Args:
            group: a group name, can use dot syntax (e.g. "model.optimizer")
        """
        _cur_config_group = self.configs
        for g in group.split("."):
            _cur_config_group = _cur_config_group[g]
        return _cur_config_group


def _add_config_to_library(config: Type[BaseConfig], config_lib: ConfigLibrary):
    """#TODO: docstring + add better exception handling."""
    for config_subclass in config.__subclasses__():
        _add_config_to_library(config_subclass, config_lib)
    if config not in REDBAND_CONFIG_CLASSES:
        config_lib.add(config)


def fill_config_library(entrypoint_file_path: str, config_lib_dir: Optional[str] = None) -> None:
    """Fills the ConfigLibrary singleton with all the configs defined in either the given config directory
    (if one is passed via an environment variable, the command-line, or in the entrypoint arguments) or
    from within the entrypoint file.
    """
    config_lib_path = config_lib_dir if config_lib_dir is not None else entrypoint_file_path
    for _, name, _ in pkgutil.iter_modules([config_lib_path]):
        importlib.import_module(f"{config_lib_dir.replace('/', '.')}.{name}")
    config_lib = ConfigLibrary()
    _add_config_to_library(BaseConfig, config_lib)
