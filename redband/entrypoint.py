import functools
import inspect
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from redband.base import BaseConfig
from redband.cli import get_args_parser
from redband.merge import merge


EntrypointFunc = Callable[[Type[BaseConfig]], Any]


def _get_task_name(entrypoint_file_path: str) -> str:
    """Derives a name for the job based on the entrypoint file."""
    entrypoint_file_name = Path(entrypoint_file_path).name
    entrypoint_file_stem = Path(entrypoint_file_name).stem
    entrypoint_file_stem = str(entrypoint_file_stem).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", entrypoint_file_stem)


def _get_yaml_dir_and_name(entrypoint_file_path: str, entrypoint_yaml_path: Optional[str] = None, cli_yaml_path: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """#TODO: docstring"""
    
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
    """#TODO: docstring"""
    for yaml_name in [cli_yaml_name, entrypoint_yaml_name]:
        return yaml_name


def _compose_overrides(overrides: List[str]) -> Dict[str, Any]:
    return {}


def _compose_yaml_config(yaml_dir: str, yaml_name: Optional[str] = None) -> Dict[str, Any]:
    """#TODO: docstring"""
    if yaml_name is None:
        return {}
    assert yaml_dir is not None, "You cannot compose a config from YAML without passing a `yaml_dir`"


def _compose(
    cli_args: Any,  # TODO: add proper annotation
    entrypoint_func: EntrypointFunc,
    entrypoint_yaml_name: Optional[str] = None,
    entrypoint_yaml_path: Optional[str] = None,
) -> Type[BaseConfig]:
    """TODO:docstring"""

    # TODO: validate that the yaml_name and yaml_path arguments are formatted correctly

    # find the entrypoint config type based on the users type annotation
    entrypoint_func_signature = inspect.signature(entrypoint_func)
    assert len(entrypoint_func_signature.parameters) == 1
    entrypoint_config_type: Type[BaseConfig] = list(entrypoint_func_signature.parameters.values())[0].annotation

    # compose overrides into an override dict
    overrides = _compose_overrides(cli_args.overrides)

    # if we were passed a config, compose that directly (with optional overrides) and return, ignoring other cli_args
    if cli_args.config is not None:
        return merge(entrypoint_config_type.from_pickle(cli_args.config), overrides)

    entrypoint_file_path = inspect.getfile(entrypoint_func)
    task_name = _get_task_name(entrypoint_file_path)

    # get entrypoint YAML dir and name, & if necessary resolve the YAML config
    yaml_dir, yaml_name = _get_yaml_dir_and_name(entrypoint_file_path, entrypoint_yaml_path, cli_args.yaml_path)
    if yaml_name is None:
        yaml_name = _get_yaml_name(entrypoint_yaml_name, cli_args.yaml_name)
    yaml_config = _compose_yaml_config(yaml_dir, yaml_name)

    # TODO: instantiate this (=> getting defaults from code), then merge with YAML, then merge with overrides
    # TODO: might have to use partial or something, else we'll get validation errors when we instantiate it like this
    # OR: instead construct the YAML / overrides stuff as a dict that we can instantiate this backing class with
    entrypoint_config = entrypoint_config_type()

    # compose YAML
    
    # compose overrides & merge

    # merge everything with the entrypoint_config_type

    # overrides = _compose_overrides(cli_args.overrides)
    # if cli_args.config is not None:
    #     # TODO: use the correct config class (i.e. the one specified in the YAML)
    #     config = merge(BaseConfig.from_pickle(cli_args.config), overrides)

    return


def entrypoint(
    yaml_name: Optional[str] = None,
    yaml_path: Optional[str] = None,
) -> Callable[[EntrypointFunc], Any]:
    """#TODO: docstring"""

    def entrypoint_decorator(entrypoint_func: EntrypointFunc) -> Callable[[], None]:
        """TODO: docstring"""

        # TODO: enable this to work with or without arguments (e.g. if user doesn't need to specify anything)

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
                )

            entrypoint_func(config)

        return decorated_entrypoint

    return entrypoint_decorator
