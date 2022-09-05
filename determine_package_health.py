# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 19:12:28 2022

@author: garth

8 w 8
8 w 88b.     d88b .d8b .d88 8 gm.
8 8 8  8     `Yb. 8    8  8 8P Y8
8 8 88P' www Y88P `Y8P `Y88 8   8

For packages found within .py modules and yml env files, pull info from APIs
pypi, github condaforge, github and stackoverflow.

To see what the an API call look like:
    pypi api: https://pypi.org/pypi/ipywidgets/json
    github api: https://api.github.com/repos/jupyter-widgets/ipywidgets

refactor for clean functional programming:
2 source files:
    1. yml
        - dependencies
        [API calls condaforge, SO, github]
            - pip:
                [API calls pypi, SO, github]
    2. local_py_imports
        - less *.py local filenames
        - less standard_libraries
        - lists
            if in conda_list:
                [API calls condaforge, SO, github]
            elif in pip_list:
                [API calls pypi, SO, github]

modules = {"conda": [
        	, "condaforge": []
        	, "github": []
        	, "stackoverflow": []
        	]
        , "pip": [
        	, "pypi": []
        	, "github": []
        	, "stackoverflow": []
        	]}

then oop refactor:
    class Module(object):
        - self.module name
        - self.homepage
        - self.SO tags
        - self.in pip_list or conda_list
        - self.repo info (pypi or condaforge stats)

    class yaml_file(object):
    class script_file(object):
"""

import requests
import os
import subprocess
import io
import sys
import json
from datetime import datetime  # for delta days
import yaml

# load github token to overcome api limit
from pathlib import Path

# set working path
dir_py = os.path.dirname(os.path.abspath("__file__"))  # linux friendly
os.chdir(dir_py)

# %%

def token_in_env(token_env: bool) -> str:
    """If you have Github token saved in ~/.env, input True.
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


def calc_delta_days(timestamp: str) -> str:
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
    """Pull repo stats using GitHub API. This provides stats not available via
    other pypi/conda repo API calls.
    Input:
        https://api.github.com/repos/{owner}/{repo}
        e.g. https://github.com/jupyter-widgets/ipywidgets
        github username
        github API token
    Output: dict of pulled repo content
    """

    # parse page before constructing api query url
    owner_repo = homepage.split('://github.com/')[1]  # jupyter-widgets/ipywidgets
    owner = owner_repo.split('/')[0]  # jupyter-widgets
    repo = owner_repo.split('/')[1]  # ipywidgets

    query_url = f"https://api.github.com/repos/{owner}/{repo}"
    sess = requests.Session()
    # sess.proxies = proxies
    response = sess.get(query_url, auth=token_in_env(True))

    # loop through json elements and populate dict
    github_repo_info = {}

    key_parent = "api_url_repo"
    github_repo_info[f"github_{key_parent}"] = query_url

    # ensure request succeeds
    if response.status_code != 200:  #  request failed
        github_repo_info['github_api_status'] = "fail"

    else:  # request succeeded
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
        response = sess.get(query_url, auth=token_in_env(True))
        
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


# %%

def pull_condaforge_content(module: str) -> dict:
    """
    Read from condaforge raw feedstock readme.md file, parse for developer site,
    then feed this url to github API.
    Example file to be parsed:
    https://raw.githubusercontent.com/conda-forge/qtconsole-feedstock/main/README.md

    Input: module name
    Output: dict of module's Github content
    """

    condaforge_repo_info = {}
    query_url = f"https://raw.githubusercontent.com/conda-forge/{module}-feedstock/main/README.md"

    key_parent = "api_url_repo"
    condaforge_repo_info[f"condaforge_{key_parent}"] = query_url

    sess = requests.Session()
    response = sess.get(query_url, stream=True)  # stream until website found

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

    return condaforge_repo_info


def pull_stackoverflow_content(package: str) -> dict:
    """Pull package info using Stackoverflow API.
    API limit is 300 requests/day. OAuth registration requires a domain.
    Example endpoint:
    https://api.stackexchange.com/2.3/packages/{package}/info?site=stackoverflow
    https://stackoverflow.com/questions/packageged/{package}

    Input: library name as string
    Output: dict of stackoverflow stats
    """

    package = package  # search SO for package name as package
    query_url = f"https://api.stackexchange.com/2.3/packages/{package}/info?site=stackoverflow"
    sess = requests.Session()
    response = sess.get(query_url, stream=True)  # stream until website found

    package_info = {}
    # json section: header ================================================
    package_info['stackoverflow_package'] = f"{package}"

    # ensure request succeeds
    if response.status_code != 200:  #  request failed
        package_info['stackoverflow_api_status'] = "fail"

    else:   # request succeeded
        try:
            data = response.json()
            data = data['items'][0]  # items contains a list of length 1!
            package_info['stackoverflow_api_status'] = "success"

            key_parent = 'name'
            package_info[f"stackoverflow_{key_parent}"] = data.get(key_parent)

            key_parent = 'has_synonyms'
            package_info[f"stackoverflow_{key_parent}"] = data.get(key_parent)

            key_parent = 'count'
            package_info[f"stackoverflow_{key_parent}"] = data.get(key_parent)

        except IndexError:
            package_info['stackoverflow_api_status'] = "stackoverflow package returned no results"

    return package_info


def pull_pypi_content(package: str) -> dict:
    """Given a package name, function queries pypi repo for selected fields.
    Pypi repo typically contains the official dev site for each package. This
    site is read in, and if it links to a Github page, the function then
    queries Github API.
    """

    pypi_results = {}

    query_url = f"https://pypi.org/pypi/{package}/json"
    sess = requests.Session()
    response = sess.get(query_url, stream=True)  # stream until website found

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

    pypi_results["pypi"] = repo_info

    return pypi_results


# %%


def get_pip_list_modules() -> list:
    """Function runs command line to determine which packages were installed
    via `pip install {module}`
    Output: list of modules
    """
    pip_list_modules = []
    proc = subprocess.Popen('pip list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        pip_list_modules.append(line)

    pip_list_modules = pip_list_modules[2:]  # drop header lines
    pip_list_modules = list(set(pip_list_modules))

    return pip_list_modules


def get_conda_list_modules() -> list:
    """Function runs command line to determine which packages were installed
    via `conda install {module}`
    Output: list of modules
    """
    conda_list_modules = []
    proc = subprocess.Popen('conda list', stdout=subprocess.PIPE, shell=True)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        conda_list_modules.append(line)

    conda_list_modules = conda_list_modules[3:]  # drop header lines
    conda_list_modules = list(set(conda_list_modules))

    return conda_list_modules


def get_standard_libraries() -> list:
    """
    Get list of all standard libraries. If code fails, it returns the hardcoded
    standard library for python version 3.9.7

    Output:
    list of standard library names found in Lib dir.
    """

    try:
        # start list with python version
        standard_libraries = []
        standard_libraries.append(sys.version)    
        standard_lib_path = os.path.join(sys.prefix, "Lib")
        for file in os.listdir(standard_lib_path):
            standard_libraries.append(file.split(".py")[0].strip().lower())
        
    except:  # still working on linux functionality
        standard_libraries = ["3.9.7 (default, Sep 16 2021, 16:59:28) [MSC v.1916 64 bit (AMD64)]", "abc", "aifc", "antigravity", "argparse", "ast", "asynchat", "asyncio", "asyncore", "base64", "bdb", "binhex", "bisect", "bz2", "calendar", "cgi", "cgitb", "chunk", "cmd", "code", "codecs", "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser", "contextlib", "contextvars", "copy", "copyreg", "cprofile", "crypt", "csv", "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis", "distutils", "doctest", "email", "encodings", "ensurepip", "enum", "filecmp", "fileinput", "fnmatch", "formatter", "fractions", "ftplib", "functools", "genericpath", "getopt", "getpass", "gettext", "glob", "graphlib", "gzip", "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect", "io", "ipaddress", "json", "keyword", "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox", "mailcap", "mimetypes", "modulefinder", "msilib", "multiprocessing", "netrc", "nntplib", "ntpath", "nturl2path", "numbers", "opcode", "operator", "optparse", "os", "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform", "plistlib", "poplib", "posixpath", "pprint", "profile", "pstats", "pty", "pyclbr", "pydoc", "pydoc_data", "py_compile", "queue", "quopri", "random", "re", "reprlib", "rlcompleter", "runpy", "sched", "secrets", "selectors", "shelve", "shlex", "shutil", "signal", "site-packages", "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "sqlite3", "sre_compile", "sre_constants", "sre_parse", "ssl", "stat", "statistics", "string", "stringprep", "struct", "subprocess", "sunau", "symbol", "symtable", "sysconfig", "tabnanny", "tarfile", "telnetlib", "tempfile", "test", "textwrap", "this", "threading", "timeit", "tkinter", "token", "tokenize", "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types", "typing", "unittest", "urllib", "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zoneinfo", "_aix_support", "_bootlocale", "_bootsubprocess", "_collections_abc", "_compat_pickle", "_compression", "_markupbase", "_nsis", "_osx_support", "_pydecimal", "_pyio", "_py_abc", "_sitebuiltins", "_strptime", "_system_path", "_threading_local", "_weakrefset", "__future__", "__phello__.foo", "__pycache__", ]

    return standard_libraries


# %%


def get_script_names(dir_py: str) -> list:
    """
    Create list of .py modules found in input directory.
    
    Because .py modules may import functionality from personally created
    modules located in the same directory, these filenames should be excluded
    from API qeuries. That is, if you wrote helper.py module and 
    `import helper`, then this would be excluded from API queries.
    
    Input: string directory of where your working project modules are.
    Output: 
        list of filenames, without file extensions.
    """

    dir_scripts = os.path.join(dir_py, "input_py")

    filenames = []
    for file in os.listdir(dir_scripts):
        if file.endswith('.py'):
            filenames.append(file.replace(".py", ""))

    return filenames


# %%


def get_script_imports(dir_py: str) -> dict:
    """
    Scans all files in input directory and creates a list of all imported
    modules. Removed standard library and local module .py imports from result.
    
    It then checks each module to see if it was installed via conda or pip,
    then makes respective API requests.
    
    It also writes results to a .json file in ouput dir.
    
    Input: string directory of where your working project modules are.
    Output: dict of API requests
    """

    dir_scripts = os.path.join(dir_py, "input_py")

    # get lists of installed modules
    conda_list_modules = get_conda_list_modules()  # $ conda list
    pip_list_modules = get_pip_list_modules()  # $ pip list

    already_checked = []
    conda_modules = {}
    pip_modules = {}
    all_modules = {}
    for file in os.listdir(dir_scripts):
        if file.endswith('.py'):
            filepath = os.path.join(dir_scripts, file)
            lines = open(filepath, "r").readlines()

            for line in lines:
                if 'import' in line:
                    import_line = line.split(' ')[1]
                    module = import_line.strip().lower()
                    # this handles `from sqlalchemy import a, from sqlalchemy import b`

                    if import_line not in get_standard_libraries() \
                            and import_line not in get_script_names(dir_py) \
                            and import_line not in already_checked:
                        already_checked.append(import_line)

                        if import_line in conda_list_modules:
                            conda_modules[module] = pull_stackoverflow_content(module)
                            conda_modules[module]["condaforge"] = pull_condaforge_content(module)

                        elif import_line in pip_list_modules:
                            pip_modules[module] = pull_stackoverflow_content(module)
                            pip_modules[module]["pypi"] = pull_pypi_content(module)

    all_modules["conda_modules"] = conda_modules
    all_modules["pip_modules"] = pip_modules

    # write to file
    file = json.dumps(all_modules, indent=4)
    with open(os.path.join(dir_py, "output", "local_script_imports.json"), "w") as outfile:
        outfile.write(file)

    return all_modules


local_script_imports = get_script_imports(dir_py)

# %%


def get_yml_modules() -> dict:
    """Reads yml/yaml conda environment files in a directory, and then does
    API requests for conda dependencies, followed by pip dependencies.
    
    Output: dict of API requests
    It also writes results to a .json file in ouput dir.
    """

    dir_yml = os.path.join(dir_py, "input_yml")

    all_modules = {}
    conda_modules = {}
    pip_modules = {}
    for file in os.listdir(dir_yml):
        if file.endswith('.yml') or file.endswith('.yaml'):
            # TODO: or file == "requirements.txt":
            filepath = os.path.join(dir_yml, file)
            with open(filepath, "r") as stream:
                yml_file = yaml.safe_load(stream)  # safe cannot execute code
    
                # drill down into 'dependencies' yml block
                dependencies = yml_file['dependencies']
                for module in dependencies:
                    
                    # each module is a string in this list
                    if isinstance(module, str):
                        if "=" in module:
                            module = module.split("=")[0].strip().lower()
                            conda_modules[module] = pull_stackoverflow_content(module)
                            conda_modules[module]["condaforge"] = pull_condaforge_content(module)
                        elif "://" in module:  # http sites can happen
                            next
                        else:
                            conda_modules[module] = f"Unexpected formatting on {module}"

                    # pip dependencies, are a nested dict
                    # this contains single element list, so drill down again
                    # then iterate through pip dependency lis
                    elif isinstance(module, dict) and 'pip' in module.keys():
                        for pip_module in module['pip']:
                            if "=" in pip_module:
                                pip_module = pip_module.split("=")[0].strip().lower()
                                pip_modules[pip_module] = pull_stackoverflow_content(pip_module)
                                pip_modules[pip_module]["pypi"] = pull_pypi_content(pip_module)
                            elif "://" in pip_module:  # http sites can happen
                                next
                            else:
                                pip_modules[pip_module] = f"Unexpected formatting on {pip_module}"
                                
    all_modules["conda_modules"] = conda_modules
    all_modules["pip_modules"] = pip_modules

    # write to file
    file = json.dumps(all_modules, indent=4)
    with open(os.path.join(dir_py, "output", "yml_env_modules.json"), "w") as outfile:
        outfile.write(file)

    return all_modules


yml_env_modules = get_yml_modules()
