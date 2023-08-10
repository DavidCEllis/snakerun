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
`snakerun your_script.py`

Command-line arguments:
--clear-cache
    Delete all virtual environments created by snake_run
"""

import sys
import os.path

from .core import DependencySpec, VEnvCache
from .exceptions import MetadataError, UnsupportedPlatform


__version__ = "0.0.1a1"
version_pth = __version__.replace(".", "_")

LAUNCHER_NAME = "snakerun"

platform = sys.platform

if platform == "win32":
    CACHE_PATH = os.path.expandvars(f"%LOCALAPPDATA%\\{LAUNCHER_NAME}\\venv_cache")
elif platform == "linux":
    CACHE_PATH = os.path.expanduser(f"~/.{LAUNCHER_NAME}/venv_cache")
elif platform == "darwin":
    CACHE_PATH = os.path.expanduser(
        f"~/Library/Caches/{LAUNCHER_NAME}/venv_cache"
    )
else:
    raise UnsupportedPlatform(f"'{platform}' is currently not supported.")


CACHE_INFO_FILENAME = f"CACHE_INFO_{version_pth}"


def main():

    # re can be removed for faster launch on linux/osx
    # windows entry points use zipapp which uses re internally
    if 're' in sys.modules and sys.platform in ("linux", "darwin"):
        print(
            "Detected 're' import, "
            "Run `python -m snakerun --fixlauncher` "
            "to attempt to remove unnecessary import."
        )

    if sys.argv[1] == "--clear-cache":
        print(f"Removing cache folder {CACHE_PATH}")
        from .build_env import clear_cache
        clear_cache(CACHE_PATH)
        return

    print("Launching with snakerun:")

    script_spec = DependencySpec.from_script(sys.argv[1])

    if script_spec.satisfied():
        python_path = sys.executable
    else:
        cached_envs = VEnvCache.from_cache(CACHE_PATH)
        for env in cached_envs.venvs:
            if env.spec == script_spec:
                python_path = env.python_path
                break
        else:
            from . import build_env
            python_path = build_env.build(script_spec, cached_envs)

    args = [
        python_path,
        *sys.argv[1:]
    ]

    sys.stdout.flush()

    response = os.spawnv(os.P_WAIT, python_path, args)

    return response


if __name__ == "__main__":
    sys.exit(main())
