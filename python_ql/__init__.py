# -*- coding: utf-8 -*-
# **************************************************************
# Python Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

from __future__ import annotations  # can be removed at 3.8 EOL

from .pql import (
    PythonQuery,
    apply,
    iter_objects,
    match,
    parse,
)
