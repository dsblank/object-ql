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

class PythonishTransformer(ast.NodeTransformer):
    def visit_Set(self, node):
        expr = ast.parse("row['%s']" % node.elts[0].value)
        return expr.body[0].value

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
        print(exc)
        return None

def parse(query: str) -> str:
    """Parse a query into a transformed query."""
    converted = transform(query)
    if converted:
        return ast.unparse(converted)
    else:
        return None

def make_env(db: DbReadBase, **kwargs) -> dict[str, Any]:
    """Create an environment with useful functions and row."""
    if db is None:
        env = {}
    else:
        env = {
            "get_person": lambda handle: to_dict(db.get_person_from_handle(handle)),
            "get_note": lambda handle: to_dict(db.get_note_from_handle(handle)),
            "get_family": lambda handle: to_dict(db.get_family_from_handle(handle)),
            "get_event": lambda handle: to_dict(db.get_event_from_handle(handle)),
            "get_media": lambda handle: to_dict(db.get_media_from_handle(handle)),
            "get_place": lambda handle: to_dict(db.get_place_from_handle(handle)),
            "get_tag": lambda handle: to_dict(db.get_tag_from_handle(handle)),
            "get_source": lambda handle: to_dict(db.get_source_from_handle(handle)),
            "get_citation": lambda handle: to_dict(db.get_citation_from_handle(handle)),
            "get_repository": lambda handle: to_dict(db.get_repository_from_handle(handle)),
        }
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
            print(obj)
            print(esc)
            results = False
            print(results)
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
