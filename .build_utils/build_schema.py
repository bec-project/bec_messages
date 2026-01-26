import argparse
import inspect
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Self, get_args, get_origin

import bec_messages.messages
from pydantic import BaseModel, create_model

import bec_messages

JSON_SCHEMA_DIR = Path(__file__).parent.resolve() / "../json_schema"


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

    def written_node_names(self):
        return (node.__name__ for node in self.written_nodes)

    def remove_from_all_parents(self, node: GraphNode):
        for potential_parent in self.nodes.values():
            potential_parent.remove_child(node)
        self.nodes.pop(node.model, None)

    def process_generation(self, mode: Literal["display", "rebuild"] = "display"):
        for node in self.leaves():
            filename = (
                self._write_schema_file(node.model)
                if mode == "rebuild"
                else Path(f"./<schema_dir>/{node.model.__name__}.json")
            )

            self.set_node_written(node, filename)
            self.remove_from_all_parents(node)

    def _write_enum_schema(self, cls: type[Enum], filename: Path):
        TmpEnumModel = create_model("TmpEnumModel", enum_field=cls)
        schema = TmpEnumModel.model_json_schema(mode="serialization")
        with open(filename, "w") as f:
            f.write(f"{json.dumps(schema["$defs"], indent=2)}\n")
        return filename

    def _write_schema_file(self, cls: ItemType) -> Path:
        filename = JSON_SCHEMA_DIR / f"{cls.__name__}.json"
        if issubclass(cls, Enum):
            return self._write_enum_schema(cls, filename)
        with open(filename, "w") as f:
            try:
                schema = cls.model_json_schema(mode="serialization")
            except Exception as e:
                raise TypeError(f"Schema generation for {cls} failed") from e
            self.link_schema(schema)
            f.write(f"{json.dumps(schema, indent=2)}\n")
        return filename

    def link_schema(self, schema: dict[str, dict]):
        defs = schema.pop("$defs", None)
        if defs is not None:
            for defn in defs.keys():
                assert defn in list(
                    self.written_node_names()
                ), f"No written schema for def: {defn}!"
                for prop in schema["properties"]:
                    if "$ref" in schema["properties"][prop] and schema["properties"][
                        prop
                    ]["$ref"].endswith(defn):
                        schema["properties"][prop]["$ref"] = f"{defn}.json"

    def print_state(self):
        print("\nUnwritten nodes:")
        for node in self.nodes.values():
            print(f"    {node}")
        print("\nWritten nodes:")
        for node in self.written_nodes.values():
            print(f"    {node}")


def _list_all_schema_files():
    return (f for f in os.listdir(JSON_SCHEMA_DIR) if f != "README.md")


def _remove_all_schema_files():
    for f in _list_all_schema_files():
        os.remove(JSON_SCHEMA_DIR / f)


def _rebuild():
    """Rebuild the BEC message schema."""
    _remove_all_schema_files()
    clss = list(_get_model_classes())
    for cls in clss:
        cls.model_rebuild()
    dag = ModelGraphManager(clss)

    i = 0
    while len(dag.nodes) > 0:
        print(f"\n----------------------------------------------------------\n")
        print(f"\nGeneration {i} leaves:")
        for leaf in dag.leaves():
            print(f"    {leaf}")
        dag.process_generation(mode="rebuild")
        dag.print_state()
        i += 1


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
        print(f"\n----------------------------------------------------------\n")
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
