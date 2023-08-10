import sys
import os
import os.path

from .exceptions import MetadataError


PYVER_BLOCK_MARKERS = {
    "x-requires-python",
}
DEPENDENCY_BLOCK_MARKERS = {
    "script dependencies",
}


def current_python_version():
    # If no python version is given, assume only major/minor match
    v = sys.version_info
    return f"{v.major}.{v.minor}"


class DependencySpec:
    pyver: str
    dependencies: list[str]

    def __init__(self, pyver: None | str, dependencies: list[str]):
        if pyver:
            self.pyver = pyver
            self.version_given = True
        else:
            self.pyver = f"=={current_python_version()}"
            self.version_given = False

        self.dependencies = dependencies

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"pyver={self.pyver!r}, "
            f"dependencies={self.dependencies!r}"
            f")"
        )

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return (self.pyver, self.dependencies) == (other.pyver, other.dependencies)
        return False

    def satisfied(self):
        """
        return True if the parent env satisfies the requirements
        """
        if (
            self.pyver == f"=={current_python_version()}" or not self.version_given
        ) and not self.dependencies:
            return True
        return False

    def check_requirements(self):
        from packaging.requirements import Requirement

        return [Requirement(dep) for dep in self.dependencies]

    @classmethod
    def from_script(cls, script_path: str | os.PathLike):
        """
        Parse a PEP 722 Dependency block and return a DependencyData object
        """
        python_specifier = None
        deps = []

        with open(script_path, "r", encoding="utf-8") as f:
            in_dependency_block = False

            for line in f:
                if line.startswith("#"):
                    # strip comments and leading '#'
                    line = line[1:].partition(" # ")[0].strip()
                    if not line:
                        continue  # Skip blank or all comment lines

                    if in_dependency_block:
                        deps.append(line)
                    else:
                        header, _, extra = (
                            item.strip() for item in line.lower().partition(":")
                        )
                        if header in DEPENDENCY_BLOCK_MARKERS:
                            if deps:
                                raise MetadataError(
                                    "Script Dependencies block "
                                    "defined multiple times in script"
                                )
                            in_dependency_block = True
                        elif header in PYVER_BLOCK_MARKERS:
                            if python_specifier:
                                raise MetadataError(
                                    f"x-requires-python block "
                                    f"defined multiple times in script"
                                )
                            python_specifier = extra
                else:
                    if in_dependency_block:
                        in_dependency_block = False
                    if python_specifier and deps:
                        break

        return cls(python_specifier, deps)


class VEnv:
    env_folder: str
    spec: DependencySpec

    def __init__(self, env_folder, spec):
        self.env_folder = env_folder
        self.spec = spec

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"env_folder={self.env_folder!r}, "
            f"spec={self.spec!r}"
            f")"
        )

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


class VEnvCache:
    MAX_CACHESIZE = 10  # Don't keep more than this many virtualenvs
    ENV_PREFIX = "cached_venv_"

    cache_path: str
    venvs: list[VEnv]

    def __init__(self, cache_path, venvs):
        self.cache_path = cache_path
        self.venvs = venvs

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"cache_path={self.cache_path!r}, "
            f"venvs={self.venvs!r}"
            f")"
        )

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
