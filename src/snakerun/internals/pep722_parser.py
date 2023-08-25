import os

from ..constants import PYVER_BLOCK_MARKERS, DEPENDENCY_BLOCK_MARKERS
from ..exceptions import MetadataError


def parse_pep722(source_file: str | os.PathLike) -> tuple[str, list[str]]:
    """
    Python implementation of the PEP722 Parser
    """
    pyver = None
    dependencies = []

    with open(source_file, "r", encoding="utf-8") as f:
        in_dependency_block = False

        for line in f:
            if line.startswith("#"):
                # strip comments and leading '#'
                line = line[1:].partition(" # ")[0].strip()
                if not line:
                    continue  # Skip blank or all comment lines

                if in_dependency_block:
                    dependencies.append(line)
                else:
                    header, _, extra = (
                        item.strip() for item in line.lower().partition(":")
                    )
                    if header in DEPENDENCY_BLOCK_MARKERS:
                        if dependencies:
                            raise MetadataError(
                                "Script Dependencies block "
                                "defined multiple times in script."
                            )
                        in_dependency_block = True
                    elif header in PYVER_BLOCK_MARKERS:
                        if pyver:
                            raise MetadataError(
                                "x-requires-python block "
                                "defined multiple times in script."
                            )
                        pyver = extra
            else:
                if in_dependency_block:
                    in_dependency_block = False
                if pyver and dependencies:
                    break

    return pyver, dependencies
