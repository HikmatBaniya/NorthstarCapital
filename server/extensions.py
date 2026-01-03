from __future__ import annotations

import importlib
import os
from typing import Any


def get_extension() -> Any | None:
    module_name = os.getenv("LOCAL_EXTENSION_MODULE", "local_extensions.extension").strip()
    if not module_name:
        return None
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None
