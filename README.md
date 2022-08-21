# Repo health

Check the health of any pypi packages found in .py files in directory 

Ignore builtins and standard library packages.

You input the directory `./sample_scripts`, which contains .py files, and it reads from PyPi and GitHub to return basic repo information, such as days since creation, days since last update, number of followers, number of pull requests + outstanding issues, etc.

## Improvements

Add support for `conda install` libraries. Challenge is to find anaconda API to pull repo info.
