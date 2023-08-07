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
"""
import sys
import os
import time

from prefab_classes import prefab, attribute

LAUNCHER_NAME = "snakerun"
PYVER_BLOCK_MARKER = "X-Minimum-Python"
DEPENDENCY_BLOCK_MARKER = "Script Dependencies"

MAX_VENV_CACHESIZE = 10  # Don't keep more than this many virtualenvs


class UnsupportedPlatform(Exception):
    """
    Operating system not supported - This is not actually an OS error
    """


class MetadataError(Exception):
    """
    Error for incorrect use of the metadata format
    """
    pass


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


CACHE_INFO_FILE = os.path.join(CACHE_PATH, "CACHE_INFO")


@prefab(compile_prefab=True, compile_fallback=True)
class CacheEnv:
    ctime: int
    pyver: tuple[int, int, int]
    dependencies: str

    def __prefab_post_init__(self, pyver: str):
        self.pyver = tuple(int(item) for item in pyver.split("."))  # noqa: always len 3
        assert len(self.pyver) == 3

    @classmethod
    def from_line(cls, line):
        ctime, pyver, *dependencies = line.split(";")
        ctime = int(ctime)
        dependencies = ';'.join(dependencies)

        return cls(ctime, pyver, dependencies)

    def match(self, pyver: tuple[int, int, int], dependencies: str):
        if dependencies != self.dependencies:
            return False

        if pyver is None:
            return True

        return pyver >= tuple(int(v) for v in self.pyver.split())


@prefab(compile_prefab=True, compile_fallback=True)
class MetadataBlock:
    name: str
    extra: str
    contents: list[str] = attribute(default_factory=list)


@prefab(compile_prefab=True, compile_fallback=True)
class Metadata:
    data: dict[str, MetadataBlock]

    def get_cache_info(self) -> tuple[str, str]:

        pyver = ".".join(sys.version_info[:3])
        ctime = time.time_ns()
        dependencies = ",".join(sorted(self.dependencies))

        cache_path = os.path.join(CACHE_PATH, str(ctime))

        return cache_path, f"{ctime};{pyver};{dependencies}"

    @property
    def python_version_ok(self, version_info=None) -> bool:
        """
        Naively check python version

        :return: True if this version of python is sufficient for the script
        """
        min_version = self.data.get(PYVER_BLOCK_MARKER, None)
        if min_version:
            try:
                version_tuple = tuple(
                    (int(item) for item in min_version.extra.split(".")))
            except ValueError:
                raise MetadataError(
                    "Python version specification must only use integers")
            if version_info is None:
                return sys.version_info[:3] >= version_tuple
            else:
                return version_info >= version_tuple
        else:
            return True

    @property
    def dependencies(self) -> list[str]:
        """
        Get dependency tuple from metadata.

        :return: tuple of dependencies if present in metadata or empty list
        """
        try:
            return self.data[DEPENDENCY_BLOCK_MARKER].contents
        except KeyError:
            return []

    @property
    def checked_dependencies(self):
        # Delay importing until absolutely necessary
        # This will only be used *AFTER* finding there is no cached venv
        from packaging.requirements import Requirement
        return [Requirement(item) for item in self.dependencies]

    @classmethod
    def from_file(cls, filename: str | os.PathLike):
        metadata_blocks: dict[str, MetadataBlock] = {}

        with open(filename, "r", encoding="utf-8") as f:
            current_block: None | MetadataBlock = None
            for line in f:
                if line.startswith("##"):
                    if current_block:
                        data = line[2:].strip()
                        if data:
                            current_block.contents.append(data)
                    else:
                        block_type, sep, extra = (
                            item.strip() for item in line[2:].partition(":")
                        )
                        if not sep:
                            continue
                        if block_type in metadata_blocks:
                            if extra:
                                raise MetadataError(
                                    f"Extra block defined twice for {block_type}"
                                )
                            current_block = metadata_blocks[block_type]
                        else:
                            current_block = MetadataBlock(block_type, extra.strip())
                            metadata_blocks[block_type] = current_block
                else:
                    current_block = None

        return cls(metadata_blocks)
