"""
Once we need to create a venv and manage dependencies, imports are no longer
as critical as the bottleneck.
"""

import sys
import os
import os.path
from packaging.version import Version, InvalidVersion
from packaging.requirements import Requirement

from .core import current_python_version, DependencyData, VEnvCache, VEnv
from .exceptions import PyenvMissingError


def clear_cache(cache_folder):
    pass


def get_pyenv_versions():
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


def build(requirements: DependencyData, venvs: VEnvCache):
    # Get the current python version
    python_ver = Version(current_python_version())

    return sys.executable
