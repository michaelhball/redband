import functools
import inspect
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from redband.base import BaseConfig, is_config_node
from redband.cli import get_args_parser
from redband.library import ConfigLibrary, fill_config_library
from redband.merge import merge
from redband.typing import DictStrAny, JSON
from redband.util import load_yaml


EntrypointFunc = Callable[[Type[BaseConfig]], Any]
ConfigDict = DictStrAny  # TODO: make annotation better


class ConfigCompositionException(Exception):
    ...


def _get_task_name(entrypoint_file_path: str) -> str:
    """Derives a name for the job based on the entrypoint file."""
    entrypoint_file_name = Path(entrypoint_file_path).name
    entrypoint_file_stem = Path(entrypoint_file_name).stem
    entrypoint_file_stem = str(entrypoint_file_stem).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", entrypoint_file_stem)


def _get_yaml_dir_and_name(
    entrypoint_file_path: str,
    entrypoint_yaml_path: Optional[str] = None,
    cli_yaml_path: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Derives the directory (and possible the name) of the entrypoint YAML from multiple sources
    (arguments to the entrypoint decorator and command-line overrides). NB: the presence of a valid
    command-line override will, obviously, override the @entrypoint argument specified in code.
    """

    yaml_name = None
    yaml_dir = Path(entrypoint_file_path).parent

    for yaml_path in [cli_yaml_path, entrypoint_yaml_path]:
        if yaml_path is not None:
            _yaml_path = Path(yaml_path)
            if not Path.is_absolute(_yaml_path):
                _yaml_path = yaml_dir / _yaml_path
            yaml_dir = _yaml_path
            if Path.is_file(_yaml_path):
                yaml_name = Path(_yaml_path.name).stem
                yaml_dir = _yaml_path.parent
            break

    return str(yaml_dir), str(yaml_name)


def _get_yaml_name(entrypoint_yaml_name: Optional[str], cli_yaml_name: Optional[str]) -> Optional[str]:
    """Gets the name of the entrypoint YAML, first considering a command-line override then the argument
    to the @entrypoint decorator
    """
    for yaml_name in [cli_yaml_name, entrypoint_yaml_name]:
        return yaml_name


def _compose_overrides(overrides: List[str]) -> DictStrAny:
    """#TODO: docstring"""
    return {}


def _validate_config_dict(node: Union[Any, Type[BaseConfig], ConfigDict]) -> ConfigDict:
    """TODO: docstring + get rid of Any in annotation (I need something)"""

    # instantiate config nodes to trigger validation
    if is_config_node(node):
        return node()

    # if we have a dict then recursively validate all children
    elif isinstance(node, dict):
        return {key: _validate_config_dict(value) for key, value in node.items()}

    # otherwise we have a 'vanilla' parameter => return
    else:
        return node


def _compose_yaml(
    entrypoint_config_class: Type[BaseConfig], yaml_dir: str, yaml_name: Optional[str] = None
) -> ConfigDict:
    """#TODO: docstring"""

    # if the user didn't specify a YAML, return empty
    if yaml_name is None:
        return {}
    assert yaml_dir is not None, "You cannot compose a config from YAML without passing a `yaml_dir`"

    # find YAML & load —> JSON dict
    valid_yamls = sorted(Path(yaml_dir).glob(f"{yaml_name}.y*ml"))
    assert len(valid_yamls) == 1, "There is more than one matching YAML in your specified `yaml_path`"
    yaml_dict: Dict[str, JSON] = load_yaml(str(valid_yamls[0]))

    config_lib = ConfigLibrary()
    config_dict = {}

    # iterate through YAML items, merging each into the `config_dict`
    for key, value in yaml_dict.get("entrypoint").items():
        entrypoint_key, *nested_keys = key.split(".")

        # get information about field in entrypoint config
        config_field = entrypoint_config_class.__fields__[entrypoint_key]
        config_field_type = config_field.type_

        # adding of a single parameter, either a config or parameter node
        if len(nested_keys) == 0:
            if is_config_node(config_field_type):
                config_group = config_lib.get_config_group(config_field_type._group())
                value = config_group[value]
            config_dict[entrypoint_key] = value

        # TODO: this is hard because if we're going deeper within configs we need to mutate in place
        elif entrypoint_key in config_dict:
            ...

        #
        else:
            raise ConfigCompositionException("")  # TODO: come up with a nice error structure

    return config_dict


def _compose(
    cli_args: Any,  # TODO: add proper annotation
    entrypoint_func: EntrypointFunc,
    entrypoint_yaml_name: Optional[str] = None,
    entrypoint_yaml_path: Optional[str] = None,
    config_lib_dir: Optional[str] = None,
) -> Type[BaseConfig]:
    """TODO:docstring"""

    # TODO: validate that the yaml_name and yaml_path arguments are formatted correctly

    # find the entrypoint config type based on the users type annotation + set 'entrypoint' group
    entrypoint_func_signature = inspect.signature(entrypoint_func)
    assert len(entrypoint_func_signature.parameters) == 1
    entrypoint_config_class: Type[BaseConfig] = list(entrypoint_func_signature.parameters.values())[0].annotation
    entrypoint_config_class._add_fields(group__=(str, "entrypoint"))

    # compose overrides into an override dict
    overrides = _compose_overrides(cli_args.overrides)

    # if we were passed a config, compose that directly (with optional overrides) and return, ignoring other cli_args
    if cli_args.config is not None:
        return merge(entrypoint_config_class.from_pickle(cli_args.config), overrides)

    entrypoint_file_path = inspect.getfile(entrypoint_func)
    task_name = _get_task_name(entrypoint_file_path)

    # find all user configs & construct the Singleton ConfigLibrary
    fill_config_library(entrypoint_file_path, cli_args.config_lib_dir or config_lib_dir)
    assert False

    # get entrypoint YAML dir and name, & if necessary resolve the YAML config
    yaml_name = entrypoint_yaml_name
    yaml_dir, _yaml_name = _get_yaml_dir_and_name(entrypoint_file_path, entrypoint_yaml_path, cli_args.yaml_path)
    yaml_name = yaml_name or _yaml_name or _get_yaml_name(entrypoint_yaml_name, cli_args.yaml_name)

    # compose YAML, merge with overrides, & validate
    yaml_config_dict = _compose_yaml(entrypoint_config_class, yaml_dir, yaml_name)
    config_dict = yaml_config_dict  # TODO: merge with overrides here
    config_dict = _validate_config_dict(config_dict)

    # merge YAML + overrides with entrypoint config class, & validate
    # TODO: should I use .merge()? Do I even need a .merge() function?
    entrypoint_config = entrypoint_config_class(**config_dict)

    return entrypoint_config


def entrypoint(
    yaml_name: Optional[str] = None,
    yaml_path: Optional[str] = None,
    config_lib_dir: Optional[str] = None,
) -> Callable[[EntrypointFunc], Any]:
    """#TODO: docstring"""

    # TODO: enable this to work with or without arguments (e.g. if user doesn't need to specify anything)

    def entrypoint_decorator(entrypoint_func: EntrypointFunc) -> Callable[[], None]:
        """TODO: docstring"""

        @functools.wraps(entrypoint_func)
        def decorated_entrypoint(config_passthrough: Optional[BaseConfig] = None) -> Any:
            if config_passthrough is not None:
                config = config_passthrough
            else:
                # compose a config object from the entrypoint_config_type base class, the entrypoint
                # YAML, and any command-line overrides
                args_parser = get_args_parser()
                config = _compose(
                    args_parser.parse_args(),
                    entrypoint_func=entrypoint_func,
                    entrypoint_yaml_name=yaml_name,
                    entrypoint_yaml_path=yaml_path,
                    config_lib_dir=config_lib_dir,
                )

            entrypoint_func(config)

        return decorated_entrypoint

    return entrypoint_decorator
