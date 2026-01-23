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


ItemType = type[BaseModel | Enum]


class GraphNode:
    def __init__(self, model: ItemType):
        self.model = model
        self.children: set[GraphNode] = set()

    def add_child(self, child: Self):
        self.children.add(child)

    def remove_child(self, child: Self):
        if child in self.children:
            self.children.remove(child)

    def __repr__(self):
        return f"GraphNode({self.model.__name__}) -> {self.children}"


class WrittenGraphNode(GraphNode):
    def __init__(self, base: GraphNode, file_path: Path):
        super().__init__(base.model)
        self.file_path = file_path

    def __repr__(self):
        return f"WrittenGraphNode({self.model.__name__}) -> {self.file_path}"


def extract_from_anno(tp: type[Any] | None) -> set[ItemType]:
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


def extract_child_models(model: ItemType):
    """Get all child models for a model"""
    if not issubclass(model, BaseModel):
        return set()
    result = set()
    for _, info in (model.model_fields).items():
        result |= extract_from_anno(info.annotation)
    for _, info in (model.model_computed_fields).items():
        result |= extract_from_anno(info.return_type)
    return result


class ModelGraphManager:
    def __init__(self, models: Iterable[type[BaseModel]]):
        self.nodes: dict[ItemType, GraphNode] = {}
        for model in models:
            self._process_model(model)
        self.written_nodes: dict[ItemType, WrittenGraphNode] = {}

    def get_node(self, model: ItemType) -> GraphNode:
        if model not in self.nodes:
            self.nodes[model] = GraphNode(model)
        return self.nodes[model]

    def _process_model(self, model: type[BaseModel]):
        parent_node = self.get_node(model)

        for ref_model in extract_child_models(model):
            child_node = self.get_node(ref_model)
            parent_node.add_child(child_node)

    def leaves(self) -> set[GraphNode]:
        return set(node for node in self.nodes.values() if node.children == set())

    def set_node_written(self, node: GraphNode, path: Path):
        _node = self.nodes.pop(node.model)
        self.written_nodes[node.model] = WrittenGraphNode(_node, path)

    def remove_from_all_parents(self, node: GraphNode):
        for potential_parent in self.nodes.values():
            potential_parent.remove_child(node)
        self.nodes.pop(node.model, None)

    def process_generation(self):
        for node in self.leaves():
            self.set_node_written(node, Path(f"./schema/{node.model.__name__}.json"))
            self.remove_from_all_parents(node)

    def print_state(self):
        print("\nUnwritten nodes:")
        for node in self.nodes.values():
            print(f"    {node}")
        print("\nWritten nodes:")
        for node in self.written_nodes.values():
            print(f"    {node}")


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
            schema = cls.model_json_schema(mode="serialization")
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
    "print a graph of the relationships of the models and in what order they will be processed"
    clss = list(_get_model_classes())
    for cls in clss:
        cls.model_rebuild()
    dag = ModelGraphManager(clss)

    dag.print_state()

    i = 0
    while len(dag.nodes) > 0:
        print(f"\nGeneration {i} leaves:")
        for leaf in dag.leaves():
            print(f"    {leaf}")
        dag.process_generation()
        dag.print_state()
        i += 1


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
