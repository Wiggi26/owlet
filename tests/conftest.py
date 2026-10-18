"""Offline Home Assistant fixtures and fail-closed cloud boundaries."""

from contextlib import ExitStack
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pyowletapi.api import OwletAPI
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.owlet.const import DOMAIN, POLLING_INTERVAL

from .fixture_data import INPUT, TOKENS, load_fixture, properties


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations):
    """Load this custom component rather than a nonexistent Core integration."""


@pytest.fixture(autouse=True)
def mock_api():
    """Mock every cloud boundary; forgotten HTTP/refresh/activation mocks fail."""
    with ExitStack() as stack:
        mocks = SimpleNamespace()
        for name in (
            "authenticate",
            "validate_authentication",
            "get_devices",
            "get_properties",
            "post_command",
        ):
            setattr(
                mocks,
                name,
                stack.enter_context(patch.object(OwletAPI, name, autospec=True)),
            )
        mocks.authenticate.return_value = deepcopy(TOKENS)
        mocks.validate_authentication.return_value = None
        mocks.get_devices.return_value = load_fixture("get_devices.json")
        mocks.get_properties.return_value = properties()
        mocks.post_command.return_value = {"synthetic": True}
        forbidden = []
        for name in (
            "request",
            "activate",
            "password_verification",
            "get_mini_token",
            "token_sign_in",
            "refresh_authentication",
            "close",
        ):
            forbidden.append(
                stack.enter_context(
                    patch.object(
                        OwletAPI,
                        name,
                        autospec=True,
                        side_effect=AssertionError(f"Unmocked Owlet call: {name}"),
                    )
                )
            )
        yield mocks
        for unexpected in forbidden:
            unexpected.assert_not_awaited()


@pytest.fixture
def config_entry(hass):
    """Create an existing version-1 entry with synthetic saved tokens and options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=INPUT["username"],
        unique_id=INPUT["username"],
        version=1,
        data={"region": INPUT["region"], "username": INPUT["username"], **TOKENS},
        options={"scan_interval": POLLING_INTERVAL},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_entry(hass, config_entry, mock_api):
    """Set up all actual entity platforms through Home Assistant's loader."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
