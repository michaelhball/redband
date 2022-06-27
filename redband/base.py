import inspect
from _collections_abc import dict_keys
from typing import AbstractSet, Any, Dict, List, Mapping, Optional, Union

from pydantic.error_wrappers import ValidationError
from pydantic.fields import ModelField
from pydantic_yaml import YamlModel as BaseModel
from redband.typing import DictStrAny

from redband.util import load_yaml, save_yaml


class BaseConfig(BaseModel):
    """The base config class that all configs extend."""

    # name of the config group this config is a part of
    group__: str

    # optional name of this config (that will override the __class__ name if specified)
    name__: Optional[str]

    # whether or not redband.instantiate should recursively instantiate sub-configs of this
    # config (even though this config may not be `Instantiable`, setting `recursive__` here
    # can control the recursion through this config to its potentially instantiable children)
    recursive__: bool = True

    @classmethod
    def _add_fields(cls, **field_definitions: Any) -> None:
        """Adds any number of fields to a `BaseConfig` class definition, inplace. Used e.g. to
        automatically set `group__="entrypoint"` for entrypoint configs.
        Taken from https://github.com/samuelcolvin/pydantic/issues/1937#issuecomment-695313040
        """
        new_fields: Dict[str, ModelField] = {}
        new_annotations: Dict[str, Optional[type]] = {}

        for f_name, f_def in field_definitions.items():
            if isinstance(f_def, tuple):
                try:
                    f_annotation, f_value = f_def
                except ValueError as e:
                    raise Exception(
                        "field definitions should either be a tuple of (<type>, <default>) or a default "
                        "value alone. Therefore, this method doesn't yet support tuples as default values"
                    ) from e
            else:
                f_annotation, f_value = None, f_def

            if f_annotation:
                new_annotations[f_name] = f_annotation

            new_fields[f_name] = ModelField.infer(
                name=f_name, value=f_value, annotation=f_annotation, class_validators=None, config=cls.__config__
            )

        cls.__fields__.update(new_fields)
        cls.__annotations__.update(new_annotations)

    @classmethod
    def _get_param(cls, param: str) -> str:
        return cls.__fields__[param].get_default()

    @classmethod
    def _set_param(cls, param_name: str, value: Any) -> None:
        """"""

        # TODO: if the param is a BaseConfig then value should NOT be a dict, it should be that config class type

        old_field = cls.__fields__[param_name]
        new_field = ModelField.infer(
            name=param_name,
            value=value,
            annotation=old_field.type_,
            class_validators=None,
            config=cls.__config__,
        )

        # validate override that created the new field
        _, error_ = new_field.validate(value, {}, loc=param_name)
        if error_:
            raise ValidationError([error_], cls)

        cls.__fields__[param_name] = new_field

    @classmethod
    def _group(cls) -> str:
        return cls._get_param("group__")

    @classmethod
    def _name(cls) -> str:
        return cls._get_param("name__") or cls.__name__

    @classmethod
    def _to_config_dict(cls) -> DictStrAny:
        """Converts config to a dict representation."""
        config_dict = {}
        for k, v in cls.__fields__.items():
            config_dict[k] = v.get_default()
        return config_dict

    def __getitem__(self, attr_name: str) -> Any:
        return getattr(self, attr_name)

    @property
    def keys(self) -> dict_keys:
        return self.dict().keys()

    def pop(self, attr_name: str) -> Any:
        """Pops a parameter from this config instance."""
        attr_value = self[attr_name]
        delattr(self, attr_name)
        return attr_value

    def yaml(self, sort_keys: bool = False) -> str:
        """Returns a YAML dump of this config, optionally sorting keys alphabetically."""
        # TODO: expressiveness
        return super().yaml(exclude={"recursive__", "partial__"})

    @classmethod
    def load(cls, file_path: str) -> "BaseConfig":
        return cls(**load_yaml(file_path))

    def save(self, file_path: str, exclude: Union[AbstractSet[str], Mapping[str, Any]] = None) -> None:
        """Serialize this config object as a YAML. Refer to `super().dict()` for argument details."""
        save_yaml(self.dict(exclude=exclude), file_path)


class InstantiableConfig(BaseConfig):
    """The base config class for all configs that instantiate a class or callable."""

    target__: str
    partial__: bool = False

    # TODO: add `instantiate` method


# TODO: but I still think I need to handle the case where the user doesn't use this (e.g. at serialization time)
class EntrypointConfig(BaseConfig):
    group__: str = "entrypoint"


class ListConfig(List[BaseConfig]):
    ...


REDBAND_CONFIG_CLASSES = {BaseConfig, InstantiableConfig, EntrypointConfig}


def is_config_node(node: Any) -> bool:
    return inspect.isclass(node) and (isinstance(node, BaseConfig) or issubclass(node, BaseConfig))


def is_instantiable_node(node: Any) -> bool:
    return inspect.isclass(node) and (isinstance(node, InstantiableConfig) or issubclass(node, InstantiableConfig))


def is_target_node(node: Any) -> bool:
    return is_dict_config(node) and "target__" in node


def is_dict_config(node: Any) -> bool:
    return is_config_node(node)


def is_list_config(node: Any) -> bool:
    return isinstance(node, ListConfig)
