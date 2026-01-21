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

import bec_messages
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
from bec_messages.serialization import MsgpackSerialization


def _get_model_classes():
    return (
        cls
        for cls in messages.__dict__.values()
        if issubclass(cls, BaseModel)
        and cls is not BaseModel
        and cls is not BECMessage
        and not cls.__name__.startswith("_")
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


CLSS_TO_TEST = list(_get_model_classes())


@pytest.mark.parametrize("msg_cls", CLSS_TO_TEST)
def test_msgpack_roundtrip(msg_cls):
    instance = _instantiate_with_defaults(msg_cls)
    ser = MsgpackSerialization.dumps(instance)
    deser = MsgpackSerialization.loads(ser)
    if isinstance(deser, dict):
        deser = msg_cls.model_validate(deser)
    if msg_cls is BundleMessage:
        assert deser == instance.messages
    else:
        assert deser == instance


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
    ser = MsgpackSerialization.dumps(instance)
    deser = msgpack.unpackb(ser)

    schema = _schema_for_cls(msg_cls)
    jsonschema.validate(dump, schema)
