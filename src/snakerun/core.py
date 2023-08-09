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
    # If no python version is given, assume exact match with the version running
    v = sys.version_info
    if v.releaselevel == "final":
        current_ver = f"{v.major}.{v.minor}.{v.micro}"
    elif v.releaselevel == "candidate":
        current_ver = f"{v.major}.{v.minor}.{v.micro}rc{v.serial}"
    elif v.releaselevel in {"alpha", "beta"}:
        current_ver = f"{v.major}.{v.minor}.{v.micro}{v.releaselevel[0]}{v.serial}"
    else:
        raise ValueError(f"Unrecognised Python release level {v.releaselevel}")
    return current_ver


class DependencyData:
    pyver: str
    dependencies: list[str]

    def __init__(self, pyver: None | str, dependencies: list[str]):
        if pyver:
            self.pyver = pyver
        else:
            self.pyver = f"=={current_python_version()}"

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
            return (self.pyver, self.dependencies) == (other.pyver, other.spec)
        return False

    @property
    def requirements(self):
        from packaging.requirements import Requirement
        return [Requirement(dep) for dep in self.dependencies]

    @classmethod
    def from_script(cls, script_path: str | os.PathLike):
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

        return cls(python_specifier, deps)


class VEnv:
    python_path: str
    spec: DependencyData

    def __init__(self, path, spec):
        self.python_path = path
        self.spec = spec

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"python_path={self.python_path!r}, "
            f"spec={self.spec!r}"
            f")"
        )

    def to_string(self):
        dep_list = "\n".join(self.spec.dependencies)
        return (
            f"{self.python_path}\n"
            f"{self.spec}\n"
            f"{dep_list}\n"
        )


class VEnvCache:
    venvs: list[VEnv]

    def __init__(self, venvs):
        self.venvs = venvs

    def __repr__(self):
        return f"{type(self).__name__}(venvs={self.venvs!r})"

    @classmethod
    def from_cache(cls, cache_info_file):
        try:
            with open(cache_info_file, 'r', encoding="utf-8") as f:
                venv_blocks = f.read().split("\n\n")
        except FileNotFoundError:
            return cls([])

        venvs = []
        for block in venv_blocks:
            path, pyver, *deps = block.split("\n")
            venvs.append(VEnv(path, DependencyData(pyver, deps)))

        return cls(venvs)

    def to_cache(self, cache_info_file):
        with open(cache_info_file, 'w', encoding="utf-8") as f:
            f.write("\n".join(v.to_string() for v in self.venvs))
