# In order to run, this script needs the following 3rd party libraries
#
# x-requires-python: >=3.10
# Script Dependencies:
#    prefab_classes

from prefab_classes import prefab


@prefab
class Demo:
    message: str = "Hello World"


print(Demo())
