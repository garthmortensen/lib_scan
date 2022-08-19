# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 19:12:28 2022

@author: garth

Determine package health
"""

import requests
import os
import subprocess
import json

dir_py = os.path.dirname(__file__)
os.chdir(dir_py)  # change working path
dir_scripts = os.path.join(dir_py, "sample_scripts")

# %%

# determine which modules are in pip installed
data = subprocess.check_output(["pip", "list", "--format", "json"])
parsed_results = json.loads(data)

pip_list = []
for each in parsed_results:
    pip_list.append(each['name'].lower())

# %%

# determine which modules are in conda list

# %%

# exclude modules are in standard library (not on pypi)

# %%

# collect all scripts in directory in order to search them
used_imports = []
for file in os.listdir(dir_scripts):
    if file.endswith('.py'):
        filepath = os.path.join(dir_scripts, file)
        lines = open(filepath, "r").readlines()
        
        for line in lines:
            if 'import' in line:
                # "import sqlalchemy = 1"
                # "from sqlalchemy import Table"
                # "from sqlalchemy import *"
                import_line = line.split(' ')[1]
                import_line = import_line.strip().lower()
                if import_line in pip_list \
                        or import_line in pip_list:  # TODO switch to conda_list
                    used_imports.append(import_line)
                else:
                    print(f"{import_line} not found")

used_imports = list(set(used_imports))  # remove dupes from list

# %%

package = used_imports[0]
url = f"https://pypi.org/pypi/{package}/json"
r = requests.get(url)
data = r.json()

# info = data['info']
# releases = data['releases']
# vulnerabilities = data['vulnerabilities']
# urls = data['urls']


# https://api.anaconda.org/docs

