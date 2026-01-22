import inspect
import json
from enum import Enum
from pathlib import Path
from types import GenericAlias, NoneType, UnionType
from typing import Any, ForwardRef, Literal, TypeVar, get_args, get_origin

import msgpack
import numpy as np
import pytest
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from bec_lib import messages as bec_lib_messages
from bec_lib.serialization import MsgpackSerialization
from bec_messages import messages as bec_messages_messages
from bec_messages.messages import (
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
    np.ndarray: np.ones((10, 50)),
    str: "hello",
    dict: {"a": "b"},
}


def log_msg_override(module):
    return [
        module.__dict__.get("LogMessage")(log_type="trace", log_msg="log1"),
        module.__dict__.get("LogMessage")(log_type="trace", log_msg="log2"),
    ]


def scan_que_stat_override(module):
    return {"primary": module.__dict__.get("ScanQueueStatus")(info=[], status="test")}


VALIDATION_OVERRIDES = {
    "BundleMessage": {"messages": log_msg_override},
    "DeviceMonitor1DMessage": {"data": np.ones(5)},
    "ScanQueueStatusMessage": {"queue": scan_que_stat_override},
    "DeviceAsyncUpdate": {"max_shape": [3, 3, 3]},
    "DeviceConfigMessage": {"config": {"K": "v"}},
    "ProcedureAbortMessage": {"queue": "test"},
    "ProcedureClearUnhandledMessage": {"queue": "test"},
    "ProcedureWorkerStatusMessage": {"current_execution_id": "test"},
    "MacroUpdateMessage": {"macro_name": "test", "file_path": "/tmp/"},
}


def _default_var(c: type, k: str, i: FieldInfo, module):
    # For special cases such as validation functions, check the overrides first
    if c.__name__ in VALIDATION_OVERRIDES and k in VALIDATION_OVERRIDES[c.__name__]:
        override = VALIDATION_OVERRIDES[c.__name__][k]
        if callable(override):
            return override(module)
        return VALIDATION_OVERRIDES[c.__name__][k]
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
        return _instantiate_with_defaults(t, module)
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
        return _default_var(c, k, get_args(t)[0], module)
    if issubclass(t, Enum):
        return list(t)[0]
    try:
        return t()
    except Exception:
        raise TypeError(f"No default for type: {t}")


_M = TypeVar("_M", bound=BaseModel)


def _instantiate_with_defaults(c: type[_M], module) -> _M:
    c.model_rebuild()
    data = {k: _default_var(c, k, v, module) for k, v in c.model_fields.items()}
    return c.model_validate(data)


def _get_model_classes(msg_module):
    return (
        cls
        for cls in msg_module.__dict__.values()
        if inspect.isclass(cls)
        if issubclass(cls, msg_module.BECMessage)
        and cls is not msg_module.BaseModel
        and cls is not msg_module.BECMessage
        and not cls.__name__.startswith("_")
    )


BEC_CORE_CLASSES = list(_get_model_classes(bec_lib_messages))
BEC_MESSAGES_CLASSES = list(_get_model_classes(bec_messages_messages))


def object_hook(data):
    if "__bec_codec__" in data:
        if (type_name := data["__bec_codec__"].get("type_name")) is None:
            raise TypeError(f"Malformed __bec_codec__ block in {data}")
        if (msg_cls := bec_messages_messages.__dict__.get(type_name)) is None:
            raise TypeError(f"BEC serializable type {type_name} unknown")
        return msg_cls.model_validate(data)
    return data


def test_msgpack_roundtrip():
    for _ in range(100):
        for msg_cls in BEC_MESSAGES_CLASSES:
            instance = _instantiate_with_defaults(msg_cls, bec_messages_messages)
            ser = msgpack.packb(instance.model_dump(mode="json"))
            deser = msgpack.unpackb(ser, object_hook=object_hook)
            assert instance == deser


def test_bec_core_msgpack_roundtrip():
    for _ in range(100):
        for msg_cls in BEC_CORE_CLASSES:
            instance = _instantiate_with_defaults(msg_cls, bec_lib_messages)
            ser = MsgpackSerialization.dumps(instance)
            deser = MsgpackSerialization.loads(ser)
            if msg_cls.__name__ == "BundleMessage":
                assert instance.messages == deser
            else:
                assert instance == deser
