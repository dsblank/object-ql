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

class Name:
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

class One:
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
    
def test_match_1():
    query = "name.surname.startswith('B')"
    q = PythonishQuery(query)
    obj = Name(surname="Blank")
    assert q.match(obj)
    assert match(query, obj)
    
    obj = Name(surname="Smith")
    assert not q.match(obj)
    assert not match(query, obj)

def test_match():
    query = "one.two == 'x'"
    q = PythonishQuery(query)
    obj = One(two="x", three=One(four=["y"]))
    assert q.match(obj)
    assert match(query, obj)

def test_match_noop():
    q = PythonishQuery("one.two")
    obj = One(two=1, three=One(four=["y"]))
    assert q.match(obj)

def test_match_and():
    q = PythonishQuery("one.two == 'x' and one.three.four[0] == 'y'")
    obj = One(two="x", three=One(four=["y"]))
    assert q.match(obj)


def test_match_and_or():
    q = PythonishQuery("one.two == 'x' and one.three.four[0] == 'y' or one.five")
    obj = One(two="x", three=One(four=["y"]), five=1)
    assert q.match(obj)


def test_length():
    q = PythonishQuery("len(obj) == 1")
    assert not q.match([])
    assert not q.match([1, 1])
    assert q.match([1])


def test_array_contains():
    q = PythonishQuery("2 in obj")
    assert not q.match([])
    assert not q.match([3, 4, 5])
    assert q.match([1, 2, 3])


def test_string_contains():
    q = PythonishQuery("'2' in obj")
    assert not q.match("abc")
    assert not q.match("145")
    assert q.match("co2")


def test_string_contains_case():
    q = PythonishQuery("'a' in obj.lower()")
    assert q.match("abc")
    assert q.match("Abc")


def test_any():
    q = PythonishQuery("any([2 == x for x in obj])")
    assert not q.match([])
    assert not q.match([3, 4, 5])
    assert q.match([1, 2, 3])


def test_any_string():
    q = PythonishQuery("any(['a' in x.values() for x in obj])")
    assert not q.match([])
    assert not q.match([{"value": "c"}])
    assert q.match([{"value": "b"}, {"value": "a"}])


def test_any_number():
    q = PythonishQuery("any([3 in x.values() for x in obj])")
    assert not q.match([])
    assert not q.match([{"value": 1}])
    assert q.match([{"value": 2}, {"value": 3}])


def test_all():
    q = PythonishQuery("all([2 == x for x in obj]) and obj != []")
    assert not q.match([])
    assert not q.match([2, 4, 5])
    assert q.match([2, 2, 2])


def test_all_string():
    q = PythonishQuery("all(['a' in d.values() for d in obj]) and obj != []")
    assert not q.match([])
    assert not q.match([{"value": "a"}, {"value": "b"}])
    assert q.match([{"value": "a"}, {"value": "a"}])


def test_all_number():
    q = PythonishQuery("all([3 in d.values() for d in obj]) and obj != []")
    assert not q.match([])
    assert not q.match([{"value": 1}, {"value": 3}])
    assert q.match([{"value": 3}, {"value": 3}])

