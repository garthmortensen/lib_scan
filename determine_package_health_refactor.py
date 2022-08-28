# -*- coding: utf-8 -*-
"""
Created on Sun Aug 28 11:43:57 2022

@author: garth
"""

import requests
import os
import subprocess
import io
import sys
import json
from datetime import datetime  # for delta days
import urllib.request  # parse readme
import fnmatch  # parse yml

# load github token to overcome api limit
from pathlib import Path

# set working path
dir_py = os.path.dirname(__file__)
os.chdir(dir_py)  # change working path

# %%

def token_in_env(token_env):
    """If you have github token in .env file, input True.
    Otherwise, input False and paste values below.
    """
    if token_env:
        from dotenv import load_dotenv  # pip install python-dotenv

        # get environmental variables
        home = Path.home() / ".env"
        load_dotenv(home)
        github_user = os.getenv("github_user")
        github_token = os.getenv("github_token")

    else:
        github_user = ""
        github_token = ""

    return github_user, github_token


github_user, github_token = token_in_env(True)


# %%


def get_yml_modules():
    """reads a single yml file in directory
    returns list of conda dependencies and pip dependencies"""
    dir_yml = os.path.join(dir_py, "input_yml")

    # loop will parse all files, but return only last file
    for file in os.listdir(dir_yml):
        if file.endswith('.yml') or file.endswith('.yaml'):
            filepath = os.path.join(dir_yml, file)
            all_lines = open(filepath, "r").readlines()

            yml_env_conda_modules = []
            yml_env_pip_modules = []

            # find start of conda and pip dependencies. Convert from list
            start_conda_dep = fnmatch.filter(all_lines, "*dependencies:*")[0]
            start_pip_dep = fnmatch.filter(all_lines, "*pip:*")[0]

            try:
                start_conda_dep_int = all_lines.index(start_conda_dep)
                start_pip_dep_int = all_lines.index(start_pip_dep)

                # scan from dependencies: to pip:
                for line in all_lines[start_conda_dep_int + 1: start_pip_dep_int]:  # go from there, but exclude dependencies line
                        try:
                            # parse line for package name
                            dash_space_removed = line.split("- ")[1]
                            # the following line handles <= >= ==
                            version_removed = dash_space_removed.split("=")[0]
                            version_removed = version_removed.strip().lower()
                            yml_env_conda_modules.append(version_removed)

                        except IndexError:
                            print("Index error perhaps due to comment or wheel url in yml conda dependencies.")

                # scan after pip:
                for line in all_lines[start_pip_dep_int + 1:]:  # go from there, but exclude dependencies line
                    if ":" in line:  # stop at next header
                        break
                    else:
                        # parse line for package name
                        try:
                            dash_space_removed = line.split("- ")[1]
                            # the following line handles <= >= ==
                            version_removed = dash_space_removed.split("=")[0]
                            version_removed = version_removed.strip().lower()
                            yml_env_pip_modules.append(version_removed)
                        except IndexError:
                            print("Index error perhaps due to comment or wheel url in yml pip dependencies.")

            except IndexError:
                print("yml might not contain dependencies.")


    return yml_env_conda_modules, yml_env_pip_modules


def get_script_modules(dir_py: str) -> list:
    """
    Input: string directory of where your working project modules are.
    Output: list of `import yxz` modules.

    Collects all modules in directory, gets imports.
    The text parsing handles various import techniques, such as:
        `import sqlalchemy = 1`
        `from sqlalchemy import Table`
        `from sqlalchemy import *`

    Note: If you import a personally made module, there may be a false API matches
    """

    dir_scripts = os.path.join(dir_py, "input_py")

    script_modules = []
    for file in os.listdir(dir_scripts):
        if file.endswith('.py'):
            filepath = os.path.join(dir_scripts, file)
            lines = open(filepath, "r").readlines()

            for line in lines:
                if 'import' in line:
                    import_line = line.split(' ')[1]
                    import_line = import_line.strip().lower()
                    script_modules.append(import_line)

    return list(set(script_modules))  # distinct


def get_standard_modules() -> list:
    """
    Output:
    list of standard library names found in Lib dir.

    Description:
    get list of all standard libraries.

    You may decide to exclude standard_modules from results,
    since theyre not on pypi or conda repos
    """

    standard_modules = []
    standard_lib_path = os.path.join(sys.prefix, "Lib")
    for file in os.listdir(standard_lib_path):
        standard_modules.append(file.split(".py")[0].strip().lower())

    return standard_modules


def get_pip_list_modules() -> list:
    """pip installs source from pypi repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from pip
    """
    pip_list_modules = []
    proc = subprocess.Popen('pip list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        pip_list_modules.append(line)

    return pip_list_modules[2:]  # drop header lines


def get_conda_list_modules() -> list:
    # TODO: if not conda user, this might error
    """conda installs source from Anaconda repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from conda
    """
    conda_list_modules = []
    proc = subprocess.Popen('conda list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        conda_list_modules.append(line)

    return conda_list_modules[3:]  # drop header lines


# %%

# Ideally, these should be mutually exclusive
standard_libs = get_standard_modules()  # prolly exclude this from subsequent lists
local_script_modules = get_script_modules(dir_py)  # your files
# pip_list_libs = get_pip_list_libs()  # $ pip list
# conda_list_libs = get_conda_list_libs()  # $ conda list
yml_env_conda_modules, yml_env_pip_modules = get_yml_modules()  # yml content

local_script_modules = list(set(local_script_modules) - set(standard_libs))

# optional check: pypi has API, but not conda, so default on pip lookup
# pip_list_libs = list(set(pip_list_libs) - set(conda_list_libs) - set(standard_libs))

# conda_list_libs = list(set(conda_list_libs) - set(pip_list_libs) - set(standard_libs))
yml_env_conda_modules = list(set(yml_env_conda_modules) - set(standard_libs))
yml_env_pip_modules = list(set(yml_env_pip_modules) - set(standard_libs))

# %%

print(f"length of local_script_libs: {len(local_script_modules)}")
# print(f"length of pip_list_libs: {len(pip_list_libs)}")
# print(f"length of conda_list_libs: {len(conda_list_libs)}")
print(f"length of yml_env_conda_libraries: {len(yml_env_conda_libraries)}")
print(f"length of yml_env_pip_libraries: {len(yml_env_pip_libraries)}")
