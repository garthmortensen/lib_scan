# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 19:12:28 2022

@author: garth

Determine package health
"""

import requests
import os
import subprocess
import io
import sys

# load github token to overcome api limit
from dotenv import load_dotenv  # pip install python-dotenv
from pathlib import Path

# set working path
dir_py = os.path.dirname(__file__)
os.chdir(dir_py)  # change working path
dir_scripts = os.path.join(dir_py, "sample_scripts")

# set environmental variables
home = Path.home() / ".env"
load_dotenv(home)
github_user = os.getenv("github_user")
github_token = os.getenv("github_token")

# %%

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

    exclude standard_libs from results, since theyre not on pypi or conda repos
    """
        
    standard_libs = []
    standard_lib_path = os.path.join(sys.prefix, "Lib")
    for file in os.listdir(standard_lib_path):
        standard_libs.append(file.split(".py")[0].strip().lower())

    return standard_libs


standard_libs = get_standard_libs()

# %%

def get_downloaded_pip_libs() -> list:
    # pypi, conda repo
    # not installed or imported, so must download and import
    
    # determine which modules are in pip list
    downloads_pip = []
    proc = subprocess.Popen('pip list', stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        downloads_pip.append(line)
    
    return downloads_pip[2:]  # drop header lines


def get_downloaded_conda_libs() -> list:
    # TODO: if not conda user, this might error
    # determine which modules are in conda list
    downloads_conda = []
    proc = subprocess.Popen('conda list', stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.split()[0].strip().lower()  # get first column, strip spaces
        downloads_conda.append(line)

    return downloads_conda[3:]  # drop header lines


def pip_less_conda(downloads_pip: list, downloads_conda: list) -> list:
    """If you want to carve conda out of pip, run this"""
    # using conda, so when appropro, default on conda
    # TODO: check if user is not conda, then has no impact?
    return list(set(downloads_pip) - set(downloads_conda))


downloads_pip = get_downloaded_pip_libs()
downloads_conda = get_downloaded_conda_libs()
downloads_pip = pip_less_conda(downloads_pip, downloads_conda)

# %%

def get_local_script_imports(dir_scripts: str) -> list:
    """
    Collects all scripts in directory, and finds imports
    The text parsing handles various import techniques, such as:
        "import sqlalchemy = 1"
        "from sqlalchemy import Table"
        "from sqlalchemy import *"
    """

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


script_imports = get_local_script_imports(dir_scripts)

# %%


def pull_pypi_content(downloads_pip: list) -> list:
    """loop through packages on pypi and pull basic stats"""

    pypi_results = []
    homepages = []
    for package in downloads_pip:
    
        query_url = f"https://pypi.org/pypi/{package}/json"
        response = requests.get(query_url)
        
        # ensure request succeeds
        if response.status_code == 200:
            data = response.json()
    
        repo_info = {}
        # Section: header =====================================================
        repo_info['package'] = f"{package}"
        repo_info['header'] = f"Info about {package}"
        
        # Section: info =======================================================
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
            # TODO: Add github API pull into here, add content into dict
        except: print(f"pypi call {package} contains missing data on: {key_parent}, {key_child}, {key_grandchild}")
    
        # Section: releases ===================================================
        key_parent = 'info'
        repo_info[key_child] = data.get(key_parent)
    
        # Section: vulnerabilities ============================================
        key_parent = 'vulnerabilities'
        repo_info[key_child] = data.get(key_parent)
        
        # Section: urls =======================================================
        key_parent = 'urls'
        repo_info[key_child] = data.get(key_parent)
     
        # api_results['pypi'] = repo_info
        pypi_results.append(repo_info)
        
    return pypi_results, homepages


def pull_github_content(homepages):
    """loop through each github page to collect metrics"""
    github_results = []
    for homepage in homepages:
        if '://github.com/' in homepage:  # https://github.com/jupyter-widgets/ipywidgets
    
            # parse page before constructing api query url
            owner_repo = homepage.split('://github.com/')[1]  # jupyter-widgets/ipywidgets
            owner = owner_repo.split('/')[0]  # jupyter-widgets
            repo = owner_repo.split('/')[1]  # ipywidgets
            
            query_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(query_url, auth=(github_user, github_token))
            
            # loop through json elements and populate dict
            repo_info = {}
    
            # ensure request succeeds
            if response.status_code == 200:  # success
                data = response.json()
            
                key_parent = "api_url_repo"
                repo_info[key_parent] = query_url
    
                # Section: header =================================================
                repo_info['package'] = f"{repo}"
                repo_info['header'] = f"Info about {repo}"
    
                key_parent = 'description'
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "created_at"
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "updated_at"
                repo_info[key_parent] = data.get(key_parent)
                
                # watcher count
                key_parent = "subscribers_count"
                repo_info[key_parent] = data.get(key_parent)
    
                # user show of support            
                key_parent = "stargazers_count"  
                repo_info[key_parent] = data.get(key_parent)
                
    			# open_issues_count = issues + pull requests
                key_parent = "has_issues"
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "open_issues_count"
                repo_info[key_parent] = data.get(key_parent)
                
                key_parent = "open_issues"  # repeat?
                repo_info[key_parent] = data.get(key_parent)
    			
                key_parent = "has_projects"
                repo_info[key_parent] = data.get(key_parent)
                
                key_parent = "has_downloads"
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "has_wiki"
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "allow_forking"
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "fork"
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "forks_count"
                repo_info[key_parent] = data.get(key_parent)
    
                key_parent = "forks"  # repeat?
                repo_info[key_parent] = data.get(key_parent)
                
                # get the total count of commits from commits endpoint
                # API limits commit count return to 30
                query_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
                response = requests.get(query_url, auth=(github_user, github_token))
                if response.status_code == 200:  # success
                    data = response.json()
                    
                    commit_count = 0
                    for each in data:
                        for k in each.keys():  # dont need values() or items()
                            if k == "commit":
                                commit_count += 1
    
                    key_parent = "api_url_commit"
                    repo_info[key_parent] = query_url
    
                    key_parent = "commits_max_30"
                    repo_info[key_parent] = commit_count
    
            github_results.append(repo_info)
            # print(json.dumps(repo_info))

    return github_results


pypi_results, homepages = pull_pypi_content(downloads_pip)
github_results = pull_github_content(homepages)

# %%

# scrape anaconda
# https://api.anaconda.org/docs

# %%

# calc repo health
