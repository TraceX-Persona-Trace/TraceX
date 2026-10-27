# Empty placeholder - removed legacy proxy


"""
The original codebase imports ``from models.investigation import Investigation`` etc.
When the project is run from the repository root the ``models`` package does not exist, causing
``ModuleNotFoundError`` and, later, duplicate SQLAlchemy table definitions when the same model
file is imported both as ``backend.models.xxx`` and ``models.xxx``.

This lightweight proxy imports the real modules once and registers them under ``sys.modules``
with the ``models.<name>`` keys, so that existing import statements continue to work without
creating new class objects.
"""

import importlib
import sys

# List of model module names that exist under ``backend.models``.
_MODEL_NAMES = ["investigation", "evidence", "correlation", "graph"]

for _name in _MODEL_NAMES:
    # Import the actual implementation module.
    _module = importlib.import_module(f"backend.models.{_name}")
    # expose it as ``models.<name>`` – this points to the same module object,
    # so class definitions are not recreated.
    sys.modules[f"models.{_name}"] = _module

# Export the public symbols for ``import models`` users.
__all__ = []
for _name in _MODEL_NAMES:
    __all__.append(_name)
