import argparse
import functools
import inspect
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from redband.base import BaseConfig, EntrypointConfig, is_config_node
from redband.cli import get_args_parser
from redband.library import ConfigLibrary, fill_config_library
from redband.merge import merge, merge_dicts
from redband.typing import ConfigFields, DictStrAny, JSON
from redband import util as rb_util


EntrypointFunc = Callable[[Type[BaseConfig]], Any]
ConfigDict = DictStrAny


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
            yaml_dir = str(_yaml_path)
            if Path.is_file(_yaml_path):
                yaml_name = str(Path(_yaml_path.name).stem)
                yaml_dir = str(_yaml_path.parent)
            break

    return yaml_dir, yaml_name


def _get_yaml_name(entrypoint_yaml_name: Optional[str], cli_yaml_name: Optional[str]) -> Optional[str]:
    """Gets the name of the entrypoint YAML, first considering a command-line override then the argument
    to the @entrypoint decorator
    """
    for yaml_name in [cli_yaml_name, entrypoint_yaml_name]:
        return yaml_name


def _compose_overrides(entrypoint_config_class_fields: ConfigFields, overrides: List[str]) -> DictStrAny:
    """#TODO: docstring + error handling"""
    config_lib: ConfigLibrary = ConfigLibrary()
    config_dict = {}
    for override_str in overrides:
        assert (
            "=" in override_str and override_str.count("=") == 1
        ), "Your command-line overrides must be of the form '<key>=<value>'"

        key, value = override_str.split("=")
        entrypoint_key, *nested_keys = key.split(".")
        config_field = entrypoint_config_class_fields[entrypoint_key]
        config_field_type = config_field.type_

        if len(nested_keys) == 0:
            if is_config_node(config_field_type):
                config_group = config_lib.get_config_group(config_field_type._group())
                value = config_group[value]
            config_dict[entrypoint_key] = value

        else:
            # TODO:
            ...

    return config_dict


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
    entrypoint_config_class_fields: ConfigFields,
    yaml_dir: str,
    yaml_name: Optional[str] = None,
) -> ConfigDict:
    """#TODO: docstring"""

    # if the user didn't specify a YAML, return empty
    if yaml_name is None:
        return {}
    assert yaml_dir is not None, "You cannot compose a config from YAML without passing a `yaml_dir`"

    # find YAML & load —> JSON dict
    valid_yamls = sorted(Path(yaml_dir).glob(f"{yaml_name}.y*ml"))
    assert len(valid_yamls) == 1, "There is more than one matching YAML in your specified `yaml_path`"
    yaml_dict: Dict[str, JSON] = rb_util.load_yaml(str(valid_yamls[0]))

    config_lib: ConfigLibrary = ConfigLibrary()
    config_dict = {}

    # iterate through YAML items, merging each into the `config_dict`
    for key, value in yaml_dict.get("entrypoint").items():
        entrypoint_key, *nested_keys = key.split(".")

        # get information about field in entrypoint config
        config_field = entrypoint_config_class_fields[entrypoint_key]
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
    cli_args: argparse.Namespace,
    entrypoint_func: EntrypointFunc,
    entrypoint_yaml_name: Optional[str] = None,
    entrypoint_yaml_path: Optional[str] = None,
    config_lib_dir: Optional[str] = None,
) -> Type[BaseConfig]:
    """This function
        1) composes an entrypoint config based on a combination of the config classes defined by the user,
            an entrypoint YAML, and any command-line overrides, and
        2) validates the config ensuring that all parameters are valid and none that are required are missing

    Args:
        cli_args: the namespace containing parsed command-line arguments
        entrypoint_func: the callable object that was decorated as a redband entrypoint
        entrypoint_yaml_name:
            optional name of the entrypoint YAML specified as an argument to the entrypoint decorator
        entrypoint_yaml_path:
            optional path to the entrypoint YAML specified as an argument to the entrypoint decorator
        config_lib_dir:
            an optional path to the directory in which the user defined their configs,
            specified as an argument to the entrypoint decorator

    Returns the composed, validated config: an instantiated instance of a BaseConfig subclass
    """

    entrypoint_file_path = inspect.getfile(entrypoint_func)

    # find all user configs & construct the Singleton ConfigLibrary
    fill_config_library(entrypoint_file_path, cli_args.config_lib_dir or config_lib_dir)

    # find the entrypoint config type based on the users type annotation + set 'entrypoint' group
    entrypoint_func_signature = inspect.signature(entrypoint_func)
    assert (
        len(entrypoint_func_signature.parameters) == 1
    ), "Your decorated entrypoint function should expect only a single argument, the resolved config object"
    entrypoint_config_class: Type[BaseConfig] = list(entrypoint_func_signature.parameters.values())[0].annotation
    if not isinstance(entrypoint_config_class, EntrypointConfig):
        entrypoint_config_class._add_fields(group__=(str, "entrypoint"))
    entrypoint_config_class_fields = entrypoint_config_class.__fields__

    # compose overrides into a config_dict
    overrides_config_dict = _compose_overrides(entrypoint_config_class_fields, cli_args.overrides)

    # if we were passed a config, compose that directly (with optional overrides) and return, ignoring other cli_args
    if cli_args.config is not None:
        return merge(entrypoint_config_class.load(cli_args.config), overrides_config_dict)

    # work out entrypoint YAML dir and name &, if necessary, resolve the YAML config
    yaml_name = entrypoint_yaml_name
    yaml_dir, _yaml_name = _get_yaml_dir_and_name(entrypoint_file_path, entrypoint_yaml_path, cli_args.yaml_path)
    yaml_name = yaml_name or _yaml_name or _get_yaml_name(entrypoint_yaml_name, cli_args.yaml_name)
    yaml_config_dict = _compose_yaml(entrypoint_config_class_fields, yaml_dir, yaml_name)

    # merge entrypoint YAML and overrides config dicts with the entrypoint config class, & validate
    config_dict = merge_dicts(yaml_config_dict, overrides_config_dict)
    config_dict = _validate_config_dict(config_dict)
    entrypoint_config = entrypoint_config_class(**config_dict)

    return entrypoint_config


def entrypoint(
    _entrypoint_func: Optional[EntrypointFunc] = None,
    yaml_name: Optional[str] = None,
    yaml_path: Optional[str] = None,
    config_lib_dir: Optional[str] = None,
) -> Callable[[EntrypointFunc], Any]:
    """This decorator adds Redband's core functionality to any Python script. By decorating your entrypoint
    function with with this decorator you specify that said function expects a single argument: the composed
    config of the type defined by your entrypoint config class.

    ```
        class MyEntrypointConfig(redband.EntrypointConfig):
            ...

        @redband.entrypoint(yaml_name="dootdoot")
        def do_main_thing(config: MyEntrypointConfig):
            ...

        if __name__ == "__main__":
            do_main_thing()
    ```

    Your entrypoint function (`do_main_thing`) contains all the domain-specific code that you wish; all Redband does
    is compose and pass it a config object derived from the combination of
        1. predefined config classes (that have been added to the `ConfigLibrary`)
        2. the entrypoint config definition
        3. an optional entrypoint YAML
        4. any command-line overrides

    Args:
        _entrypoint_func: the entrypoint function, non-None if the decorator is used without arugments
        yaml_name:
            the name of an entrypoint YAML file (the filename excluding extension in the same directory as
            the entrypoint script)
        yaml_path:
            the path to an entrypoint YAML from which to load default config values (this supercedes
            `yaml_name` as the full path must include a name).
        config_lib_dir:
            the directory in which your config classes are defined. This can also be handled via setting
            the 'RB_CONFIG_LIB_DIR' environment variable or using the `--config-lib-dir` command-line option
    """

    # validate that arguments are formatted correctly
    assert yaml_name is None or (
        "." not in yaml_name and "/" not in yaml_name
    ), "Your 'yaml_name' must be the file name of your entrypoint YAML, excluding the suffix"
    assert yaml_path is None or rb_util.file_exists(
        yaml_path
    ), "Your `yaml_path` must be that path to a file that exists"
    assert config_lib_dir is None or (
        rb_util._is_local_path(config_lib_dir) and rb_util.file_exists(config_lib_dir)
    ), "If you pass a `config_lib_dir` it must be the path to a local _directory_ that exists"
    assert (
        yaml_path is None or yaml_name is None
    ), "You cannot specify both a `yaml_name` and a `yaml_path` (the latter supercedes the former)"

    def entrypoint_decorator(entrypoint_func: EntrypointFunc) -> Callable[[], None]:
        @functools.wraps(entrypoint_func)
        def decorated_entrypoint(config_passthrough: Optional[BaseConfig] = None) -> Any:
            if config_passthrough is not None:
                config = config_passthrough
            else:
                # compose a config object from the entrypoint_config_type base class, the entrypoint
                # YAML, and any command-line overrides
                cli_args = get_args_parser().parse_args()
                config = _compose(
                    cli_args,
                    entrypoint_func=entrypoint_func,
                    entrypoint_yaml_name=yaml_name,
                    entrypoint_yaml_path=yaml_path,
                    config_lib_dir=config_lib_dir,
                )

            if cli_args.show:
                print(config.yaml())
            else:
                entrypoint_func(config)

        return decorated_entrypoint

    return entrypoint_decorator if _entrypoint_func is None else entrypoint_decorator(_entrypoint_func)
