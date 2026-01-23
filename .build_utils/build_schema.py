import argparse
from enum import Enum
import inspect
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Self, get_args, get_origin
import bec_messages
import bec_messages.messages
from pydantic import BaseModel


def _get_model_classes() -> Iterable[type[BaseModel]]:
    """Get all the relevant classes from the message definitions."""
    return (
        cls
        for cls in bec_messages.messages.__dict__.values()
        if issubclass(cls, BaseModel)
        and cls is not BaseModel
        and not cls.__name__.startswith("_")
    )


ItemType = BaseModel | Enum


class GraphNode:
    def __init__(self, model: type[ItemType]):
        self.model = model
        self.children: set[GraphNode] = set()

    def add_child(self, child: Self):
        self.children.add(child)

    def __repr__(self):
        return f"GraphNode({self.model.__name__})"


def extract_from_anno(tp: type[Any] | None) -> set[type[ItemType]]:
    """Return all the BaseModel subclasses in an annotation."""
    if tp is None:
        return set()
    if inspect.isclass(tp) and issubclass(tp, get_args(ItemType)):
        return {tp}

    args = get_args(tp)
    result = set()
    for arg in args:
        result |= extract_from_anno(arg)
    return result


def extract_child_models(model: type[ItemType]):
    """Get all child models for a model"""
    if not issubclass(model, BaseModel):
        return set()
    result = set()
    for _, info in model.model_fields.items():
        result |= extract_from_anno(info.annotation)


class ModelGraph:
    def __init__(self, models: Iterable[type[BaseModel]]):
        self.nodes: dict[type[ItemType], GraphNode] = {}
        for model in models:
            self._process_model(model)

    def get_node(self, model: type[ItemType]) -> GraphNode:
        if model not in self.nodes:
            self.nodes[model] = GraphNode(model)
        return self.nodes[model]

    def _process_model(self, model: type[BaseModel]):
        parent_node = self.get_node(model)

        for field in model.model_fields.values():
            referenced_models = extract_from_anno(field.annotation)

            for ref_model in referenced_models:
                child_node = self.get_node(ref_model)
                parent_node.add_child(child_node)

    def roots(self) -> set[GraphNode]:
        all_children = {
            child for node in self.nodes.values() for child in node.children
        }
        return set(self.nodes.values()) - all_children


def _json_schema_dir():
    return Path(__file__).parent.resolve() / "../json_schema"


def _list_all_schema_files():
    return (f for f in os.listdir(_json_schema_dir()) if f != "README.md")


def _remove_all():
    for f in _list_all_schema_files():
        os.remove(_json_schema_dir() / f)


def _write_schema_file(cls: type[BaseModel]):
    with open(_json_schema_dir() / f"{cls.__name__}.json", "w") as f:
        try:
            schema = cls.model_json_schema()
        except Exception as e:
            raise TypeError(f"Schema generation for {cls} failed") from e
        f.write(f"{json.dumps(schema, indent=2)}\n")


def _write_schema_files(classes: Iterable[type[BaseModel]]):
    for cls in classes:
        _write_schema_file(cls)


def _rebuild():
    """Rebuild the BEC message schema."""
    _remove_all()
    _write_schema_files(_get_model_classes())


def _check():
    """Check that the contents of the built schema would be unchanged by a rebuild"""


def _display_graph():
    "print a graph of the relationships of the models"
    clss = list(_get_model_classes())
    for cls in clss:
        cls.model_rebuild()
    dag = ModelGraph(clss)
    for node in dag.nodes.values():
        print(node, "->", node.children)


Actions = Literal["check", "rebuild", "display"]

SUBCOMMANDS: dict[Actions, Callable] = {
    "check": _check,
    "rebuild": _rebuild,
    "display": _display_graph,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=list(SUBCOMMANDS.keys()))
    args = parser.parse_args()
    SUBCOMMANDS[args.action]()
