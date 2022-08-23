# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 19:12:28 2022

@author: garth

Pull library repo info from pypi and github, using APIs.

This can be used to assess the vitality of a package.

To see what the API calls look like, load up Postman and get:
    pypi api: https://pypi.org/pypi/ipywidgets/json
    github api: https://api.github.com/repos/jupyter-widgets/ipywidgets
"""

import requests
import os
import subprocess
import io
import sys
import json
from datetime import datetime

# load github token to overcome api limit
from dotenv import load_dotenv  # pip install python-dotenv
from pathlib import Path

# set working path
dir_py = os.path.dirname(__file__)
os.chdir(dir_py)  # change working path

# set environmental variables
home = Path.home() / ".env"
load_dotenv(home)
github_user = os.getenv("github_user")
github_token = os.getenv("github_token")

# %%


def get_local_script_imports(dir_py: str) -> list:
    """
    Input: string directory of where your working project scripts are.
    Output: list of imported modules in project scripts.

    Collects all scripts in directory, and finds imports
    The text parsing handles various import techniques, such as:
        "import sqlalchemy = 1"
        "from sqlalchemy import Table"
        "from sqlalchemy import *"
    
    Note: If you import a personally made script, there may be a false match
    on the pypi repo.
    """

    dir_scripts = os.path.join(dir_py, "input")

    script_imports = []
    for file in os.listdir(dir_scripts):
        if file.endswith('.py'):
            filepath = os.path.join(dir_scripts, file)
            lines = open(filepath, "r").readlines()
            
            for line in lines:
                if 'import' in line:
                    import_line = line.split(' ')[1]
                    import_line = import_line.strip().lower()
                    script_imports.append(import_line)
    
    return list(set(script_imports))  # distinct


def get_standard_libs() -> list:
    """
    Output: 
    list of standard library names found in Lib dir.
    
    Description:
    get list of all standard libraries.

    standardlibrary = dont need to download, but need to import
    things that automatically come with python when you download it
    but these all take a lot space, so these are not automatically loaded

    builtins = dont need to import
    these are all automatically loaded. No need to import them.
    you dont need to `import print`
    print(dir(__builtins__))
    builtins are irrelevant to this script.

    Consider excluding standard_libs from results,
    since theyre not on pypi or conda repos
    """

    standard_libs = []
    standard_lib_path = os.path.join(sys.prefix, "Lib")
    for file in os.listdir(standard_lib_path):
        standard_libs.append(file.split(".py")[0].strip().lower())

    return standard_libs


def get_downloaded_pip_libs() -> list:
    """pip installs source from pypi repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from pip
    """
    downloads_pip = []
    proc = subprocess.Popen('pip list', stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        downloads_pip.append(line)
    
    return downloads_pip[2:]  # drop header lines


def get_downloaded_conda_libs() -> list:
    # TODO: if not conda user, this might error
    """conda installs source from Anaconda repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from conda
    """    
    downloads_conda = []
    proc = subprocess.Popen('conda list', stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        downloads_conda.append(line)

    return downloads_conda[3:]  # drop header lines


# %%

# obtain lists of libraries from different sources
# Ideally, these should be mutually exclusive
script_imports = get_local_script_imports(dir_py)
standard_libs = get_standard_libs()  # no health check needed
downloads_pip = get_downloaded_pip_libs()
downloads_conda = get_downloaded_conda_libs()

# remove standard libs from scripts
# checking on scripts_imports is the main objective
script_imports = list(set(script_imports) - set(standard_libs))

# optional check: pypi has API, but not conda, so lookup using pip
downloads_pip = list(set(downloads_pip) - set(downloads_conda))

# optional check: find leftover conda libraries
downloads_conda = list(set(downloads_conda) - set(downloads_pip))

print(f"length of script_imports: {len(script_imports)}")
print(f"length of downloads_pip: {len(downloads_pip)}")
print(f"length of downloads_conda: {len(downloads_conda)}")

# %%

def calc_delta_days(timestamp):
    """Input: string timestamp
    Output: string of total day difference from timestamp
    """

    datetime_format = '%Y-%m-%d'
    updated_at = timestamp[0:10]  # string = 2012-06-11T23:41:23Z
    today = datetime.today().strftime('%Y-%m-%d')
    
    updated_at = datetime.strptime(updated_at, datetime_format)
    today = datetime.strptime(today, datetime_format)
    delta = today - updated_at
    
    return f"{delta} days"


def pull_github_content(homepage: str) -> dict:
    """Pull repo stats using GitHub API. Provides additional stats which are
    not available at pypi/conda repos.
    Input: 
        https://api.github.com/repos/{owner}/{repo}
        github username
        github API token
    Output: dict of repo stats
    """
    
    # parse page before constructing api query url
    owner_repo = homepage.split('://github.com/')[1]  # jupyter-widgets/ipywidgets
    owner = owner_repo.split('/')[0]  # jupyter-widgets
    repo = owner_repo.split('/')[1]  # ipywidgets
    
    query_url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(query_url, auth=(github_user, github_token))
    
    # loop through json elements and populate dict
    github_repo_info = {}

    # ensure request succeeds
    if response.status_code == 200:  # success
        github_data = response.json()
    
        key_parent = "api_url_repo"
        github_repo_info[f"github_{key_parent}"] = query_url

        # json section: header ================================================
        github_repo_info['github_package'] = f"{repo}"
        github_repo_info['github_header'] = f"Info about {repo}"

        key_parent = 'description'
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        key_parent = "created_at"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        # calc days since creation=============================================
        delta = calc_delta_days(github_data.get(key_parent))
        github_repo_info[f"github_{key_parent}_delta"] = delta

        key_parent = "updated_at"  # string = 2021-04-03T22:01:26Z
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        # calc days since update===============================================
        delta = calc_delta_days(github_data.get(key_parent))
        github_repo_info[f"github_{key_parent}_delta"] = delta
        
        # watcher count
        key_parent = "subscribers_count"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        # user show of support            
        key_parent = "stargazers_count"  
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)
        
			# open_issues_count = issues + pull requests
        key_parent = "has_issues"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        key_parent = "open_issues_count"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)
        
        key_parent = "open_issues"  # repeat?
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)
			
        key_parent = "has_projects"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)
        
        key_parent = "has_downloads"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        key_parent = "has_wiki"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        key_parent = "allow_forking"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        key_parent = "fork"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        key_parent = "forks_count"
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)

        key_parent = "forks"  # repeat?
        github_repo_info[f"github_{key_parent}"] = github_data.get(key_parent)
        
        # get the total count of commits from commits endpoint
        # API limits commit count return to 30
        query_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        response = requests.get(query_url, auth=(github_user, github_token))
        if response.status_code == 200:  # success
            github_data = response.json()
            
            commit_count = 0
            for each in github_data:
                for k in each.keys():  # dont need values() or items()
                    if k == "commit":
                        commit_count += 1

            # key_parent = "api_url_commit"
            # github_repo_info[key_parent] = query_url

            key_parent = "commits_max_30"
            github_repo_info[f"github_{key_parent}"] = commit_count

    # print(json.dumps(github_repo_info))
    return github_repo_info  # dict


def pull_pypi_content(dir_py: str, downloads_pip: list, filename: str) -> list:
    """loop through packages on pypi and pull basic stats"""

    pypi_results = []
    for package in downloads_pip:

        query_url = f"https://pypi.org/pypi/{package}/json"
        response = requests.get(query_url)
        
        # ensure request succeeds
        if response.status_code == 200:
            data = response.json()
    
        repo_info = {}
        # json section: header ================================================
        repo_info['pypi_package'] = f"{package}"
        repo_info['pypi_header'] = f"Info about {package}"
        
        # json section: info ==================================================
        key_parent = 'info'
    
        # Note: get() overcomes missing keys. For nested keys, use many gets
        key_child = 'summary'
        repo_info[f"pypi_{key_parent}_{key_child}"] = data.get(key_parent).get(key_child)
    
        key_child = 'requires_python'
        repo_info[f"pypi_{key_parent}_{key_child}"] = data.get(key_parent).get(key_child)
    
        key_child = 'requires_dist'
        # repo_info[f"pypi_{key_parent}_{key_child}"] = data.get(key_parent).get(key_child)
        repo_info[f"pypi_{key_parent}_{key_child}"] = str(data.get(key_parent).get(key_child))  # formatting variation
    
        key_child = 'yanked'
        repo_info[f"pypi_{key_parent}_{key_child}"] = data.get(key_parent).get(key_child)
        
        # json section: releases ==============================================
        # key_parent = 'releases'
        # repo_info[f"pypi_{key_parent}"] = data.get(key_parent)
    
        # json section: vulnerabilities =======================================
        key_parent = 'vulnerabilities'
        repo_info[f"pypi_{key_parent}"] = data.get(key_parent)
        
        # json section: info github============================================
        key_parent = 'info'

        try:  # if parent is None, error
            key_child = 'project_urls'
            key_grandchild = 'Homepage'

            # json section: github=============================================
            # repeating the assignment, but homepage is cleaner syntax to parse
            homepage = data.get(key_parent).get(key_child).get(key_grandchild)
            if '://github.com/' in homepage:  # https://github.com/jupyter-widgets/ipywidgets
                github_api_call = pull_github_content(homepage)
                repo_info['github_api_pull'] = github_api_call
            else:
                repo_info['github_api_pull'] = "Not a Github homepage."

        except: print(f"pypi call {package} contains missing data on: {key_parent}, {key_child}, {key_grandchild}")
        
        # api_results['pypi'] = repo_info
        pypi_results.append(repo_info)
        
        file = json.dumps(pypi_results, indent=4)

        with open(os.path.join(dir_py, "output", filename + ".json"), "w") as outfile:
            outfile.write(file)

    # return pypi_results
    return json.dumps(pypi_results, indent=4)


# run the searches
pypi_results_script = pull_pypi_content(dir_py, script_imports, "pypi_results_script")
downloads_pip = pull_pypi_content(dir_py, downloads_pip, "downloads_pip")

# %%

# TODO: conda forge?
# conda contains not just python packages, also r, etc
# readme files are standardized and contain homepage
# https://github.com/conda-forge/qtconsole-feedstock#readme
# Development: https://github.com/jupyter/qtconsole


# %%

# TODO: get R package info
# github.com/cran/package

# %%

# TODO: get stackoverflow info on packages
# https://api.stackexchange.com/docs/tags-by-name#order=desc&sort=popular&tags=sql&filter=default&site=stackoverflow&run=true
# https://api.stackexchange.com/2.3/tags/sql/info?order=desc&sort=popular&site=stackoverflow

