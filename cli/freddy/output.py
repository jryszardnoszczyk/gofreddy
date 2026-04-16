"""Output formatting — JSON (default) or human-readable."""

import json
import sys
from typing import Any


def emit(data: Any, *, human: bool = False) -> None:
    """Print output data in JSON (default) or human-readable format."""
    if human:
        _print_human(data)
    else:
        print(json.dumps(data, indent=2, default=str))


def _print_human(data: Any, indent: int = 0) -> None:
    """Pretty-print data for human consumption."""
    prefix = "  " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}:")
                _print_human(value, indent + 1)
            else:
                print(f"{prefix}{key}: {value}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                if i > 0:
                    print(f"{prefix}---")
                _print_human(item, indent)
            else:
                print(f"{prefix}- {item}")
    else:
        print(f"{prefix}{data}")


def emit_error(code: str, message: str) -> None:
    """Print structured error to stderr and exit."""
    json.dump({"error": {"code": code, "message": message}}, sys.stderr)
    sys.stderr.write("\n")
    raise SystemExit(1)
