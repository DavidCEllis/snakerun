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
the specification, not the environment. An environment will only be 
reused if the **specification** matches.

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


## Performance considerations ##

As a tool that is intended to start, find an environment matching and launch
as quickly as possible in the fast case, many modules that would otherwise
make development easier are avoided in the code that will be loaded
in this case.

Most of the available argument parsers and the modules they depend on
add a significant proportion of runtime so the current goal is to avoid
them if possible.

* `re` would be necessary for most current commandline parsers but 
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

All of these are used when it is clear that a new env will have to be constructed.
