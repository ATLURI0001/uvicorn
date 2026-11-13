import pytest

from uvicorn.importer import ImportFromStringError, import_from_string


def test_invalid_format() -> None:
    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("example:")
    expected = 'Import string "example:" must be in format "<module>:<attribute>".'
    assert expected in str(exc_info.value)


def test_invalid_module() -> None:
    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("module_does_not_exist:myattr")
    expected = 'Could not import module "module_does_not_exist".'
    assert expected in str(exc_info.value)


def test_invalid_attr() -> None:
    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("tempfile:attr_does_not_exist")
    expected = 'Attribute "attr_does_not_exist" not found in module "tempfile".'
    assert expected in str(exc_info.value)


def test_internal_import_error() -> None:
    with pytest.raises(ImportError):
        import_from_string("tests.importer.raise_import_error:myattr")


def test_valid_import() -> None:
    instance = import_from_string("tempfile:TemporaryFile")
    from tempfile import TemporaryFile

    assert instance == TemporaryFile


def test_no_import_needed() -> None:
    from tempfile import TemporaryFile

    instance = import_from_string(TemporaryFile)
    assert instance == TemporaryFile


def test_circular_import_error() -> None:
    with pytest.raises(ImportError) as exc_info:
        import_from_string("tests.importer.circular_import_a:bar")
    expected = (
        "cannot import name 'bar' from partially initialized module "
        "'tests.importer.circular_import_a' (most likely due to a circular import)"
    )
    assert expected in str(exc_info.value)


def test_invalid_submodule_and_empty_attr_segments() -> None:
    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("nonexistent_parent_package.submodule:app")
    assert 'Could not import module "nonexistent_parent_package.submodule".' in str(exc_info.value)

    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("tempfile:app.")
    assert 'must be in format "<module>:<attribute>".' in str(exc_info.value)

    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("tempfile:.app")
    assert 'must be in format "<module>:<attribute>".' in str(exc_info.value)

    from tempfile import TemporaryFile

    instance = import_from_string("  tempfile : TemporaryFile  ")
    assert instance == TemporaryFile


def test_invalid_relative_and_empty_module_segments() -> None:
    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string(".module:app")
    assert 'must be in format "<module>:<attribute>".' in str(exc_info.value)

    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("module..sub:app")
    assert 'must be in format "<module>:<attribute>".' in str(exc_info.value)

    with pytest.raises(ImportFromStringError) as exc_info:
        import_from_string("..parent.sub:app")
    assert 'must be in format "<module>:<attribute>".' in str(exc_info.value)
