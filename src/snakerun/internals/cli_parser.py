import argparse


def make_parser():
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description="Launch single file python scripts that use PEP-722 style dependency lists.",
    )

    subparsers = parser.add_subparsers(dest="subparser_name")
    main_command = subparsers.add_parser("launch", help="Execute python script with required dependencies.")
    main_command.add_argument("filename")
    main_command.add_argument("--quiet", action="store_true", help="Suppress stdout messages from snakerun.")

    settings = subparsers.add_parser("settings", help="Modify tool settings.")
    settings.add_argument("--cache-size", help="Set the maximum number of temporarily cached environments.")

    launcher_fix = subparsers.add_parser("fixlauncher", help="Patch the launch script to remove 're' usage.")
    cache_clearer = subparsers.add_parser("clear-cache", help="Clear all temporary caches.")

    cache_clearer.add_argument("--all-caches", action="store_true", help="Also clear permanent caches.")

    return parser
