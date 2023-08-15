**The format used for this is still subject to change.**

**This is currently an experiment with using the PEP-722 style dependency format and is only lightly tested.**

# SnakeRun #

Launch python scripts with specific python versions and dependencies.

## How to use ##

Inside your python script specify requirements in a PEP-722 style format.

eg:
```python
# Script Dependencies:
#     prefab_classes>=0.9.3
#     requests
```

Optionally specify python version with a non-standard `# x-requires-python: >=3.10`.

Run with `snakerun myscript.py`
Clear caches with `snakerun --clear-cache`

## Logic ##

In order to save time on launching, environments are cached based upon 
the exact text of the specification. If a text match can be found then 
the matching environment will be used without any further comparison.

If there is no match then a new venv will be generated. If a python
version is given it will be checked against the version used to launch
`snakerun` first. If that is sufficient it will be used to create the venv.

Otherwise:
* On Windows:
  * `snakerun` will ask the `py` launcher for available python versions
    if a sufficient version is found that will be used, otherwise an 
    error will be raised. (On windows this will only look for 3.X, not 3.X.Y)
* On Linux/MacOS:
  * `snakerun` will look for `pyenv` environments. If a sufficient version
    is found that will be used, otherwise an error will be raised.

If dependencies are specified they will be installed into the new venv and
then the script will be launched.

If no python version or dependencies are given, the version of python
running `snakerun.py` will launch the script without creating a venv.

## Why not TOML ##

It is faster to parse this block than it is to import any of the main 
python toml libraries.

```
Summary
  'python perf/parse_dependencies.py' ran
    1.99 ± 0.29 times faster than 'python -c "import pytomlpp"'
    2.38 ± 0.32 times faster than 'python -c "import rtoml"'
    2.42 ± 0.32 times faster than 'python -c "import tomllib"'
    3.53 ± 0.46 times faster than 'python -c "import tomlkit"'
```

This isn't to say any of these libraries are 'bad' or 'slow'. Parsing a TOML
file in general is more complex than parsing the simple PEP-722 block. In service 
of parsing the more complex data or for maintainability these modules have 
made different choices which have a noticeable impact on import performance
and make them less suitable for this specific use case.

## Other performance considerations ##

Much like prefab_classes this goes to some lengths to keep the start time
as low as possible (for python). Ideally the only overhead in the optimal 
case is the time it takes to parse the dependency format and find the 
cached environment.

This leads to avoiding some otherwise useful modules as importing
them takes as long as launching python from scratch.

* `re` would probably be cleaner than looking for string matches but 
  adds 60% to the launch time (on my development machine)
  * This is actually still used when pip installed as part of the entrypoint
    script that is generated. There is a script included to replace that 
    entrypoint script if so desired.
  * Note: on windows `re` gets used as part of the zipapp format anyway
* `argparse` would be useful to allow for the addition of command line arguments
  but nearly doubles the launch time.
* `subprocess` is the new intended way to launch processes, but `os.spawnv`
  is used in the fast path because importing subprocess doubles the launch time
* `packaging` is useful to compare specifications but its use is delayed until
  after the initial comparison because importing `packaging.specifiers` would
  make launching take 4x longer.

If no match is found this time is largely insignificant as the time to create
the venv and install dependencies will be much more noticeable.
