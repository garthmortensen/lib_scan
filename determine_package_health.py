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

# %%

# using conda, so when appropro, default on conda
# TODO: add param
downloads_pip = list(set(downloads_pip) - set(downloads_conda))

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

script_imports = list(set(script_imports))  # distinct

# %%

pypi_results = []
homepages = []
for package in downloads_pip:

    try:
        url = f"https://pypi.org/pypi/{package}/json"
        r = requests.get(url)
        data = r.json()
    except: print(f"Package not found on pypi: {package}")

    repo_info = {}
    # Section: header =========================================================
    repo_info['package'] = f"{package}"
    repo_info['header'] = f"Info about {package}"
    
    # Section: info ===========================================================
    key_parent = 'info'

    # NB: get() overcomes missing keys. For nested keys, use many gets
    key_child = 'summary'
    repo_info[key_child] = data.get(key_parent).get(key_child)

    key_child = 'requires_python'
    repo_info[key_child] = data.get(key_parent).get(key_child)

    key_child = 'requires_dist'
    repo_info[key_child] = data.get(key_parent).get(key_child)

    key_child = 'yanked'
    repo_info[key_child] = data.get(key_parent).get(key_child)

    try:  # if parent is None, error
        key_child = 'project_urls'
        key_grandchild = 'Homepage'
        repo_info[key_grandchild] = data.get(key_parent).get(key_child).get(key_grandchild)
        homepages.append(repo_info[key_grandchild])
    except: print(f"pypi call {package} contains missing data on: {key_parent}, {key_child}, {key_grandchild}")

    # Section: releases =======================================================
    key_parent = 'info'
    repo_info[key_child] = data.get(key_parent)

    # Section: vulnerabilities ================================================
    key_parent = 'vulnerabilities'
    repo_info[key_child] = data.get(key_parent)
    
    # Section: urls ===========================================================
    key_parent = 'urls'
    repo_info[key_child] = data.get(key_parent)
 
    # api_results['pypi'] = repo_info
    pypi_results.append(repo_info)

# %%

for homepage in homepages:
    if '://github.com/' in homepage:  # https://github.com/jupyter-widgets/ipywidgets

        # parse page before constructing api query url
        owner_repo = homepage.split('://github.com/')[1]  # jupyter-widgets/ipywidgets
        owner = owner_repo.split('/')[0]  # jupyter-widgets
        repo = owner_repo.split('/')[1]  # ipywidgets

        query_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(query_url)
        if response.status_code == 200:  # success
            response_dict = response.json()


# %%


# https://api.anaconda.org/docs
