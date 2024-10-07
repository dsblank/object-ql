# -*- coding: utf-8 -*-
# **************************************************************
# Python Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

from python_ql import match, PythonQuery

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
    q = PythonQuery(query)
    obj = Name(surname="Blank")
    assert q.match(obj)
    assert match(query, obj)
    
    obj = Name(surname="Smith")
    assert not q.match(obj)
    assert not match(query, obj)

def test_match():
    query = "one.two == 'x'"
    q = PythonQuery(query)
    obj = One(two="x", three=One(four=["y"]))
    assert q.match(obj)
    assert match(query, obj)

def test_match_noop():
    q = PythonQuery("one.two")
    obj = One(two=1, three=One(four=["y"]))
    assert q.match(obj)

def test_match_and():
    q = PythonQuery("one.two == 'x' and one.three.four[0] == 'y'")
    obj = One(two="x", three=One(four=["y"]))
    assert q.match(obj)


def test_match_and_or():
    q = PythonQuery("one.two == 'x' and one.three.four[0] == 'y' or one.five")
    obj = One(two="x", three=One(four=["y"]), five=1)
    assert q.match(obj)


def test_length():
    q = PythonQuery("len(obj) == 1")
    assert not q.match([])
    assert not q.match([1, 1])
    assert q.match([1])


def test_array_contains():
    q = PythonQuery("2 in obj")
    assert not q.match([])
    assert not q.match([3, 4, 5])
    assert q.match([1, 2, 3])


def test_string_contains():
    q = PythonQuery("'2' in obj")
    assert not q.match("abc")
    assert not q.match("145")
    assert q.match("co2")


def test_string_contains_case():
    q = PythonQuery("'a' in obj.lower()")
    assert q.match("abc")
    assert q.match("Abc")


def test_any():
    q = PythonQuery("any([2 == x for x in obj])")
    assert not q.match([])
    assert not q.match([3, 4, 5])
    assert q.match([1, 2, 3])


def test_any_string():
    q = PythonQuery("any(['a' in x.values() for x in obj])")
    assert not q.match([])
    assert not q.match([{"value": "c"}])
    assert q.match([{"value": "b"}, {"value": "a"}])


def test_any_number():
    q = PythonQuery("any([3 in x.values() for x in obj])")
    assert not q.match([])
    assert not q.match([{"value": 1}])
    assert q.match([{"value": 2}, {"value": 3}])


def test_all():
    q = PythonQuery("all([2 == x for x in obj]) and obj != []")
    assert not q.match([])
    assert not q.match([2, 4, 5])
    assert q.match([2, 2, 2])


def test_all_string():
    q = PythonQuery("all(['a' in d.values() for d in obj]) and obj != []")
    assert not q.match([])
    assert not q.match([{"value": "a"}, {"value": "b"}])
    assert q.match([{"value": "a"}, {"value": "a"}])


def test_all_number():
    q = PythonQuery("all([3 in d.values() for d in obj]) and obj != []")
    assert not q.match([])
    assert not q.match([{"value": 1}, {"value": 3}])
    assert q.match([{"value": 3}, {"value": 3}])

