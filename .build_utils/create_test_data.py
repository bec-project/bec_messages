import importlib.util
import os
import sys
from pathlib import Path

import msgpack


def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


os.chdir(Path(__file__).parent)
test_module = import_from_path(
    "test_module",
    Path(__file__).parent / "../python/tests/test_serialization_variants.py",
)
output_dir = schema_dir = Path("../test_data")

for msg_cls in test_module.CLSS_TO_TEST:
    instance = test_module._instantiate_with_defaults(msg_cls)
    ser: bytes = msgpack.packb(instance.model_dump(mode="json"))
    with open(output_dir / msg_cls.__name__, "wb") as f:
        f.write(ser)
