import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type

from redband.base import BaseConfig
from redband.cli import get_args_parser
from redband.merge import merge


EntrypointFunc = Callable[[Type[BaseConfig]], Any]


def _compose_overrides(overrides: List[str]) -> Dict[str, Any]:
    pass


def _compose(
    cli_args: Any,  # TODO: add proper annotation
    entrypoint_config_type: Type[BaseConfig],
    entrypoint_config_name: Optional[str] = None,
    entrypoint_config_path: Optional[str] = None,
) -> Type[BaseConfig]:
    """TODO:docstring"""

    # TODO: instantiate this (=> getting defaults from code), then merge with YAML, then merge with overrides
    # TODO: might have to use partial or something, else we'll get validation errors when we instantiate it like this
    # OR: instead construct the YAML / overrides stuff as a dict that we can instantiate this backing class with
    entrypoint_config = entrypoint_config_type()

    # TODO: blend with

    # overrides = _compose_overrides(cli_args.overrides)
    # if cli_args.config is not None:
    #     # TODO: use the correct config class (i.e. the one specified in the YAML)
    #     config = merge(BaseConfig.from_pickle(cli_args.config), overrides)

    return


def entrypoint(
    config_path: Optional[str] = None,
    config_name: Optional[str] = None,
) -> Callable[[EntrypointFunc], Any]:
    def entrypoint_decorator(entrypoint_func: EntrypointFunc) -> Callable[[], None]:
        """TODO: docstring"""

        @functools.wraps(entrypoint_func)
        def decorated_entrypoint(config_passthrough: Optional[BaseConfig] = None) -> Any:
            if config_passthrough is not None:
                config = config_passthrough
            else:
                # find the entrypoint config type based on the users type annotation
                entrypoint_func_signature = inspect.signature(entrypoint_func)
                assert len(entrypoint_func_signature.parameters) == 1
                config_type = list(entrypoint_func_signature.parameters.values())[0].annotation

                # compose a config object from the entrypoint_config_type base class, the entrypoint
                # YAML, and any command-line overrides
                args_parser = get_args_parser()
                config = _compose(
                    args_parser.parse_args(),
                    entrypoint_config_type=config_type,
                    entrypoint_config_name=config_name,
                    entrypoint_config_path=config_path,
                )

            entrypoint_func(config)

        return decorated_entrypoint

    return entrypoint_decorator
