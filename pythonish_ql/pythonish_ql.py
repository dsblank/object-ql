# -*- coding: utf-8 -*-
# **************************************************************
# Pythonish Query Language, for Gramps and others
#
# Copyright (c) Douglas Blank
# MIT License
#
# Largely based on https://github.com/DavidMStraub/gramps-ql
# **************************************************************

import ast
from collections.abc import Generator
from typing import Any, Optional, Union
import json

from gramps.gen.db import DbReadBase
from gramps.gen.errors import HandleError
from gramps.gen.lib import PrimaryObject
from gramps.gen.lib.serialize import to_json
from gramps.gen.simple import SimpleAccess


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
    pq = PythonishQuery(query=query, db=db)
    return pq.match(obj)


def iter_objects(query: str, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
    """Iterate over primary objects in a Gramps database."""
    pq = PythonishQuery(query=query, db=db)
    return pq.iter_objects()

def apply(query: str, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
    """Iterate over primary objects in a Gramps database."""
    pq = PythonishQuery(query=query, db=db)
    return pq.iter_objects_apply()

def parse_to_ast(query: str):
    """Parse query string into ast."""
    try:
        ast_query = ast.parse(query, mode="eval")
        ast.fix_missing_locations(ast_query)
        return ast_query
    except Exception as exc:
        print("Parse error: %r" % exc)
        return None

def parse(query: str) -> str:
    """Parse a query into ast and return ."""
    parsed_ast = parse_to_ast(query)
    if parsed_ast:
        return ast.unparse(parsed_ast)
    else:
        return None

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

class PythonishQuery():
    def __init__(self, query: str, db: Optional[DbReadBase] = None):
        self.query = query
        self.db = db
        self.code_object = None
        parsed_ast = parse_to_ast(query)
        if parsed_ast:
            self.code_object = compile(parsed_ast, "<query>", mode="eval")


    def match(self, obj: dict[str, Any]) -> bool:
        if self.code_object is None:
            return False

        key = obj.__class__.__name__.lower()
        env = make_env(self.db, **{key: obj, "obj": obj})
        try:
            results = eval(self.code_object, env, {})
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
            iter_method = getattr(self.db, f"iter_{objects_name}")
            for obj in iter_method():
                if self.match(obj):
                    yield obj

    def iter_objects_apply(self) -> Generator[PrimaryObject, None, None]:
        """Iterate over primary objects in a Gramps database."""
        if not self.db:
            raise ValueError("Database is needed for iterating objects!")
        for object_name, objects_name in GRAMPS_OBJECT_NAMES.items():
            iter_method = getattr(self.db, f"iter_{objects_name}")
            for obj in iter_method():
                yield self.match(obj)

