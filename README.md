# Repo health

This module checks the health of any imported packages found in a subdirectory of modules.

It ignore builtins and standard library packages.

You input the directory `./input_py`, which contains .py modules, and it performs API requests to return information about all imported packages, such as days since creation, days since last update, number of followers, number of pull requests + outstanding issues, number of stackoverflow tags, etc.

## Standard Library

When you first download python, it comes with a Standard Library for greater functionality ("batteries included"). Because loading the entire Standard Library would require more memory, python's creators made the design decision to only load certain ones. These are called `builtins`, and you don't need to import them at the top of your scripts. 

`print(dir(__builtins__))`

The other Standard Library content does need to be imported. While there is a lot of discussion about programmatically finding non-builtin libraries online, I've not found a clean way to access the list across various system configurations. On my Windows system, it can be done via:

```python
standard_lib_path = os.path.join(sys.prefix, "Lib")
    for file in os.listdir(standard_lib_path):
        standard_libs.append(file.split(".py")[0].strip().lower())
```

## Package managers, repos

Going from memory...

When using base python, you handle package management with pip, which feeds off pypi repo. Packages downloaded here are source files (uncompiled code). Meanwhile, virtual environments are handled with venv.

`pip install mypackage`

`python -m venv myenv`

Anaconda added both package management and virtual environment commands into conda. 

`conda install mypackage`

`conda create --name myenv python=3.7 anaconda`

Conda install feeds off Anaconda repo. Packages downloaded here are binaries (compiled code). Additionally, Anaconda is a distribution which also supports for R and other languages, so not all compiled binaries are python compatible.

## pip or conda

If you're using Anaconda distribution, then you should always `conda install`. If the package isn't available, then fallback on `pip install`.

If is to be expected that if you `pip list` and `conda list`, you'll see overlap. Not a cause for worry.

## Wheels

As an aside, adding wheels to a package speeds the installation. I think of putting wheels on a cardboard box to make it deliver faster.

As far as I understand, wheels need to be created for 32-bit, 64-bit processors, perhaps ARM, different python versions, and other factors. As such, they're not always added.

When you go to install a package without wheels, you'll see about 3 (slow) processing steps that wouldn't otherwise be required.

## Library, package, module

As an additional aside, what is the difference between libraries, packages and modules?

Module = any document with a `.py` file extension

Package = collection of modules containing an `__init__.py` file

Library = collection of modules

Framework = Kind of like complex libraries. Also a collection of modules designed to help you speed development. They contain a basic flow and architecture of an application.

[Source](https://learnpython.com/blog/python-modules-packages-libraries-frameworks/#:~:text=Python%20Libraries&text=Actually%2C%20this%20term%20is%20often,is%20a%20collection%20of%20packages.) 

## Improvements

Add support for R repo, CRAN.
