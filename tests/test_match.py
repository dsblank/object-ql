# -*- coding: utf-8 -*-
# **************************************************************
# Pythonish Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

from pythonish_ql import match, PythonishQuery

def test_match_1():
    query = "{'Surname'}.startswith('B')"
    q = PythonishQuery(query)
    obj = {"Surname": "Blank"}
    assert q.match(obj)
    assert match(query, obj)
    
    obj = {"Surname": "Smith"}
    assert not q.match(obj)
    assert not match(query, obj)

def test_match():
    query = "{'one'}['two'] == 'x'"
    q = PythonishQuery(query)
    obj = {"one": {"two": "x"}, "three": {"four": ["y"]}}
    assert q.match(obj)
    assert match(query, obj)

def test_match_noop():
    q = PythonishQuery("{'one'}['two']")
    assert q.match({"one": {"two": 1}, "three": {"four": ["y"]}})


def test_match_and():
    q = PythonishQuery("{'one'}['two'] == 'x' and {'three'}['four'][0] == 'y'")
    assert q.match({"one": {"two": "x"}, "three": {"four": ["y"]}})


def test_match_and_or():
    q = PythonishQuery("{'one'}['two'] == 'x' and {'three'}['four'][0] == 'y' or {'five'}")
    assert q.match({"one": {"two": "x"}, "three": {"four": ["y"]}, "five": 1})


def test_length():
    q = PythonishQuery("len({'array'}) == 1")
    assert not q.match({"array": []})
    assert not q.match({"array": [1, 1]})
    assert q.match({"array": [1]})


def test_array_contains():
    q = PythonishQuery("2 in {'array'}")
    assert not q.match({"array": []})
    assert not q.match({"array": [3, 4, 5]})
    assert q.match({"array": [1, 2, 3]})


def test_string_contains():
    q = PythonishQuery("'2' in {'string'}")
    assert not q.match({"string": "abc"})
    assert not q.match({"string": "145"})
    assert q.match({"string": "co2"})


def test_string_contains_case():
    q = PythonishQuery("'a' in {'string'}.lower()")
    assert q.match({"string": "abc"})
    assert q.match({"string": "Abc"})


def test_any():
    q = PythonishQuery("any([2 == x for x in {'array'}])")
    assert not q.match({"array": []})
    assert not q.match({"array": [3, 4, 5]})
    assert q.match({"array": [1, 2, 3]})


def test_any_string():
    q = PythonishQuery("any(['a' in x.values() for x in {'array'}])")
    assert not q.match({"array": []})
    assert not q.match({"array": [{"value": "c"}]})
    assert q.match({"array": [{"value": "b"}, {"value": "a"}]})


def test_any_number():
    q = PythonishQuery("any([3 in x.values() for x in {'array'}])")
    assert not q.match({"array": []})
    assert not q.match({"array": [{"value": 1}]})
    assert q.match({"array": [{"value": 2}, {"value": 3}]})


def test_all():
    q = PythonishQuery("all([2 == x for x in {'array'}]) and {'array'} != []")
    assert not q.match({"array": []})
    assert not q.match({"array": [2, 4, 5]})
    assert q.match({"array": [2, 2, 2]})


def test_all_string():
    q = PythonishQuery("all(['a' in d.values() for d in {'array'}]) and {'array'} != []")
    assert not q.match({"array": []})
    assert not q.match({"array": [{"value": "a"}, {"value": "b"}]})
    assert q.match({"array": [{"value": "a"}, {"value": "a"}]})


def test_all_number():
    q = PythonishQuery("all([3 in d.values() for d in {'array'}]) and {'array'} != []")
    assert not q.match({"array": []})
    assert not q.match({"array": [{"value": 1}, {"value": 3}]})
    assert q.match({"array": [{"value": 3}, {"value": 3}]})
