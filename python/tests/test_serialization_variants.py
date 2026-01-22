import json
from enum import Enum
from pathlib import Path
from types import GenericAlias, NoneType, UnionType
from typing import Any, ForwardRef, Literal, TypeVar, get_args, get_origin

import jsonschema
import msgpack
import numpy as np
import pytest
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from bec_messages import messages
from bec_messages.messages import (
    BECMessage,
    BundleMessage,
    DeviceAsyncUpdate,
    DeviceConfigMessage,
    DeviceMonitor1DMessage,
    LogMessage,
    MacroUpdateMessage,
    ProcedureAbortMessage,
    ProcedureClearUnhandledMessage,
    ProcedureWorkerStatusMessage,
    ScanQueueStatus,
    ScanQueueStatusMessage,
)

_T = TypeVar("_T")
default_vals = {
    list: [1, 2, 3],
    int: 5,
    float: 6.6,
    np.ndarray: np.ones((1, 7)),
    str: "hello",
    dict: {"a": "b"},
}

VALIDATION_OVERRIDES = {
    BundleMessage: {
        "messages": [
            LogMessage(log_type="trace", log_msg="log1"),
            LogMessage(log_type="trace", log_msg="log2"),
        ]
    },
    DeviceMonitor1DMessage: {"data": np.ones(5)},
    ScanQueueStatusMessage: {"queue": {"primary": ScanQueueStatus(info=[], status="test")}},
    DeviceAsyncUpdate: {"max_shape": [3, 3, 3]},
    DeviceConfigMessage: {"config": {"K": "v"}},
    ProcedureAbortMessage: {"queue": "test"},
    ProcedureClearUnhandledMessage: {"queue": "test"},
    ProcedureWorkerStatusMessage: {"current_execution_id": "test"},
    MacroUpdateMessage: {"macro_name": "test", "file_path": "/tmp/"},
}


def _default_var(c: type, k: str, i: FieldInfo):
    # For special cases such as validation functions, check the overrides first
    if c in VALIDATION_OVERRIDES and k in VALIDATION_OVERRIDES[c]:
        return VALIDATION_OVERRIDES[c][k]
    # If the model has a default, use it
    if i.default is not PydanticUndefined:
        return i.default
    # Best effort to return a default from the type definition
    t = i.annotation
    if t is Any or t is None:
        return None  # type: ignore # yes it is
    if t in default_vals:
        return default_vals[t]
    if isinstance(t, ForwardRef):
        raise TypeError(f"Make sure all refs are resolved: error in {t}")
    if issubclass(t, BaseModel):
        return _instantiate_with_defaults(t)
    if isinstance(t, GenericAlias):
        return get_origin(t)()
    if isinstance(t, UnionType):
        args = get_args(t)
        if NoneType in args:
            return None
        return args[0]()
    if type(t) is type(Literal[""]):
        return get_args(t)[0]
    if get_origin(t) is not None:
        # optional type not caught by above
        return _default_var(c, k, get_args(t)[0])
    if issubclass(t, Enum):
        return list(t)[0]
    try:
        return t()
    except Exception:
        raise TypeError(f"No default for type: {t}")


_M = TypeVar("_M", bound=BaseModel)


def _instantiate_with_defaults(c: type[_M]) -> _M:
    c.model_rebuild()
    data = {k: _default_var(c, k, v) for k, v in c.model_fields.items()}
    return c.model_validate(data)


def _get_model_classes():
    return (
        cls
        for cls in messages.__dict__.values()
        if issubclass(cls, BaseModel)
        and cls is not BaseModel
        and cls is not BECMessage
        and not cls.__name__.startswith("_")
    )


CLSS_TO_TEST = list(_get_model_classes())


@pytest.mark.parametrize("msg_cls", CLSS_TO_TEST)
def test_pydantic_python_roundtrip(msg_cls):
    instance = _instantiate_with_defaults(msg_cls)
    ser = instance.model_dump()
    deser = msg_cls.model_validate(ser)
    assert deser == instance


@pytest.mark.parametrize("msg_cls", CLSS_TO_TEST)
def test_pydantic_json_roundtrip(msg_cls):
    instance = _instantiate_with_defaults(msg_cls)
    ser = instance.model_dump_json()
    deser = msg_cls.model_validate_json(ser)
    assert deser == instance


def object_hook(data):
    if "__bec_codec__" in data:
        if (type_name := data["__bec_codec__"].get("type_name")) is None:
            raise TypeError(f"Malformed __bec_codec__ block in {data}")
        if (msg_cls := messages.__dict__.get(type_name)) is None:
            raise TypeError(f"BEC serializable type {type_name} unknown")
        return msg_cls.model_validate(data)
    return data


@pytest.mark.parametrize("msg_cls", CLSS_TO_TEST)
def test_msgpack_roundtrip(msg_cls):
    instance = _instantiate_with_defaults(msg_cls)
    ser = msgpack.packb(instance.model_dump(mode="json"))
    deser = msgpack.unpackb(ser, object_hook=object_hook)
    assert instance == deser


def _schema_for_cls(cls: BaseModel):
    cls.__name__
    with open(Path(__file__).parent / "../../json_schema/" / (cls.__name__ + ".json")) as f:
        return json.load(f)


@pytest.mark.parametrize("msg_cls", CLSS_TO_TEST)
def test_pydantic_against_schema(msg_cls):
    instance = _instantiate_with_defaults(msg_cls)
    dump = instance.model_dump(mode="json")
    schema = _schema_for_cls(msg_cls)
    jsonschema.validate(dump, schema)


@pytest.mark.parametrize("msg_cls", CLSS_TO_TEST)
def test_msgpack_against_schema(msg_cls):
    instance = _instantiate_with_defaults(msg_cls)
    ser = msgpack.packb(instance.model_dump(mode="json"))
    deser = msgpack.unpackb(ser)
    schema = _schema_for_cls(msg_cls)
    jsonschema.validate(deser, schema)
