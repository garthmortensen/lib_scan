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

        # set environmental variables
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

def get_standard_libraries():
    """
    Output:
    list of standard library names found in Lib dir.

    Description:
    get list of all standard libraries.

    You may decide to exclude standard_modules from results,
    since theyre not on pypi or conda repos
    """

    standard_libraries = []
    standard_lib_path = os.path.join(sys.prefix, "Lib")
    for file in os.listdir(standard_lib_path):
        standard_libraries.append(file.split(".py")[0].strip().lower())

    return standard_libraries


# standard_libs = get_standard_libraries()  # prolly exclude this from subsequent lists

# %%


def get_yml_modules(remove_standard_libs=False) -> list:
    """reads a single yml file in directory
    returns list of conda dependencies and pip dependencies
    Input: set whether you want to remove standard libraries. This would
    be a good idea if standard libraries are not working (perhaps linux)
    """
    
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
    
    # Not sure if standard libs are every in yml dependencies, but leaving as option
    if remove_standard_libs:
        yml_env_conda_modules = list(set(yml_env_conda_modules) - set(get_standard_libraries()))
        yml_env_pip_modules = list(set(yml_env_pip_modules) - set(get_standard_libraries()))

    return {"yml_env_conda_modules": yml_env_conda_modules, 
            "yml_env_pip_modules": yml_env_pip_modules}

yml_env_modules = get_yml_modules(False)


# %%

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


def get_pip_list_modules(remove_standard_libs=False) -> list:
    """pip installs source from pypi repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from pip
    """
    pip_list_modules = []
    proc = subprocess.Popen('pip list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        pip_list_modules.append(line)

    pip_list_modules = pip_list_modules[2:]  # drop header lines

    # Not sure if standard libs are every in yml dependencies, but leaving as option
    if remove_standard_libs:
        pip_list_modules = list(set(pip_list_modules) - set(get_standard_libraries()))

    return pip_list_modules  # drop header lines


def get_conda_list_modules(remove_standard_libs=False) -> list:
    """conda installs source from Anaconda repo, and out of the box
    are not installed or imported, so must be downloaded and imported
    this function determines which libraries were downloaded from conda
    """
    conda_list_modules = []
    proc = subprocess.Popen('conda list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        conda_list_modules.append(line)

    conda_list_modules = conda_list_modules[3:]  # drop header lines

    # Not sure if standard libs are every in yml dependencies, but leaving as option
    if remove_standard_libs:
        conda_list_modules = list(set(conda_list_modules) - set(get_standard_libraries()))

    return pip_list_modules


# %%

# Ideally, these should be mutually exclusive
local_script_modules = get_script_modules(dir_py)  # your files
pip_list_modules = get_pip_list_modules()  # $ pip list
conda_list_modules = get_conda_list_modules()  # $ conda list
yml_env_conda_modules, yml_env_pip_modules = get_yml_modules(True)  # yml content
standard_libs = get_standard_libraries()

# %%

local_script_modules = list(set(local_script_modules) - set(standard_libs))

# optional check: pypi has API, but not conda, so default on pip lookup
pip_list_modules = list(set(pip_list_modules) - set(conda_list_modules) - set(standard_libs))

# conda_list_libs = list(set(conda_list_libs) - set(pip_list_libs) - set(standard_libs))
yml_env_conda_modules = list(set(yml_env_conda_modules) - set(standard_libs))
yml_env_pip_modules = list(set(yml_env_pip_modules) - set(standard_libs))

# %%

print(f"length of local_script_libs: {len(local_script_modules)}")
print(f"length of pip_list_modules: {len(pip_list_modules)}")
print(f"length of conda_list_modules: {len(conda_list_modules)}")
print(f"length of yml_env_conda_modules: {len(yml_env_conda_modules)}")
print(f"length of yml_env_pip_modules: {len(yml_env_pip_modules)}")

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
    Output: dict of stackoverflow stats
    """

    tag = package  # search SO for package name as tag
    query_url = f"https://api.stackexchange.com/2.3/tags/{tag}/info?site=stackoverflow"
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


# %%


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
                    repo_info['github_api_pull'] = "Github dev site not listed."

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
local_script_libs_results = pull_pypi_content(dir_py, local_script_modules, "script_modules")
pip_list_modules_results = pull_pypi_content(dir_py, pip_list_modules, "pip_list_modules")
conda_list_modules_results = pull_pypi_content(dir_py, conda_list_modules, "conda_list_modules")

# %%

def pull_condaforge_content(dir_py: str, module_list: list, filename: str) -> list:
    """
    Read from condaforge feedstock readme.md file, parse for developer site,
    then feed site to github API search function.
    example file to scan:
    https://raw.githubusercontent.com/conda-forge/qtconsole-feedstock/main/README.md

    Input: module name
    Output: dict of modules Github developer page
    """

    condaforge_libs_results = []
    for module in yml_env_conda_modules:
        query_url = f"https://raw.githubusercontent.com/conda-forge/{module}-feedstock/main/README.md"

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
                    dev_line = line.decode('UTF-8')
                    homepage = dev_line.split(' ')[1].strip()
                    if '://github.com/' in homepage:
                        # https://api.github.com/repos/{owner}/{repo}
                        # https://github.com/jupyter-widgets/ipywidgets
                        github_api_call = pull_github_content(homepage)
                        condaforge_repo_info['github_api_pull'] = github_api_call
                        break  # stop parsing readme.md
                    else:
                        condaforge_repo_info['github_api_pull'] = "Github dev site not listed."
                else:
                    condaforge_repo_info['github_api_pull'] = "development site not listed."

        condaforge_libs_results.append(condaforge_repo_info)

    file = json.dumps(condaforge_libs_results, indent=4)

    with open(os.path.join(dir_py, "output", filename + ".json"), "w") as outfile:
        outfile.write(file)


pull_condaforge_content(dir_py, yml_env_conda_modules, "yml_env_conda_modules")


# %%

# TODO: get R package info
# github.com/cran/package
