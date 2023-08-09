import sys

from . import main


def main_module():
    # The launcher can't be fixed while running so this main module
    # mostly exists to provide a way to hack the main module.

    if sys.argv[1] == "--fixlauncher":
        from .entrypoint_hack import hack_slow_launcher
        hack_slow_launcher()
    else:
        main()


main_module()
