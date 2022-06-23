import importlib
import pkgutil
from typing import Dict, List, Type, Union

from redband.base import BaseConfig, _REDBAND_CONFIG_CLASSES


class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance


ConfigTypeOrSubclass = Type[BaseConfig]
ConfigGroup = Dict[str, Union[Type[BaseConfig], "ConfigGroup"]]
ConfigTypeOrList = Union[ConfigTypeOrSubclass, List[ConfigTypeOrSubclass]]


class ConfigLibrary(object):
    __metaclass__ = Singleton

    configs: Dict[str, ConfigGroup] = {}

    def add(self, config: ConfigTypeOrList):
        """#TODO: docstring"""

        _cur_config_group = self.configs
        for g in config.group().split("."):
            if g not in _cur_config_group:
                _cur_config_group[g] = {}
            _cur_config_group = _cur_config_group[g]
        _cur_config_group[config.name()] = config


def _add_config_to_library(config: Type[BaseConfig], config_lib: ConfigLibrary):
    """#TODO: docstring + add better exception handling."""
    for config_subclass in config.__subclasses__():
        _add_config_to_library(config_subclass, config_lib)
    if config not in _REDBAND_CONFIG_CLASSES:
        config_lib.add(config)


def fill_config_library(config_lib_dir: str):
    """#TODO: docstring"""
    for _, name, _ in pkgutil.iter_modules([config_lib_dir]):
        importlib.import_module(f"{config_lib_dir.replace('/', '.')}.{name}")
    config_lib = ConfigLibrary()
    _add_config_to_library(BaseConfig, config_lib)
