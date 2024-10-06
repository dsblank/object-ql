# -*- coding: utf-8 -*-
# **************************************************************
# Pythonish Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

import os
import shutil
import tempfile

import pytest
from gramps.cli.clidbman import CLIDbManager
from gramps.gen.db import DbReadBase, DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Person

from pythonish_ql import PythonishQuery


@pytest.fixture
def db():
    """Return Gramps Database."""
    TEST_GRAMPSHOME = tempfile.mkdtemp()
    os.environ["GRAMPSHOME"] = TEST_GRAMPSHOME
    dbman = CLIDbManager(DbState())
    path, name = dbman.create_new_db_cli("GQL Test", dbid="sqlite")
    db = make_database("sqlite")
    db.load(path)
    person = Person()
    person.gramps_id = "person001"
    with DbTxn("Add test objects", db) as trans:
        db.add_person(person, trans)
    yield db
    db.close()
    shutil.rmtree(TEST_GRAMPSHOME)


def test_fixture(db):
    assert isinstance(db, DbReadBase)


def test_person_gramps_id(db):
    q = PythonishQuery("person", db=db)
    assert len(list(q.iter_objects())) == 1
    for obj in q.iter_objects():
        assert isinstance(obj, Person)
    q = PythonishQuery("""person.gramps_id == "person001" """, db=db)
    assert len(list(q.iter_objects())) == 1
    q = PythonishQuery("""person.gramps_id != "person001" """, db=db)
    assert len(list(q.iter_objects())) == 0
    q = PythonishQuery("""person.gramps_id == "person002" """, db=db)
    assert len(list(q.iter_objects())) == 0
    q = PythonishQuery("""person.gramps_id > "person002" """, db=db)
    assert len(list(q.iter_objects())) == 0
    q = PythonishQuery("""person.gramps_id < "person002" """, db=db)
    assert len(list(q.iter_objects())) == 1
