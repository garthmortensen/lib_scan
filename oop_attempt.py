# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 11:23:21 2022
 
 L
 L:         L         L:LLLL
 L:     L   LL      LLLL  LLL
 LL    LoL  LL      LL:
 LL     L    LL      :LLLLLLL                             LLL
 :L          LL          L:LLLLL       L:LL      :LL   L::LLLL
  LL         LLLL:            :LL:   LLLLL:   LLLLLL   LLL: LLL
  LL    LL   :L  LL             :L   LL       LLLLLL   LLL   LL
  LL    LL   LL  LL       LLL  LLL   LLLL:::  LLL L:   :L     L:
  LL    LL    :LLL        LLLLLL:      LLLLL                  gm
  LL



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

import platform
import requests
import os
import subprocess
import io
import sys
import json
from datetime import datetime  # for delta days
import yaml

# to timestamp file
right_now = datetime.today().strftime('%Y%m%d_%H%M%S')

# load github token to overcome api limit
from pathlib import Path

# set working path
if platform.system() == 'Windows':
    dir_py = os.path.dirname(__file__)
else:
    dir_py = os.path.dirname(os.path.abspath("__file__"))  # linux friendly?

os.chdir(dir_py)

# %%

def token_in_env(token_env: bool=False) -> str:
    """If you have Github token saved in ~/.env, input True.
    Otherwise, input False and paste values into below code.
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


def convert_github_page_to_endpoint(homepage: str):
    """Convert github page to api endpoint
    Input: https://github.com/jupyter-widgets/ipywidgets
    Output: https://api.github.com/repos/jupyter-widgets/ipywidgets
    """
    owner_repo = homepage.split('://github.com/')[1]  # jupyter-widgets/ipywidgets
    owner = owner_repo.split('/')[0]  # jupyter-widgets
    repo = owner_repo.split('/')[1]  # ipywidgets
    query_url = f"https://api.github.com/repos/{owner}/{repo}"
    return query_url


def find_github_pages(package: str) -> dict:
    """Finds github pages listed on pypi and condaforge websites. If they list
    the same github page, only one page is returned.
    
    Conda-forge raw readme link:
    Read from condaforge raw feedstock readme.md file, parse for developer site,
    then feed this url to github API.
    Example file to be parsed:
    https://raw.githubusercontent.com/conda-forge/setuptools-feedstock/main/README.md
    
    Input: package name
    Output: dictionary of 1 or 2 github urls
    """

    repo_info = {}

    # find github page on pypi
    query_url = f"https://pypi.org/pypi/{package}/json"
    sess = requests.Session()
    response = sess.get(query_url, stream=True)  # stream until website found

    # ensure request succeeds
    if response.status_code != 200:  #  request failed
        next

    else:   # request succeeded
        data = response.json()
        try:  # if parent is None, error
            key_parent = 'info'
            key_child = 'project_urls'
            key_grandchild = 'Homepage'
            homepage = data.get(key_parent).get(key_child).get(key_grandchild)
            if '://github.com/' in homepage:
                query_url = convert_github_page_to_endpoint(homepage)
                repo_info['github_page_pypi'] = query_url
            # else:
                # repo_info['github_page_pypi'] = "None"

        except:
            print(f"pypi call {package} for github page failed")

    # TODO: get conda-forge github page
    query_url = f"https://api.github.com/repos/conda-forge/{package}-feedstock"
    sess = requests.Session()
    response = sess.get(query_url, stream=True)  # stream until website found

    # ensure request succeeds
    if response.status_code != 200:  #  request failed
        next

    else:   # request succeeded
        data = response.json()
        try:  # if parent is None, error
            repo_info['github_page_condaforge_repo'] = query_url

        except:
            print(f"conda-forge request {package} for github page failed")

    # find github homepage page on condaforge
    query_url = f"https://raw.githubusercontent.com/conda-forge/{package}-feedstock/main/README.md"
    sess = requests.Session()
    response = sess.get(query_url, stream=True)  # stream until website found

    # ensure request succeeds
    if response.status_code != 200:  #  request failed
        next

    else:   # request succeeded
        # iterate through readme.md lines, stop early when the "dev:" found
        for line in response.iter_lines():
            if 'development:' in str(line).lower():
                dev_line = line.decode('UTF-8')
                homepage = dev_line.split(' ')[1].strip()
                if '://github.com/' in homepage:
                    query_url = convert_github_page_to_endpoint(homepage)
                    repo_info['github_page_condaforge'] = query_url
                    break  # stop parsing readme.md
                # else:
                    # repo_info['github_page_condaforge'] = "None"
            else:
                continue  # return to `if`
    
    # if both pypi and condaforge return same dev site, return one
    if 'github_page_pypi' in repo_info and \
        'github_page_condaforge' in repo_info and \
        repo_info['github_page_pypi'] == repo_info['github_page_condaforge']:

        repo_info['github_page_pypi_condaforge'] = query_url
        del repo_info['github_page_pypi'], repo_info['github_page_condaforge']
    
    print(repo_info)
    return repo_info


# %%


def pull_github_content(query_url: str) -> dict:
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
    owner_repo = query_url.split('://api.github.com/repos/')[1]  # jupyter-widgets/ipywidgets
    owner = owner_repo.split('/')[0]  # jupyter-widgets
    repo = owner_repo.split('/')[1]  # ipywidgets

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

    return github_repo_info


# %%


def pull_stackoverflow_content(package: str) -> dict:
    """Pull package info using Stackoverflow API.
    API limit is 300 requests/day. OAuth registration requires a domain.
    Example endpoint:
    https://api.stackexchange.com/2.3/packages/{package}/info?site=stackoverflow
    https://stackoverflow.com/questions/packages/{package}

    Input: library name as string
    Output: dict of stackoverflow stats
    """

    package = package  # search SO for package name as package
    query_url = f"https://api.stackexchange.com/2.3/tags?inname={package}&site=stackoverflow"
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

            package_info['stackoverflow_api_call'] = query_url

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


def get_standard_libraries(attempt_reading_libs=False) -> list:
    """
    Get list of all standard libraries. If code fails, it returns the hardcoded
    standard library for python version 3.9.7

    Output:
    list of standard library names found in Lib dir.
    """

    if attempt_reading_libs:
        try:
            # start list with python version
            standard_libraries = []
            standard_libraries.append(sys.version)    
            standard_lib_path = os.path.join(sys.prefix, "Lib")
            for file in os.listdir(standard_lib_path):
                standard_libraries.append(file.split(".py")[0].strip().lower())
        
        except:  # still working on linux functionality
            print("get_standard_libraries failed. Run with arg = False")
    
    else:
        standard_libraries = ["__future__", "__main__", "__phello__.foo", "__pycache__", "_aix_support", "_bootlocale", "_bootsubprocess", "_collections_abc", "_compat_pickle", "_compression", "_markupbase", "_nsis", "_osx_support", "_py_abc", "_pydecimal", "_pyio", "_sitebuiltins", "_strptime", "_system_path", "_thread", "_threading_local", "_weakrefset", "abc", "aifc", "antigravity", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore", "atexit", "audioop", "base64", "bdb", "binascii", "binhex", "bisect", "builtins", "bz2", "cProfile", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs", "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser", "contextlib", "contextvars", "copy", "copyreg", "cprofile", "crypt", "crypt ", "csv", "ctypes", "curses", "curses ", "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis", "distutils", "doctest", "email", "encodings", "ensurepip", "enum", "errno", "faulthandler", "fcntl ", "filecmp", "fileinput", "fnmatch", "formatter", "fractions", "ftplib", "functools", "gc", "genericpath", "getopt", "getpass", "gettext", "glob", "graphlib", "grp ", "gzip", "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect", "io", "ipaddress", "itertools", "json", "keyword", "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder", "msilib", "msilib ", "msvcrt ", "multiprocessing", "netrc", "nis ", "nntplib", "ntpath", "nturl2path", "numbers", "opcode", "operator", "optparse", "os", "ossaudiodev ", "pathlib", "pdb", "pickle", "pickletools", "pipes", "pipes ", "pkgutil", "platform", "plistlib", "poplib", "posixpath", "posix ", "pprint", "profile", "pstats", "pty", "pty ", "pwd ", "py_compile", "pyclbr", "pydoc", "pydoc_data", "queue", "quopri", "random", "re", "readline ", "reprlib", "resource ", "rlcompleter", "runpy", "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil", "signal", "site", "site-packages", "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "spwd ", "sqlite3", "sre_compile", "sre_constants", "sre_parse", "ssl", "stat", "statistics", "string", "stringprep", "struct", "subprocess", "sunau", "symbol", "symtable", "sys", "sysconfig", "syslog ", "tabnanny", "tarfile", "telnetlib", "tempfile", "termios ", "test", "textwrap", "this", "threading", "time", "timeit", "tkinter", "token", "tokenize", "trace", "traceback", "tracemalloc", "tty", "tty ", "turtle", "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser", "winreg ", "winsound ", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo", ]

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
    # conda_list_modules = get_conda_list_modules()  # $ conda list
    # pip_list_modules = get_pip_list_modules()  # $ pip list

    already_checked = []
    conda_modules = {}
    pip_modules = {}
    all_modules = {}
    for file in os.listdir(dir_scripts):
        print(f"processing file: {file}")
        if file.endswith('.py'):
            filepath = os.path.join(dir_scripts, file)
            lines = open(filepath, "r").readlines()

            for line in lines:
                if 'import' in line.casefold():
                    module = line.split(' ')[1]
                    module = module.strip().lower()
                    # this handles `from sqlalchemy import a, from sqlalchemy import b`

                    if module not in get_standard_libraries() \
                            and module not in get_script_names(dir_py) \
                            and module not in already_checked:
                        already_checked.append(module)
                        print(f"processing module: {module}")

                        # if module in conda_list_modules:
                            # conda_modules[module] = pull_stackoverflow_content(module)

                        # elif module in pip_list_modules:
                            # pip_modules[module] = pull_stackoverflow_content(module)
                            # pip_modules[module]["pypi"] = pull_pypi_content(module)
                            
                        # else:  # if module not conda or pip installed
                        pip_modules[module] = pull_stackoverflow_content(module)
                        pip_modules[module]["pypi"] = pull_pypi_content(module)
                        pip_modules[module]["github"] = find_github_pages(module)

                        # get all homepages and make github endpoint calls
                        for key, homepage in pip_modules[module]["github"].items():
                            pip_modules[module]["github"][key] = pull_github_content(homepage)

    all_modules["conda_modules"] = conda_modules
    all_modules["pip_modules"] = pip_modules

    # write to file
    file = json.dumps(all_modules, indent=4)
    with open(os.path.join(dir_py, "output", f"local_script_imports_{right_now}.json"), "w") as outfile:
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
    with open(os.path.join(dir_py, "output", f"yml_env_modules_{right_now}.json"), "w") as outfile:
        outfile.write(file)

    return all_modules


# yml_env_modules = get_yml_modules()
