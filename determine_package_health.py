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
import io
import sys

dir_py = os.path.dirname(__file__)
os.chdir(dir_py)  # change working path
dir_scripts = os.path.join(dir_py, "sample_scripts")

# %%

# exclude modules are in standard library (not on pypi)

# standardlibrary = dont need to download, but need to import
# things that automatically come with python when you download it
# but these all take a lot space, so these are not automatically loaded

standard_libs = []
standard_lib_path = os.path.join(sys.prefix, "Lib")
for file in os.listdir(standard_lib_path):
    standard_libs.append(file.split(".py")[0].strip().lower())

# exclude these from results, since not on pypi or conda repo

# builtins = dont need to import
# these are all automatically loaded. No need to import them.
# you dont need to `import print`
# print(dir(__builtins__))
# builtins are irrelevant to this script.

# %%

# pypi, conda repo
# not installed or imported, so must download and import

# determine which modules are in pip list
downloads_pip = []
proc = subprocess.Popen('pip list', stdout=subprocess.PIPE)
for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
    line = line.split()[0].strip().lower()  # get first column, strip spaces
    downloads_pip.append(line)
downloads_pip = downloads_pip[2:]  # drop header lines

# determine which modules are in conda list
downloads_conda = []
proc = subprocess.Popen('conda list', stdout=subprocess.PIPE)
for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
    line = line.split()[0].strip().lower()  # get first column, strip spaces
    downloads_conda.append(line)
downloads_conda = downloads_conda[3:]  # drop header lines

downloaded_libs = downloads_pip + downloads_conda

# %%

# collect all scripts in directory in order to search them
script_imports = []
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
                script_imports.append(import_line)

script_imports = list(set(script_imports))  # remove dupes from list

# %%

pypi_searches = []
for import_line in script_imports:
    if import_line in downloaded_libs:
        print(f"{import_line} in downloaded_libs. Adding to search list")
        pypi_searches.append(import_line)
    if import_line in standard_libs:
        print(f"{import_line} in standard_libs. No need to check health.")

# %%

package = pypi_searches[0]
url = f"https://pypi.org/pypi/{package}/json"
r = requests.get(url)
data = r.json()

info = data['info']
releases = data['releases']
vulnerabilities = data['vulnerabilities']
urls = data['urls']


# https://api.anaconda.org/docs

