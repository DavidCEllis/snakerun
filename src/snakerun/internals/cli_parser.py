import argparse


def make_parser():
    parser = argparse.ArgumentParser(
        description="Launch single file python scripts that use PEP-722 style dependency lists.",
    )

    parser.add_argument("filename")
    parser.add_argument("--fixlauncher")
    parser.add_argument("--clear-cache")

    return parser
