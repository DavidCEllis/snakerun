# Original (modified) example from the PEP
#
# In order to run, this script needs the following 3rd party libraries
#
# Script Dependencies:
#    requests
#    rich     # Needed for the output

import requests
from rich.pretty import pprint

resp = requests.get("https://peps.python.org/api/peps.json")
data = resp.json()
pprint([(k, v["title"]) for k, v in data.items()][:10])
