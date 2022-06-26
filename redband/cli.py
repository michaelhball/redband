import argparse
import os


def get_args_parser() -> argparse.ArgumentParser:
    """Returns the redband argparse command-line parser.

    This implementation was taken almost directly from https://github.com/facebookresearch/hydra.
    """
    from . import __version__

    parser = argparse.ArgumentParser(add_help=False, description="RedBand")
    parser.add_argument("--help", "-h", action="store_true", help="Application's help")
    parser.add_argument("--redband-help", action="store_true", help="RedBand's help")
    parser.add_argument(
        "--version",
        action="version",
        help="Show RedBand's version and exit",
        version=f"RedBand {__version__}",
    )
    parser.add_argument(
        "overrides",
        nargs="*",
        help="Any key=value arguments to override config values (use dots for.nested=overrides)",
    )

    parser.add_argument(
        "--show",
        "-s",
        action="store_true",
        help="Display config instead of running entrypoint",
    )

    parser.add_argument(
        "--yaml-path",
        "-yp",
        help=(
            "Overrides the `yaml_path` specified in redband.entrypoint(). "
            "The `yaml_path` can be either the absolute or relative path to the `.py` file "
            "containing @redband.entrypoint()"
        ),
    )

    parser.add_argument(
        "--yaml-name",
        "-yn",
        help="Overrides the `yaml_name` specified in @redband.entrypoint()",
    )

    parser.add_argument(
        "--config-lib-dir",
        "-cld",
        help="A directory in which to look for user-defined configs s.t. they can be added to the `ConfigLibrary`",
        default=os.getenv("RB_CONFIG_LIB_DIR"),
    )

    parser.add_argument(
        "--config",
        "-c",
        help=(
            "Runs the entrypoint with a serialized config object, bypassing all config composition "
            "(all other command-line arguments are ignored)"
        ),
    )

    return parser
