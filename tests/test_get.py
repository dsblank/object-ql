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
from gramps.gen.lib import Note, Person, PersonRef

from pythonish_ql import PythonishQuery


@pytest.fixture
def db():
    """Return Gramps Database."""
    TEST_GRAMPSHOME = tempfile.mkdtemp()
    os.environ["GRAMPSHOME"] = TEST_GRAMPSHOME
    dbman = CLIDbManager(DbState())
    path, name = dbman.create_new_db_cli("PythonishQL Test", dbid="sqlite")
    db = make_database("sqlite")
    db.load(path)
    with DbTxn("Add test objects", db) as trans:
        # person001
        person = Person()
        person.set_gramps_id("person001")
        person.set_handle("handle001")
        db.add_person(person, trans)

        # note003
        note = Note()
        note.set_gramps_id("note003")
        note.set_handle("handle003")
        db.add_note(note, trans)

        # person002
        person = Person()
        person.set_gramps_id("person002")
        person.set_handle("handle002")
        person_ref = PersonRef()
        person_ref.set_reference_handle("handle001")
        person.add_person_ref(person_ref)
        person.add_note("handle003")
        db.add_person(person, trans)

    yield db
    db.close()
    shutil.rmtree(TEST_GRAMPSHOME)


def test_fixture(db):
    assert isinstance(db, DbReadBase)


def test_get_person(db):
    q = PythonishQuery("'handle001' in [x['ref'] for x in {'person_ref_list'}]", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_person_0(db):
    q = PythonishQuery("any([get_person(x['ref'])['gramps_id'] == 'person001' for x in {'person_ref_list'}])", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_person_1(db):
    q = PythonishQuery("[get_person('handle001') for x in {'person_ref_list'}]", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_person_2(db):
    q = PythonishQuery("any([get_person(x['ref'])['gramps_id'] == 'person001' for x in {'person_ref_list'}])", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_note(db):
    q = PythonishQuery("'handle003' in {'note_list'} and {'gramps_id'} == 'person002'", db=db)
    assert len(list(q.iter_objects())) == 1
    q = PythonishQuery("any([get_note(ref)['gramps_id'] == 'note003' for ref in {'note_list'}])", db=db)
    assert len(list(q.iter_objects())) == 1


def test_get_note_0(db):
    q = PythonishQuery("any([get_note(ref) for ref in {'note_list'}])", db=db)
    assert len(list(q.iter_objects())) == 1

# Enhancements

def test_get_person_from_ref_list(db):
    q = PythonishQuery("any([get_person(ref)['gramps_id'] == 'person001' for ref in {'person_ref_list'}])", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_person_from_top_level(db):
    q = PythonishQuery("get_person()['gramps_id'] == 'person001'", db=db)
    assert len(list(q.iter_objects())) == 1

