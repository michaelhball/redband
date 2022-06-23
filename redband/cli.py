import argparse


def get_args_parser() -> argparse.ArgumentParser:
    from . import __version__

    # TODO: Can I use CLICK here instead of ArgumentParser ??

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
            "The `yaml_path` can either be absolute or relative to the `.py` file containing @redband.entrypoint()"
        ),
    )

    parser.add_argument(
        "--yaml-name",
        "-yn",
        help="Overrides the `yaml_name` specified in @redband.entrypoint()",
    )

    parser.add_argument(
        "--config-dir",
        "-cd",
        help="Adds an additional config dir to the config search path",
    )

    parser.add_argument(
        "--config",
        "-c",
        help=(
            "Runs the entrypoint with a serialized config object, bypassing all config composition "
            "(all other command-line arguments are ignored)"
        ),
    )

    # TODO: add this back later
    # parser.add_argument(
    #     "--multirun",
    #     "-m",
    #     action="store_true",
    #     help="Run multiple jobs with the configured launcher and sweeper",
    # )

    return parser
