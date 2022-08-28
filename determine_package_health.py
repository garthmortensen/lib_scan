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

# TODO: rename "lib/library" references to "package".

import requests
import os
import subprocess
import io
import sys
import json
from datetime import datetime  # for delta days
import urllib.request  # parse readme

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

# TODO: handle subsequent headers, otherwise error
def get_yml_libs() -> list:
    """takes in only 1 .yml/.yaml file"""
    dir_yml = os.path.join(dir_py, "input_yml")

    for file in os.listdir(dir_yml):
        if file.endswith('.yml') or file.endswith('.yaml'):
            filepath = os.path.join(dir_yml, file)
            all_lines = open(filepath, "r").readlines()

            yml_env_libraries = []
            string_dep_line = all_lines.index("dependencies:\n")  # find where dependencies start
            # string_pip_line = all_lines.index("- pip:\n")  # if you want to remove all pip
        
            for line in all_lines[string_dep_line + 1:]:  # go from there, but exclude dependencies line
                if "pip:" not in line:
                    dash_space_removed = line.split("- ")[1]
                    version_removed = dash_space_removed.split("=")[0]
                    version_removed = version_removed.strip().lower()
                    yml_env_libraries.append(version_removed)

    return yml_env_libraries


def get_script_libs(dir_py: str) -> list:
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

    script_libs = []
    for file in os.listdir(dir_scripts):
        if file.endswith('.py'):
            filepath = os.path.join(dir_scripts, file)
            lines = open(filepath, "r").readlines()
            
            for line in lines:
                if 'import' in line:
                    import_line = line.split(' ')[1]
                    import_line = import_line.strip().lower()
                    script_libs.append(import_line)
    
    return list(set(script_libs))  # distinct


def get_standard_libs() -> list:
    """
    Output: 
    list of standard library names found in Lib dir.
    
    Description:
    get list of all standard libraries.

    You may decide to exclude standard_libs from results,
    since theyre not on pypi or conda repos
    """

    standard_libs = []
    standard_lib_path = os.path.join(sys.prefix, "Lib")
    for file in os.listdir(standard_lib_path):
        standard_libs.append(file.split(".py")[0].strip().lower())

    return standard_libs


def get_pip_list_libs() -> list:
    """pip installs source from pypi repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from pip
    """
    pip_list_libs = []
    proc = subprocess.Popen('pip list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        pip_list_libs.append(line)
    
    return pip_list_libs[2:]  # drop header lines


def get_conda_list_libs() -> list:
    # TODO: if not conda user, this might error
    """conda installs source from Anaconda repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from conda
    """    
    conda_list_libs = []
    proc = subprocess.Popen('conda list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        conda_list_libs.append(line)

    return conda_list_libs[3:]  # drop header lines


# %%

# obtain lists of libraries from different sources
# Ideally, these should be mutually exclusive
script_libs = get_script_libs(dir_py)
yml_libs = get_yml_libs()
standard_libs = get_standard_libs()  # no health check needed
pip_list_libs = get_pip_list_libs()
conda_list_libs = get_conda_list_libs()

# remove standard libs from scripts
# checking on scripts_imports is the main objective
script_libs = list(set(script_libs) - set(standard_libs))

# optional check: pypi has API, but not conda, so lookup using pip
pip_list_libs = list(set(pip_list_libs) - set(conda_list_libs))

# optional check: find leftover conda libraries
conda_list_libs = list(set(conda_list_libs) - set(pip_list_libs))

print(f"length of script_libs: {len(script_libs)}")
print(f"length of pip_list_libs: {len(pip_list_libs)}")
print(f"length of conda_list_libs: {len(conda_list_libs)}")

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
        e.g. https://github.com/jupyter-widgets/ipywidgets
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

    key_parent = "api_url_repo"
    github_repo_info[f"github_{key_parent}"] = query_url

    # ensure request succeeds
    if response.status_code != 200:  #  request failed
        github_repo_info['github_api_status'] = "fail"
    
    else:   # request succeeded
        github_data = response.json()
    
        github_repo_info['github_api_status'] = "success"

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
        
        # request count(commits). Limit set to 30 max
        query_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        response = requests.get(query_url, auth=(github_user, github_token))
        if response.status_code == 200:  # success
            github_data = response.json()
            
            commit_count = 0
            for each in github_data:
                for k in each.keys():  # dont need values() or items()
                    if k == "commit":
                        commit_count += 1

            key_parent = "commits_max_30"
            github_repo_info[f"github_{key_parent}"] = commit_count

    # print(json.dumps(github_repo_info))
    return github_repo_info


def pull_stackoverflow_content(package: str) -> dict:
    """Pull library tag stats using Stackoverflow API, on main SO site.
    Tag should be the package name.
    Limit is 300 requests/day. OAuth registration requires domain.

    https://api.stackexchange.com/2.3/tags/{tag}/info?site=stackoverflow
    https://stackoverflow.com/questions/tagged/{tag}

    Input: library name as string
    Output: dict
    """

    tag = package  # search SO for package name as tag
    query_url = f"https://api.stackexchange.com/2.3/tags/{tag}/info?order=desc&sort=popular&site=stackoverflow"
    response = requests.get(query_url)
    
    stackoverflow_results = []
    
    tag_info = {}
    # json section: header ================================================
    tag_info['stackoverflow_tag'] = f"{tag}"
    tag_info['stackoverflow_header'] = f"Info about {tag}"
    
    # ensure request succeeds
    if response.status_code != 200:  #  request failed
        tag_info['stackoverflow_api_status'] = "fail"
    
    else:   # request succeeded
        try:
            data = response.json()
            data = data['items'][0]  # items contains a list of length 1!
            tag_info['stackoverflow_api_status'] = "success"
            
            key_parent = 'name'
            tag_info[f"stackoverflow_{key_parent}"] = data.get(key_parent)
            
            key_parent = 'has_synonyms'
            tag_info[f"stackoverflow_{key_parent}"] = data.get(key_parent)
            
            key_parent = 'count'
            tag_info[f"stackoverflow_{key_parent}"] = data.get(key_parent)
            
            stackoverflow_results.append(tag_info)

        except IndexError:
            tag_info['stackoverflow_api_status'] = "tag returned no results"
    
    return stackoverflow_results


def pull_pypi_content(dir_py: str, pip_list_libs: list, filename: str) -> list:
    """loop through packages on pypi and pull basic stats"""

    pypi_results = []
    for package in pip_list_libs:

        query_url = f"https://pypi.org/pypi/{package}/json"
        response = requests.get(query_url)

        repo_info = {}
        # json section: header ================================================
        repo_info['pypi_package'] = f"{package}"
        repo_info['pypi_header'] = f"Info about {package}"
        
        # ensure request succeeds
        if response.status_code != 200:  #  request failed
            repo_info['pypi_api_status'] = "fail"

        else:   # request succeeded
            data = response.json()

            repo_info['pypi_api_status'] = "success"
            
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
            
            # json section: vulnerabilities =======================================
            key_parent = 'vulnerabilities'
            repo_info[f"pypi_{key_parent}"] = data.get(key_parent)
            
            # json section: info github============================================
            key_parent = 'info'
    
            try:  # if parent is None, error
                key_child = 'project_urls'
                key_grandchild = 'Homepage'
    
                # json section: github=============================================
                homepage = data.get(key_parent).get(key_child).get(key_grandchild)
                if '://github.com/' in homepage:  
                    github_api_call = pull_github_content(homepage)
                    repo_info['github_api_pull'] = github_api_call
                else:
                    repo_info['github_api_pull'] = "Github dev site not found."
    
            except: 
                print(f"pypi call {package} contains missing data on: {key_parent}, {key_child}, {key_grandchild}")


            # json section: stackoverflow======================================
            stackoverflow_api_call = pull_stackoverflow_content(package)
            repo_info['stackoverflow_api_call'] = stackoverflow_api_call

            pypi_results.append(repo_info)
        
        file = json.dumps(pypi_results, indent=4)

        with open(os.path.join(dir_py, "output", filename + ".json"), "w") as outfile:
            outfile.write(file)

    # return pypi_results
    return json.dumps(pypi_results, indent=4)


# %%


# run the searches
script_libs_results = pull_pypi_content(dir_py, script_libs, "script_libs")
# pip_list_libs_results = pull_pypi_content(dir_py, pip_list_libs, "pip_list_libs")

# %%

pull_condaforge_content(library):
# https://raw.githubusercontent.com/conda-forge/qtconsole-feedstock/main/README.md
package = "qtconsole"
query_url = f"https://raw.githubusercontent.com/conda-forge/{package}-feedstock/main/README.md"

condaforge_repo_info = {}

key_parent = "api_url_repo"
condaforge_repo_info[f"condaforge_{key_parent}"] = query_url

response = requests.get(query_url, stream=True)  # stream until website found

# ensure request succeeds
if response.status_code != 200:  #  request failed
    condaforge_repo_info['github_api_status'] = "fail"

else:   # request succeeded
    # iterate through readme.md lines, stop early when the "dev:" found
    for line in response.iter_lines():
        if 'development:' in str(line).lower():
            dev_line = str(line)
            homepage = dev_line.split(' ')[1].strip()
            exit

        # json section: github=================================================
        github_api_call = pull_github_content(homepage)
        condaforge_repo_info['github_api_pull'] = github_api_call
        

# %%

# TODO: get R package info
# github.com/cran/package
