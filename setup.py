# -*- coding: utf-8 -*-
# **************************************************************
# Python Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

import io
import os

import setuptools

HERE = os.path.abspath(os.path.dirname(__file__))


def get_version(file, name="__version__"):
    """
    Get the version of the package from the given file by
    executing it and extracting the given `name`.
    """
    path = os.path.realpath(file)
    version_ns = {}
    with io.open(path, encoding="utf8") as f:
        exec(f.read(), {}, version_ns)
    return version_ns[name]


__version__ = get_version(os.path.join(HERE, "python_ql/_version.py"))

with io.open(os.path.join(HERE, "README.md"), encoding="utf8") as fh:
    long_description = fh.read()

setup_args = dict(
    name="python-ql",
    version=__version__,
    url="https://github.com/dsblank/python-ql",
    author="Doug Blank",
    description="Python query language for dictionary-like data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "gramps",
    ],
    packages=[
        "python_ql",
    ],
    include_package_data=True,
    python_requires=">=3.8",
    license="MIT License",
    platforms="Linux, Mac OS X, Windows",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)

if __name__ == "__main__":
    setuptools.setup(**setup_args)
