import pathlib

import pytest

from snakerun.core import DependencySpec

examples_folder = pathlib.Path(__file__).parents[1] / "examples"

specs = [
    ("pep_example_script.py", DependencySpec(pyver=None, dependencies=['requests', 'rich'])),
    ("prefab_demo.py", DependencySpec(pyver=">=3.10", dependencies=['prefab_classes'])),
    ("requires_py39.py", DependencySpec(pyver="~=3.9.0", dependencies=[])),
    ("requires_py310.py", DependencySpec(pyver="~=3.10.0", dependencies=[])),
    ("requires_py311.py", DependencySpec(pyver="~=3.11.0", dependencies=[])),
    ("requires_gt_39.py", DependencySpec(pyver=">=3.9", dependencies=[])),
    ("requires_nothing.py", DependencySpec(pyver=None, dependencies=[])),
]


@pytest.mark.parametrize("path, spec", specs)
def test_spec_matches(path, spec):
    script_file = examples_folder / path

    deps = DependencySpec.from_script(script_file)

    assert deps == spec
