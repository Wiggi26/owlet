"""Setup, discovery, token persistence, identity and unload baseline."""

from copy import deepcopy
from importlib.metadata import version
from unittest.mock import ANY

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletDevicesError,
    OwletError,
)

from custom_components.owlet.const import DOMAIN

from .fixture_data import SERIAL, TOKENS, device, load_fixture, properties


async def test_async_setup_entry(hass, setup_entry, mock_api):
    assert setup_entry.state is ConfigEntryState.LOADED
    registry = dr.async_get(hass)
    sock = next(
        item
        for item in dr.async_entries_for_config_entry(registry, setup_entry.entry_id)
        if (DOMAIN, SERIAL) in item.identifiers
    )
    assert sock.name == f"Owlet Sock {SERIAL}"
    entities = er.async_entries_for_device(
        er.async_get(hass), sock.id, include_disabled_entities=True
    )
    assert len(entities) == 21
    assert len([entity for entity in entities if entity.disabled_by is None]) == 19
    heart_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-heart_rate"
    )
    expected_ids = {
        "2025.12.4": "sensor.owlet_sock_synthetic_sock_001_heart_rate",
        "2026.10.2": "sensor.nursery_owlet_sock_synthetic_sock_001_heart_rate",
    }
    assert heart_id == expected_ids[version("homeassistant")]
    mock_api.get_devices.assert_awaited_once_with(ANY, [2, 3])
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    assert setup_entry.state is ConfigEntryState.NOT_LOADED
    assert setup_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.parametrize("location", ["authenticate", "discovery", "poll"])
async def test_async_setup_entry_new_tokens(hass, config_entry, mock_api, location):
    original = dict(config_entry.data)
    options = dict(config_entry.options)
    config_entry_id = config_entry.entry_id
    new = {
        "api_token": "synthetic-new-access",
        "expiry": TOKENS["expiry"] + 300,
        "refresh": "synthetic-new-refresh",
    }
    if location == "authenticate":
        mock_api.authenticate.return_value = new
    elif location == "discovery":
        mock_api.get_devices.return_value = load_fixture("get_devices_with_tokens.json")
        assert mock_api.get_devices.return_value["tokens"] == new
    else:
        mock_api.get_properties.return_value["tokens"] = new
    assert await hass.config_entries.async_setup(config_entry_id)
    await hass.async_block_till_done()
    assert config_entry.data == {**original, **new}
    assert config_entry.options == options
    assert config_entry.entry_id == config_entry_id
    assert config_entry.version == 1
    assert "password" not in config_entry.data


@pytest.mark.parametrize(
    ("error", "state"),
    [
        (OwletAuthenticationError(), ConfigEntryState.SETUP_ERROR),
        (OwletConnectionError(), ConfigEntryState.SETUP_RETRY),
        (OwletDevicesError(), ConfigEntryState.SETUP_ERROR),
        (OwletError(), ConfigEntryState.SETUP_ERROR),
    ],
)
async def test_async_setup_entry_errors(hass, config_entry, mock_api, error, state):
    original = dict(config_entry.data)
    mock_api.authenticate.side_effect = error
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is state
    assert config_entry.data == original


@pytest.mark.parametrize("payload", [None, {}, {"response": None}, {"response": [{}]}])
async def test_malformed_discovery(hass, config_entry, mock_api, payload):
    mock_api.get_devices.return_value = payload
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_multiple_socks_and_reload_preserve_registry(
    hass, config_entry, mock_api
):
    second = "SYNTHETIC-SOCK-002"
    mock_api.get_devices.return_value = {"response": [device(), device(second, 2)]}

    async def reading(_api, serial):
        return properties(heart_rate=100 if serial == SERIAL else 101)

    mock_api.get_properties.side_effect = reading
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, config_entry.entry_id)
    ids_before = {entry.unique_id: entry.entity_id for entry in entries}
    assert len(entries) == 42
    for serial, value in ((SERIAL, "100.0"), (second, "101.0")):
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{serial}-heart_rate"
        )
        assert hass.states.get(entity_id).state == value
    selected = registry.async_get_entity_id("sensor", DOMAIN, f"{SERIAL}-heart_rate")
    registry.async_update_entity(
        selected,
        name="Synthetic custom name",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    saved_data, saved_options = (
        deepcopy(dict(config_entry.data)),
        dict(config_entry.options),
    )
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()
    after = er.async_entries_for_config_entry(registry, config_entry.entry_id)
    assert {entry.unique_id: entry.entity_id for entry in after} == ids_before
    assert registry.async_get(selected).name == "Synthetic custom name"
    assert registry.async_get(selected).disabled_by is er.RegistryEntryDisabler.USER
    assert config_entry.data == saved_data
    assert config_entry.options == saved_options


async def test_expired_credentials_request_reauth(hass, config_entry, mock_api):
    """Expired credentials keep the entry and options while opening reauthentication."""
    hass.config_entries.async_update_entry(
        config_entry, data={**config_entry.data, "expiry": 1}
    )
    original, options = dict(config_entry.data), dict(config_entry.options)
    mock_api.authenticate.side_effect = OwletAuthenticationError()
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    assert config_entry.data == original
    assert config_entry.options == options
    assert any(
        flow["context"].get("entry_id") == config_entry.entry_id
        for flow in hass.config_entries.flow.async_progress()
    )


async def test_refreshed_tokens_survive_unload_and_setup(hass, setup_entry, mock_api):
    """The next client loads the rotated token set from the existing entry."""
    original = dict(setup_entry.data)
    rotated = {
        "api_token": "synthetic-rotated",
        "expiry": TOKENS["expiry"] + 100,
        "refresh": "synthetic-rotated-refresh",
    }
    mock_api.get_properties.return_value = {**properties(), "tokens": rotated}
    await hass.data[DOMAIN][setup_entry.entry_id][SERIAL].async_refresh()
    assert setup_entry.data == {**original, **rotated}
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    mock_api.authenticate.return_value = None
    mock_api.get_properties.return_value = properties()
    assert await hass.config_entries.async_setup(setup_entry.entry_id)
    await hass.async_block_till_done()
    client = hass.data[DOMAIN][setup_entry.entry_id][SERIAL].sock.api
    assert client.tokens == rotated
    assert setup_entry.options == {"scan_interval": 5}
