import importlib
import keyword
from typing import Any


class ImportFromStringError(Exception):
    pass


def split_import_string(import_str: str) -> tuple[str, str]:
    """Parse and validate an import string into (module_str, attrs_str).

    Raises ImportFromStringError if the format or identifiers are invalid.
    """
    if not isinstance(import_str, str) or import_str.count(":") != 1:
        message = 'Import string "{import_str}" must be in format "<module>:<attribute>".'
        raise ImportFromStringError(message.format(import_str=import_str))

    module_str, _, attrs_str = import_str.partition(":")
    module_str = module_str.strip()
    attrs_str = attrs_str.strip()
    if (
        not module_str
        or not attrs_str
        or any(not seg or not seg.isidentifier() or keyword.iskeyword(seg) for seg in module_str.split("."))
        or any(not attr or not attr.isidentifier() for attr in attrs_str.split("."))
    ):
        message = 'Import string "{import_str}" must be in format "<module>:<attribute>".'
        raise ImportFromStringError(message.format(import_str=import_str))

    return module_str, attrs_str


def is_valid_import_string(import_str: Any) -> bool:
    """Return True if import_str is a syntactically valid '<module>:<attribute>' specification."""
    try:
        split_import_string(import_str)
        return True
    except (ImportFromStringError, TypeError):
        return False


def normalize_import_string(import_str: Any) -> str | None:
    """Normalize and sanitize an import string into a canonical '<module>:<attribute>' format.

    Strips surrounding whitespace, cleans redundant spacing around colons and attribute dots,
    and validates syntactic correctness. Returns None if import_str is invalid or non-string.
    """
    if not isinstance(import_str, str):
        return None
    try:
        module_str, attrs_str = split_import_string(import_str)
        clean_mod = ".".join(seg.strip() for seg in module_str.split("."))
        clean_attr = ".".join(attr.strip() for attr in attrs_str.split("."))
        return f"{clean_mod}:{clean_attr}"
    except (ImportFromStringError, TypeError):
        return None


def parse_import_target(import_str: Any) -> dict[str, Any] | None:
    """Decompose an import specification string into a structured descriptor dictionary.

    Returns:
        Dictionary with keys 'raw', 'normalized', 'module', 'package', 'attribute', 'attributes', 'is_nested',
        or None if the string fails import validation.
    """
    normalized = normalize_import_string(import_str)
    if normalized is None:
        return None

    module_str, attrs_str = normalized.split(":", 1)
    attributes = attrs_str.split(".")
    package = module_str.split(".")[0]

    return {
        "raw": import_str,
        "normalized": normalized,
        "module": module_str,
        "package": package,
        "attribute": attrs_str,
        "attributes": attributes,
        "is_nested": len(attributes) > 1,
    }


def import_from_string(import_str: Any) -> Any:
    if not isinstance(import_str, str):
        return import_str

    module_str, attrs_str = split_import_string(import_str)

    try:
        module = importlib.import_module(module_str)
    except ModuleNotFoundError as exc:
        if exc.name and (module_str == exc.name or module_str.startswith(f"{exc.name}.")):
            message = 'Could not import module "{module_str}".'
            raise ImportFromStringError(message.format(module_str=module_str))
        raise exc from None
    except (TypeError, ValueError) as exc:
        message = 'Could not import module "{module_str}".'
        raise ImportFromStringError(message.format(module_str=module_str)) from exc

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError:
        message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportFromStringError(message.format(attrs_str=attrs_str, module_str=module_str))

    return instance
