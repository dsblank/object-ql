# -*- coding: utf-8 -*-
# **************************************************************
# Python Query Language, for Gramps and others
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

from python_ql import PythonQuery


@pytest.fixture
def db():
    """Return Gramps Database."""
    TEST_GRAMPSHOME = tempfile.mkdtemp()
    os.environ["GRAMPSHOME"] = TEST_GRAMPSHOME
    dbman = CLIDbManager(DbState())
    path, name = dbman.create_new_db_cli("PythonQL Test", dbid="sqlite")
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
    q = PythonQuery("'handle001' in [get_person(ref).get_handle() for ref in person.get_person_ref_list()]", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_person_0(db):
    q = PythonQuery("[get_person(ref).gramps_id == 'person001' for ref in person.get_person_ref_list()]", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_person_1(db):
    q = PythonQuery("[get_person('handle001') for ref in person.get_person_ref_list()]", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_person_2(db):
    q = PythonQuery("any([get_person(x).gramps_id == 'person001' for x in person.get_person_ref_list()])", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_note(db):
    q = PythonQuery("'handle003' in person.get_note_list() and person.gramps_id == 'person002'", db=db)
    assert len(list(q.iter_objects())) == 1
    q = PythonQuery("any([get_note(ref).gramps_id == 'note003' for ref in person.get_note_list()])", db=db)
    assert len(list(q.iter_objects())) == 1

def test_get_note_0(db):
    q = PythonQuery("any([get_note(ref) for ref in person.get_note_list()])", db=db)
    assert len(list(q.iter_objects())) == 1

