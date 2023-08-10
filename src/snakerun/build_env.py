"""
Once we need to create a venv and manage dependencies, imports are no longer
as critical as the bottleneck.
"""

import sys
import os
import os.path
import subprocess

from packaging.version import Version, InvalidVersion
from packaging.requirements import SpecifierSet

from .core import current_python_version, DependencyData, VEnvCache, VEnv
from .exceptions import NoMatchingPythonVersion


def clear_cache(cache_folder):
    pass


def get_pyenv_versions() -> list[tuple[Version, str]]:
    """
    Get potential python versions from pyenv (for linux and macos)
    """
    versions_folder = os.path.expanduser("~/.pyenv/versions")
    if not os.path.exists(versions_folder):
        return []

    versions = []
    for p in os.scandir(versions_folder):
        try:
            versions.append((Version(p.name), os.path.join(p.path, "bin/python")))
        except InvalidVersion:
            pass

    versions.sort(reverse=True, key=lambda x: x[0])

    return versions


def get_py_versions() -> list[tuple[Version, str]]:
    """
    Get potential python versions from the windows 'py' launcher.
    """


def get_python_exe(py_specifier: SpecifierSet) -> str:
    pyver = Version(current_python_version())
    if pyver in py_specifier:
        return sys.executable

    if sys.platform in ("linux", "darwin"):
        pyenv_versions = get_pyenv_versions()
        for env, executable in pyenv_versions:
            if env in py_specifier:
                return executable

    raise NoMatchingPythonVersion(f"Could not find a python version to match {py_specifier}")


def build(requirements: DependencyData, venvs: VEnvCache):
    # Get the current python version
    python_exe = get_python_exe(SpecifierSet(requirements.pyver))

    # Build VENV

    # Install Modules

    # Handle venv cache

    return python_exe
