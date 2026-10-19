"""Keep the tested cloud-library version aligned with HACS installation."""

import json
from importlib.metadata import metadata, requires, version
from pathlib import Path

import pytest
from pyowletapi import api, exceptions
from pyowletapi.api import OwletAPI, TokenDict
from pyowletapi.sock import PropertiesDict, Sock


def test_manifest_dependency_matches_environment():
    manifest = json.loads(Path("custom_components/owlet/manifest.json").read_text())
    assert manifest["requirements"] == [f"pyowletapi=={version('pyowletapi')}"]


def test_retained_library_metadata_contract():
    """Require separate review of any new exact pin, including its metadata."""
    assert version("pyowletapi") == "2025.4.1"
    assert metadata("pyowletapi")["Requires-Python"] == ">=3.10"
    assert requires("pyowletapi") == ["aiohttp"]


@pytest.mark.parametrize(
    "name",
    [
        "OwletAuthenticationError",
        "OwletConnectionError",
        "OwletCredentialsError",
        "OwletDevicesError",
        "OwletEmailError",
        "OwletPasswordError",
    ],
)
def test_library_exception_imports_and_hierarchy(name):
    """Credential-specific errors are siblings, not subclasses of auth error."""
    exception = getattr(exceptions, name)
    assert getattr(api, name) is exception
    assert exception.__bases__ == (exceptions.OwletError,)
    assert exceptions.OwletError.__bases__ == (Exception,)


def test_library_public_types_remain_importable():
    assert OwletAPI.__module__ == "pyowletapi.api"
    assert Sock.__module__ == "pyowletapi.sock"
    assert TokenDict.__required_keys__ == {"api_token", "expiry", "refresh"}
    assert PropertiesDict.__required_keys__ == {
        "raw_properties",
        "properties",
        "tokens",
    }
