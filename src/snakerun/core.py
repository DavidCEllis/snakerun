import sys
import os
import os.path

from prefab_classes import prefab, attribute

from .internals import parse_pep722


def current_python_version():
    # If no python version is given, assume only major/minor match
    v = sys.version_info
    return f"{v.major}.{v.minor}"


@prefab
class DependencySpec:
    pyver: str
    dependencies: list[str]
    version_given: bool = attribute(init=False, compare=False, repr=False)

    def __prefab_post_init__(self, pyver: None | str):
        self.pyver = pyver if pyver else f"~={current_python_version()}"
        self.version_given = True if pyver else False

    def nospec(self):
        """
        return True if there was no version or dependencies given
        """
        return not (self.version_given or self.dependencies)

    def check_requirements(self):
        from packaging.requirements import Requirement

        return [Requirement(dep) for dep in self.dependencies]

    @classmethod
    def from_script(cls, script_path: str | os.PathLike):
        """
        Get dependencies from a script file
        """
        if type(script_path) is not str:  # strict check for 'str' - not a subclass either.
            script_path = str(script_path)
        pyver, deps = parse_pep722(script_path)
        return cls(pyver, deps)


@prefab
class VEnv:
    env_folder: str
    spec: DependencySpec

    @property
    def python_path(self):
        if sys.platform == "win32":
            pth = os.path.join(self.env_folder, "Scripts", "python.exe")
        else:
            pth = os.path.join(self.env_folder, "bin", "python")
        return pth

    def delete_venv(self):
        import shutil

        shutil.rmtree(self.env_folder)
        print(f"Cached venv: {self.env_folder} removed")

    def to_string(self):
        dep_list = "\n".join(self.spec.dependencies)
        return f"{self.env_folder}\n{self.spec.pyver}\n{dep_list}"


@prefab
class VEnvCache:
    MAX_CACHESIZE = 5  # Don't keep more than this many virtualenvs
    ENV_PREFIX = "cached_venv_"

    cache_path: str
    venvs: list[VEnv]

    @property
    def cache_info_path(self):
        from . import CACHE_INFO_FILENAME

        return os.path.join(self.cache_path, CACHE_INFO_FILENAME)

    @classmethod
    def from_cache(cls, cache_path):
        from . import CACHE_INFO_FILENAME

        cache_info_path = os.path.join(cache_path, CACHE_INFO_FILENAME)

        try:
            with open(cache_info_path, "r", encoding="utf-8") as f:
                venv_blocks = f.read().split("\n\n")
        except FileNotFoundError:
            return cls(cache_path, [])

        venvs = []
        for block in venv_blocks:
            block = block.strip()  # ignore empty blocks
            if block:
                path, pyver, *deps = block.split("\n")
                venvs.append(VEnv(path, DependencySpec(pyver, deps)))

        return cls(cache_path, venvs)

    def to_cache(self):
        with open(self.cache_info_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(v.to_string() for v in self.venvs))
