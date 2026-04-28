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


def _yaml_scalar(value: Any) -> str:
    """Render a primitive as its YAML spelling (null/true/false/...)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _print_human(data: Any, indent: int = 0) -> None:
    """Pretty-print data for human consumption."""
    prefix = "  " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}:")
                _print_human(value, indent + 1)
            else:
                print(f"{prefix}{key}: {_yaml_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                keys = list(item.keys())
                if not keys:
                    print(f"{prefix}- {{}}")
                    continue
                for j, key in enumerate(keys):
                    value = item[key]
                    marker = "- " if j == 0 else "  "
                    if isinstance(value, (dict, list)):
                        print(f"{prefix}{marker}{key}:")
                        _print_human(value, indent + 2)
                    else:
                        print(f"{prefix}{marker}{key}: {_yaml_scalar(value)}")
            else:
                print(f"{prefix}- {_yaml_scalar(item)}")
    else:
        print(f"{prefix}{_yaml_scalar(data)}")


def emit_error(code: str, message: str) -> None:
    """Print structured error to stderr and exit."""
    json.dump({"error": {"code": code, "message": message}}, sys.stderr)
    sys.stderr.write("\n")
    raise SystemExit(1)
