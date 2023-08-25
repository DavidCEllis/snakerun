"""
Once we need to create a venv and manage dependencies, imports are no longer
as critical as the bottleneck.
"""

import sys
import os
import os.path

# The slow modules avoided in core
import re
import subprocess
import shutil

from packaging.version import Version, InvalidVersion
from packaging.requirements import SpecifierSet

from .core import current_python_version, DependencySpec, VEnvCache, VEnv
from .exceptions import NoMatchingPythonVersion


py_versions_re = re.compile(r"^.+V:(\d+.\d+)[\s|*]+(.+)$")
python_v_re = re.compile(r"^Python\s+(\d+.\d+.\d+)$")


def clear_cache(cache_folder):
    shutil.rmtree(cache_folder)


def get_pyenv_versions() -> list[tuple[Version, str]]:
    """
    Get potential python versions from pyenv (for linux and macos)
    """
    versions_folder = os.path.expandvars("${PYENV_ROOT}/versions")
    if not os.path.exists(versions_folder):
        print("Could not find pyenv versions folder.")
        return []

    versions = []
    for p in os.scandir(versions_folder):
        try:
            versions.append((Version(p.name), os.path.join(p.path, "bin/python")))
        except InvalidVersion:
            pass

    versions.sort(reverse=True, key=lambda x: x[0])

    return versions


def get_py_versions(precise=False) -> list[tuple[Version, str]]:
    """
    Get potential python versions from the windows 'py' launcher.

    Use 'precise' to get the patch version - this requires launching the
    python version so it's considered too slow in general.
    """
    try:
        result = subprocess.run(["py", "--list-paths"], capture_output=True)
    except FileNotFoundError:
        print("py launcher not installed or present on PATH.")
        return []

    output = result.stdout.decode("UTF-8").split("\r\n")

    versions = []
    for line in output:
        data = re.fullmatch(py_versions_re, line)
        if data:
            python_path = data.group(2)
            if precise:
                # Get exact version from `python.exe -V` output
                version_output = subprocess.run(
                    [python_path, "-V"],
                    capture_output=True
                ).stdout.decode("utf-8").strip()

                version_txt = re.match(python_v_re, version_output).group(1)
                version = Version(version_txt)
            else:
                # The version 'py' gives is not the full python version
                # But is probably good enough
                version = Version(data.group(1))

            versions.append((version, python_path))

    versions.sort(reverse=True, key=lambda x: x[0])
    return versions


def get_python_exe(py_specifier: SpecifierSet) -> str:
    pyver = Version(current_python_version())
    if pyver in py_specifier:
        return sys.executable

    if sys.platform in ("linux", "darwin"):
        py_versions = get_pyenv_versions()
    elif sys.platform == "win32":
        py_versions = get_py_versions()
    else:
        py_versions = []

    for env, executable in py_versions:
        if env in py_specifier:
            return executable

    raise NoMatchingPythonVersion(
        f"Could not find a python version to match {py_specifier}"
    )


def build(specification: DependencySpec, cache: VEnvCache):
    # Check requirements are valid
    specification.check_requirements()

    # Get the appropriate python version.
    python_exe = get_python_exe(SpecifierSet(specification.pyver))

    # Remove existing VENV if cache size is too large
    while len(cache.venvs) >= cache.MAX_CACHESIZE:
        env = cache.venvs.pop(0)
        env.delete_venv()
        del env

    # Build VENV
    for i in range(1, cache.MAX_CACHESIZE + 1):
        venv_folder = os.path.join(cache.cache_path, f"{cache.ENV_PREFIX}{i:02d}")
        # Make the cache folder if it doesn't exist
        os.makedirs(cache.cache_path, exist_ok=True)
        if not os.path.exists(venv_folder):
            break
    else:
        raise RuntimeError(
            "Too many environments in cache, possibly left from older versions.\n"
            "Run `snakerun --clear-cache` to clear the cache."
        )

    # -- Build venv --
    print(f"Building venv in {venv_folder}")
    subprocess.run(
        [
            python_exe,
            "-m",
            "venv",
            venv_folder
        ],
        check=True,
        capture_output=True
    )
    venv = VEnv(venv_folder, specification)

    # Update the python path to point to the new venv
    python_exe = venv.python_path
    cache.venvs.append(venv)
    cache.to_cache()

    if specification.dependencies:
        # -- Upgrade pip --
        subprocess.run(
            [
                venv.python_path,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip"
            ],
            check=True,
            capture_output=True
        )

        print("Installing Dependencies: " + ", ".join(f"{dep!r}" for dep in venv.spec.dependencies))
        # -- Install Modules --
        subprocess.run(
            [
                venv.python_path,
                "-m",
                "pip",
                "install",
                *venv.spec.dependencies
            ],
            check=True,
            capture_output=True
        )

    return python_exe
