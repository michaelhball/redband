import functools
import importlib
from typing import Any, Callable, Optional, Union
from redband import base as rb_base

from redband.constants import SpecialKeys
from redband.merge import merge


class InstantiationException(Exception):
    ...


Target = Union[type, Callable[..., Any]]


def _convert_target_to_string(target: Target) -> str:
    """Convert instantiated target —> its string representation (for error logging)."""
    return f"{target.__module__}.{target.__qualname__}" if callable(target) else target


def _resolve_target(target_str: str, full_key: Optional[str] = None) -> Target:
    """Resolve target string into class object or callable."""
    try:
        modname, classname = target_str.rsplit(".", 1)
        mod = importlib.import_module(modname)
        target = getattr(mod, classname)
    except Exception as e:
        error_message = f"Error locating target '{target}', see chained exception above."
        if full_key is not None:
            error_message += f"\nfull_key: {full_key}"
        raise InstantiationException(error_message) from e
    return target


def instantiate(config: rb_base.InstantiableConfig, *args: Any, **kwargs: Any) -> Any:
    """TODO: documentation"""

    if config is None or not isinstance(config, rb_base.InstantiableConfig):
        return config

    # TODO: do I want this function to handle config instances or instantiated configs ?
    # TODO: I guess _either_ would be useful, but for now I will assume instances

    # merge any additional kwargs with the input config
    if kwargs:
        config = merge(config, kwargs)

    recursive__ = config.pop(SpecialKeys.RECURSIVE)
    partial__ = config.pop(SpecialKeys.PARTIAL)

    return _instantiate_node(config, *args, recursive=recursive__, partial=partial__)


def _instantiate_node(
    node: Any,
    *args: Any,
    recursive: bool = False,
    partial: bool = False,
) -> Any:
    """TODO: documentation"""
    # TODO: do I need to check for subclasses too ??
    if not not isinstance(node, rb_base.BaseConfig) and not isinstance(node, rb_base.ListConfig):
        return node

    recursive__ = node[SpecialKeys.RECURSIVE] if SpecialKeys.RECURSIVE in node else recursive
    partial__ = node[SpecialKeys.PARTIAL] if SpecialKeys.PARTIAL in node else partial

    # TODO: some function to use for logging (i.e. the full path to this node if we run into an error at this step)
    # full_key = node._get_full_key()
    full_key = None

    exclude_keys = {sk.value for sk in SpecialKeys}

    # if dealing with a list of configs then instantiate recursively instantiate each config in the list
    if rb_base.is_list_config(node):
        return [_instantiate_node(item, recursive=recursive__) for item in node]

    # if dealing with a regular config, optionally recursively instantiate on each key
    elif rb_base.is_dict_config(node):
        if rb_base.is_target_node(node):
            kwargs = {}
            for key in node.keys():
                if key not in exclude_keys:
                    value = node[key]
                    if recursive__:
                        value = _instantiate_node(value, recursive=recursive__)
                    kwargs[key] = value

            target__ = _resolve_target(node[SpecialKeys.TARGET], full_key=full_key)
            return _call_target(target__, partial__, *args, full_key=full_key, **kwargs)

        else:
            instantiated_node = node.copy()
            for key in node.keys():
                if key not in exclude_keys and recursive__:
                    instantiated_node[key] = _instantiate_node(node[key], recursive=recursive__)
            return instantiated_node

    # we should never get here, the exit conditions for non-config nodes are defined above
    else:
        raise InstantiationException(f"Unexpected config type : {node.name}")


def _call_target(
    target__: Target,
    partial__: bool,
    *args: Any,
    full_key: Optional[str] = None,
    **kwargs: Any,
):
    """Call target (type) with args and kwargs."""
    if partial__:
        try:
            return functools.partial(target__, *args, **kwargs)
        except Exception as e:
            error_message = f"Error in creating partial({_convert_target_to_string(target__)}, ...) object:\n{repr(e)}"
            if full_key is not None:
                error_message += f"\nfull_key: {full_key}"
            raise InstantiationException(error_message) from e
    else:
        try:
            return target__(*args, **kwargs)
        except Exception as e:
            error_message = f"Error in call to target '{_convert_target_to_string(target__)}':\n{repr(e)}"
            if full_key:
                error_message += f"\nfull_key: {full_key}"
            raise InstantiationException(error_message) from e
