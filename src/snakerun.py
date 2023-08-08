"""
SnakeRun

Parse a meaningful comment form to get the requirements for a python script.
Check the Python Version matches a minimum requirement.
Check for cached environments that match and use those if available.
Otherwise make a new venv and install the requirements.
Launch the script in that environment.

The cache is decided by the text of the requirements in the script and *not*
the contents of the environment or the script itself. This is so multiple
scripts with exactly the same dependencies can reuse the same venv.

If a version of a dependency is specified then only environments created
with that exact specification will match (eg: 'requests>2.28' won't reuse
an environment created with 'requests' even if the actual version installed
satisfies the requirement). This is purely to make the comparison as simple
and fast as possible in the 'good' case where the dependencies match.

If pyenv is installed and a pyenv environment is available that satisfies
the python version specification, that version will be used to generate
the virtualenv.

Usage:
`python snakerun.py your_script.py`

Command-line arguments:
--clear
Delete all virtual environments created by snake_run
"""

import sys
import os
import os.path
import abc

from prefab_classes import prefab, attribute

__version__ = "0.0.1a1"
version_pth = __version__.replace(".", "_")

LAUNCHER_NAME = "snakerun"
PYVER_BLOCK_MARKER = "x-requires-python"
DEPENDENCY_BLOCK_MARKER = "script dependencies"

MAX_VENV_CACHESIZE = 10  # Don't keep more than this many virtualenvs


class UnsupportedPlatform(Exception):
    """
    Operating system not supported - This is not actually an OS error
    """


class MetadataError(Exception):
    """
    Error for incorrect use of the metadata format
    """


class PyenvMissingError(FileNotFoundError):
    """
    Error for when pyenv is not installed
    """


platform = sys.platform
if platform == "win32":
    CACHE_PATH = os.path.expandvars(f"%LOCALAPPDATA%/{LAUNCHER_NAME}/venv_cache")
elif platform == "linux":
    CACHE_PATH = os.path.expanduser(f"~/.{LAUNCHER_NAME}/venv_cache")
elif platform == "darwin":
    CACHE_PATH = os.path.expanduser(
        f"~/Library/Caches/{LAUNCHER_NAME}/venv_cache"
    )
else:
    raise UnsupportedPlatform(f"'{platform}' is currently not supported.")


CACHE_INFO_FILE = os.path.join(CACHE_PATH, f"CACHE_INFO_{version_pth}")


@prefab
class DependencyData:
    python_specifier: None | str
    dependencies: list[str]

    @classmethod
    def from_file(cls, script_path: str | os.PathLike):
        """
        Parse a PEP 722 Dependency block and return a DependencyData object
        """
        python_specifier = None
        deps = []

        with open(script_path, 'r', encoding="utf-8") as f:
            in_dependency_block = False

            for line in f:
                if in_dependency_block:
                    if line.startswith("#"):
                        data, *_ = line[2:].partition(" # ")
                        deps.append(data.strip())
                    else:
                        in_dependency_block = False
                elif line.strip().lower() == f"# {DEPENDENCY_BLOCK_MARKER}:":
                    if deps:
                        raise MetadataError(
                            f"'{DEPENDENCY_BLOCK_MARKER}'"
                            f" block defined multiple times in script"
                        )
                    in_dependency_block = True
                elif line.lower().startswith(f"# {PYVER_BLOCK_MARKER}:"):
                    if python_specifier:
                        raise MetadataError(
                            f"'{PYVER_BLOCK_MARKER}'"
                            f" block defined multiple times in script"
                        )
                    python_specifier = line[2:].partition(":")[2].strip()

                if python_specifier and deps:
                    break

        return cls(python_specifier, deps)  # noqa


def get_pyenv_versions():
    from packaging.version import Version, InvalidVersion
    versions_folder = os.path.expanduser("~/.pyenv/versions")
    if not os.path.exists(versions_folder):
        raise PyenvMissingError("Could not find the pyenv versions folder")

    versions = []
    for p in os.scandir(versions_folder):
        try:
            versions.append(Version(p.name))
        except InvalidVersion:
            pass

    return versions


if __name__ == "__main__":
    print(get_pyenv_versions())
