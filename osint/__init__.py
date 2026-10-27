import importlib, sys
# Alias the backend.osint package as the top-level `osint` module for legacy imports
_backend_osint = importlib.import_module('backend.osint')
sys.modules[__name__] = _backend_osint
