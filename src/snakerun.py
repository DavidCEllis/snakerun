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


__version__ = "0.0.1a1"
version_pth = __version__.replace(".", "_")

LAUNCHER_NAME = "snakerun"
PYVER_BLOCK_MARKERS = {
    "x-requires-python",
}
DEPENDENCY_BLOCK_MARKERS = {
    "script dependencies",
    "script_dependencies",
    "script-dependencies",
    "scriptdependencies",
}

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


class DependencyData:
    python_specifier: None | str
    dependencies: list[str]

    def __init__(self, python_specifier: None | str, dependencies: list[str]):
        self.python_specifier = python_specifier
        self.dependencies = dependencies

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"python_specifier={self.python_specifier}, "
            f"dependencies={self.dependencies}"
            f")"
        )

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return (self.python_specifier, self.dependencies) == (other.python_specifier, other.dependencies)
        return False

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
                if line.startswith("#"):
                    line = line[1:].partition(" # ")[0].strip()  # strip comments and leading '#'
                    if not line:
                        continue  # Skip blank or all comment lines

                    if in_dependency_block:
                        deps.append(line)
                    else:
                        header, _, extra = (item.strip() for item in line.lower().partition(":"))
                        if header in DEPENDENCY_BLOCK_MARKERS:
                            if deps:
                                raise MetadataError(
                                    "Script Dependencies block defined multiple times in script"
                                )
                            in_dependency_block = True
                        elif header in PYVER_BLOCK_MARKERS:
                            if python_specifier:
                                raise MetadataError(
                                    f"x-requires-python block defined multiple times in script"
                                )
                            python_specifier = extra
                else:
                    if in_dependency_block:
                        in_dependency_block = False
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

    versions.sort(reverse=True)

    return versions


if __name__ == "__main__":
    d = DependencyData.from_file(sys.argv[1])
    print(d)
