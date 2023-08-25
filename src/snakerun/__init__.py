"""
SnakeRun

Parse a meaningful comment form to get the requirements for a python script.
Launch a python environment matching those requirements.

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
from .constants import LAUNCHER_NAME

__version__ = "0.1.0"
version_pth = __version__.replace(".", "_")

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

    if len(sys.argv) <= 1:
        print("No path given to script")
        return 0

    if sys.argv[1] == "--clear-cache":
        print(f"Removing cache folder {CACHE_PATH}")
        from .build_env import clear_cache
        clear_cache(CACHE_PATH)
        return 0

    print("Launching with snakerun:")

    script_spec = DependencySpec.from_script(sys.argv[1])

    if script_spec.nospec():
        python_path = sys.executable
    else:
        cached_envs = VEnvCache.from_cache(CACHE_PATH)
        for env in cached_envs.venvs:
            if env.spec == script_spec:
                # Move this env to the end of the list
                # resort the cache
                cached_envs.venvs.remove(env)
                cached_envs.venvs.append(env)
                cached_envs.to_cache()

                python_path = env.python_path
                break
        else:
            from . import build_env
            python_path = build_env.build(script_spec, cached_envs)

    args = [
        python_path,
        *sys.argv[1:]
    ]

    response = os.spawnv(os.P_WAIT, python_path, args)

    return response


if __name__ == "__main__":
    sys.exit(main())
