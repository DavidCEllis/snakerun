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

Some elements are being written in both rust with fallback implementations 
in python where performance is a concern on the fast path. 
