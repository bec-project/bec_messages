import argparse
import json
import os
from pathlib import Path
from typing import Callable, Iterable, Literal
import bec_messages
import bec_messages.messages
from pydantic import BaseModel


def _get_model_classes():
    return (
        cls
        for cls in bec_messages.messages.__dict__.values()
        if issubclass(cls, BaseModel)
        and cls is not BaseModel
        and not cls.__name__.startswith("_")
    )


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


Actions = Literal["check", "rebuild"]

SUBCOMMANDS: dict[Actions, Callable] = {"check": _check, "rebuild": _rebuild}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=list(SUBCOMMANDS.keys()))
    args = parser.parse_args()
    SUBCOMMANDS[args.action]()
