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

def get_attr(obj, attr):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif isinstance(obj, dict):
        if attr in obj:
            return obj[attr]

class PythonishTransformer(ast.NodeTransformer):
    def visit_Set(self, node):
        expr = ast.parse("row['%s']" % node.elts[0].value)
        return expr.body[0].value

    def visit_Attribute(self, node):
        value = self.visit(node.value)
        function = ast.parse("get_attr")
        #node.Name(node.attr
        return ast.Call(function.body[0].value, [value, ast.Constant(node.attr)], [])

TRANSFORMER = PythonishTransformer()

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


def to_dict(obj: PrimaryObject) -> dict[str, Any]:
    """Convert a Gramps object to its dictionary representation."""
    obj_dict = json.loads(to_json(obj))
    obj_dict["class"] = obj_dict["_class"].lower()
    return obj_dict


def match(
    query: str,
    obj: Union[PrimaryObject, dict[str, Any]],
    db: Optional[DbReadBase] = None,
) -> bool:
    """Match a single object (optionally given as dictionary) to a query."""
    pq = PythonishQuery(query=query, db=db)
    if isinstance(obj, PrimaryObject):
        obj_dict = to_dict(obj)
        return pq.match(obj_dict)
    return pq.match(obj)


def iter_objects(query: str, db: DbReadBase) -> Generator[PrimaryObject, None, None]:
    """Iterate over primary objects in a Gramps database."""
    pq = PythonishQuery(query=query, db=db)
    return pq.iter_objects()

def transform(query: str):
    """Convert query string into a converted ast."""
    try:
        ast_query = ast.parse(query, mode="eval")
        ast.fix_missing_locations(ast_query)
        converted = TRANSFORMER.visit(ast_query)
        ast.fix_missing_locations(converted)
        return converted
    except Exception as exc:
        print("Parse error: %r" % exc)
        return None

def parse(query: str) -> str:
    """Parse a query into a transformed query."""
    converted = transform(query)
    if converted:
        return ast.unparse(converted)
    else:
        return None

def find_handle(obj, method, env):
    """Find the handle in obj, or default to find in row."""
    if isinstance(obj, str):
        return to_dict(method(obj))
    elif isinstance(obj, dict):
        if "handle" in obj:
            return to_dict(method(obj["handle"]))
        elif "ref" in obj:
            return to_dict(method(obj["ref"]))
    elif obj is None:
        return find_handle(env["row"], method, env)
    return None

def make_env(db: DbReadBase, **kwargs) -> dict[str, Any]:
    """Create an environment with useful functions and row."""
    env = {"get_attr": get_attr}
    if db is not None:
        env.update({
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
        converted = transform(query)
        if converted:
            self.code_object = compile(converted, "<query>", mode="eval")


    def match(self, obj: dict[str, Any]) -> bool:
        if self.code_object is None:
            return False

        env = make_env(self.db, row=obj)
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
                obj_dict = to_dict(obj)
                if self.match(obj_dict):
                    yield obj
