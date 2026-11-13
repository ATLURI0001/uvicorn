import importlib
from typing import Any


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: Any) -> Any:
    if not isinstance(import_str, str):
        return import_str

    module_str, _, attrs_str = import_str.partition(":")
    module_str = module_str.strip()
    attrs_str = attrs_str.strip()
    if not module_str or not attrs_str or any(not attr for attr in attrs_str.split(".")):
        message = 'Import string "{import_str}" must be in format "<module>:<attribute>".'
        raise ImportFromStringError(message.format(import_str=import_str))

    try:
        module = importlib.import_module(module_str)
    except ModuleNotFoundError as exc:
        if exc.name and (module_str == exc.name or module_str.startswith(f"{exc.name}.")):
            message = 'Could not import module "{module_str}".'
            raise ImportFromStringError(message.format(module_str=module_str))
        raise exc from None

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError:
        message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportFromStringError(message.format(attrs_str=attrs_str, module_str=module_str))

    return instance
