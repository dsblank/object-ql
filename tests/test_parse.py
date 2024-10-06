# -*- coding: utf-8 -*-
# **************************************************************
# Pythonish Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

from pythonish_ql import parse


def test_single():
    assert parse("{'class'}=='person'") == "row['class'] == 'person'"


def test_two():
    assert parse("{'class'} == 'person' or {'date'}['year'] > 2021") == "row['class'] == 'person' or row['date']['year'] > 2021"


def test_three():
    assert parse("{'class'}=='person' or {'name'}=='John Doe' and {'date'}['year'] > 2021") == "row['class'] == 'person' or (row['name'] == 'John Doe' and row['date']['year'] > 2021)"
    assert parse("{'class'}=='person' and {'name'}=='John Doe' or {'date'}['year'] > 2021") == "row['class'] == 'person' and row['name'] == 'John Doe' or row['date']['year'] > 2021"
    assert parse("{'class'}=='person' and {'name'}=='John Doe' or 'only_id'") == "row['class'] == 'person' and row['name'] == 'John Doe' or 'only_id'"


def test_brackets():
    assert parse(
        "({'class'}=='person' or {'name'}=='John Doe') and {'date'}['year'] > 2021"
    ) == "(row['class'] == 'person' or row['name'] == 'John Doe') and row['date']['year'] > 2021"
    assert parse(
        "((((((((((({'class'}=='person' or {'name'}=='John Doe')))) and {'date'}['year'] > 2021)))))))"
    ) == "(row['class'] == 'person' or row['name'] == 'John Doe') and row['date']['year'] > 2021"

# Extensions:

def test_attribute():
    assert parse("{'date'}.year > 2021") == "get_attr(row['date'], 'year') > 2021"
