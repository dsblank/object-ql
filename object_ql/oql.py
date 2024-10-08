# -*- coding: utf-8 -*-
# **************************************************************
# Object Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

from __future__ import annotations  # can be removed at 3.8 EOL

import ast
from collections.abc import Generator
from typing import Any, Optional, Union
import json
import signal
from pyparsing.exceptions import ParseFatalException

from gramps.gen.db import DbReadBase
from gramps.gen.errors import HandleError
from gramps.gen.lib import (
    PrimaryObject,
    Person,
    SourceMediaType,
    RepositoryType,
    PlaceType,
    NoteType,
    NameType,
    NameOriginType,
    MarkerType,
    LdsOrd,
    FamilyRelType,
    EventType,
    EventRoleType,
    Citation,
    ChildRefType,
    AttributeType
)
from gramps.gen.lib.serialize import to_json
from gramps.gen.simple import SimpleAccess

EXPRESSION_TIMEOUT = 1  # integer seconds to timeout on eval per expression
GRAMPS_OBJECT_NAMES = {
    "person": "people",
    "family": "families",
    "event": "events",
    "place": "places",
    "citation": "citations",
    "source": "sources",
    "repository": "repositories",
    "media": "media",
    "note": "notes",
}


def match(
    query: str,
    obj: Union[PrimaryObject, dict[str, Any]],
    db: Optional[DbReadBase] = None,
) -> bool:
    """Match a single object (optionally given as dictionary) to a query."""
    pq = ObjectQuery(query=query, db=db)
    return pq.match(obj)


def iter_objects(query: str, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
    """Iterate over primary objects in a Gramps database."""
    pq = ObjectQuery(query=query, db=db)
    return pq.iter_objects()

def apply(query: str, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
    """Iterate over primary objects in a Gramps database."""
    pq = ObjectQuery(query=query, db=db)
    return pq.iter_objects_apply()

def get_tables(query: str):
    """Get the tables mentioned in a query"""
    ast_query = parse_to_ast(query.strip())
    visitor = VariableVisitor()
    visitor.visit(ast_query)
    result = list((visitor.used_variables - visitor.assigned_variables) &
                  set(GRAMPS_OBJECT_NAMES.keys()))
    if result:
        return result
    else:
        return list(GRAMPS_OBJECT_NAMES.keys())

def parse_to_ast(query: str):
    """Parse query string into ast."""
    try:
        ast_query = ast.parse(query.strip(), mode="eval")
    except Exception as exc:
        raise ParseFatalException(exc.msg, exc.offset) from None

    ast.fix_missing_locations(ast_query)
    # Will raise if violation:
    visitor = RestrictedVisitor()
    visitor.visit(ast_query)
    return ast_query

def parse(query: str) -> str:
    """Parse a query into ast and return ."""
    parsed_ast = parse_to_ast(query.strip())
    return ast.unparse(parsed_ast)

def find_handle(obj, method, env):
    """Find the handle in obj, or default to find in row."""
    if isinstance(obj, str):
        return method(obj)
    elif isinstance(obj, dict):
        if "handle" in obj:
            return method(obj["handle"])
        elif "ref" in obj:
            return method(obj["ref"])
    elif hasattr(obj, "ref"):
        return method(obj.ref)
    return None

def make_env(db: DbReadBase, **kwargs) -> dict[str, Any]:
    """Create an environment with useful functions and self."""
    env = {}
    # For constants, like Person.MALE
    for primary_obj in [
            Person, SourceMediaType, RepositoryType, PlaceType, NoteType, NameType,
            NameOriginType, MarkerType, LdsOrd, FamilyRelType, EventType, EventRoleType,
            Citation, ChildRefType, AttributeType,
    ]:
        env[primary_obj.__name__] = primary_obj
    if db is not None:
        env.update({
            "sa": SimpleAccess(db),
            "get_person": lambda obj=None: find_handle(obj, db.get_person_from_handle, env),
            "get_note": lambda obj=None: find_handle(obj, db.get_note_from_handle, env),
            "get_family": lambda obj=None: find_handle(obj, db.get_family_from_handle, env),
            "get_event": lambda obj=None: find_handle(obj, db.get_event_from_handle, env),
            "get_media": lambda obj=None: find_handle(obj, db.get_media_from_handle, env),
            "get_place": lambda obj=None: find_handle(obj, db.get_place_from_handle, env),
            "get_tag": lambda obj=None: find_handle(obj, db.get_tag_from_handle, env),
            "get_source": lambda obj=None: find_handle(obj, db.get_source_from_handle, env),
            "get_citation": lambda obj=None: find_handle(obj, db.get_citation_from_handle, env),
            "get_repository": lambda obj=None: find_handle(obj, db.get_repository_from_handle, env),
        })
    env.update(kwargs)
    return env

def alarm_handler(signum, frame):
    raise TimeoutExpired

def eval_with_timeout(code_object, global_env, local_env, timeout):
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)
    did_timeout = False

    try:
        result = eval(code_object, global_env, local_env)
    except TimeoutExpired:
        did_timeout = True
        result = False
    finally:
        signal.alarm(0)

    return result, did_timeout

class RestrictedVisitor(ast.NodeVisitor):
    def visit_Name(self, node):
        if ((node.id != "_") and
            ((node.id in [
                "eval", "exec", "input", "getattr", "setattr", "vars", "print",
                "globals", "locals", "delattr", "raise",
            ]) or
             (node.id.startswith("_")))):

            raise ValueError("Access denied to %r" % node.id)

        self.generic_visit(node)

    def visit_Attribute(self, node):
        if (node.attr.startswith("_")):

            raise ValueError("Access denied to %r" % node.attr)

        self.generic_visit(node)
        
class VariableVisitor(ast.NodeVisitor):
    def __init__(self):
        self.used_variables = set()
        self.assigned_variables = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_variables.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.assigned_variables.add(node.id)

class TimeoutExpired(Exception):
    pass

class ObjectQuery():
    def __init__(self, query: str, db: Optional[DbReadBase] = None):
        self.query = query.strip()
        self.db = db
        self.code_object = None
        parsed_ast = parse_to_ast(self.query)
        self.tables = get_tables(self.query)
        self.code_object = compile(parsed_ast, "<query>", mode="eval")

    def match(self, obj: dict[str, Any]) -> bool:
        if self.code_object is None:
            return False

        key = obj.__class__.__name__.lower()
        env = make_env(self.db, **{key: obj, "obj": obj})
        try:
            results, did_timeout = eval_with_timeout(
                self.code_object,
                env,
                {},
                EXPRESSION_TIMEOUT,
            )
        except Exception as esc:
            results = False
            #print(obj)
            #print("Parse mismatch: %r" % esc)
            #print(results)
        return results

    def iter_objects(self) -> Generator[PrimaryObject, None, None]:
        """Iterate over primary objects in a Gramps database."""
        if not self.db:
            raise ValueError("Database is needed for iterating objects!")
        for object_name, objects_name in GRAMPS_OBJECT_NAMES.items():
            if object_name not in self.tables:
                continue
            iter_method = getattr(self.db, f"iter_{objects_name}")
            for obj in iter_method():
                if self.match(obj):
                    yield obj

    def iter_objects_apply(self) -> Generator[PrimaryObject, None, None]:
        """Iterate over primary objects in a Gramps database."""
        if not self.db:
            raise ValueError("Database is needed for iterating objects!")
        for object_name, objects_name in GRAMPS_OBJECT_NAMES.items():
            if object_name not in self.tables:
                continue
            iter_method = getattr(self.db, f"iter_{objects_name}")
            for obj in iter_method():
                yield self.match(obj)

