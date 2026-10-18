"""Polling failures, recovery, malformed responses and token refresh baseline."""

from datetime import timedelta

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import entity_registry as er
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletError,
)

from custom_components.owlet.const import DOMAIN

from .fixture_data import SERIAL, properties
from .regressions import PollingOptionDefect


@pytest.mark.parametrize(
    "error",
    [OwletConnectionError(), OwletError(), TimeoutError(), RuntimeError("synthetic")],
)
async def test_coordinator_error_and_recovery(hass, setup_entry, mock_api, error):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-heart_rate"
    )
    mock_api.get_properties.side_effect = error
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not coordinator.last_update_success
    assert hass.states.get(entity_id).state == "unavailable"
    registry = er.async_get(hass)
    for platform, key in (("binary_sensor", "charging"), ("switch", "base_station_on")):
        unavailable_id = registry.async_get_entity_id(
            platform, DOMAIN, f"{SERIAL}-{key}"
        )
        assert hass.states.get(unavailable_id).state == "unavailable"
    mock_api.get_properties.side_effect = None
    mock_api.get_properties.return_value = properties(heart_rate=101)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert hass.states.get(entity_id).state == "101.0"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"response": {}},
        {"response": {"REAL_TIME_VITALS": {"value": "invalid-json"}}},
    ],
)
async def test_malformed_poll_unavailable(hass, setup_entry, mock_api, payload):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = payload
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not coordinator.last_update_success
    assert setup_entry.state is ConfigEntryState.LOADED


@pytest.mark.parametrize("value", [None, "not-a-number"])
async def test_malformed_numeric_poll_unavailable(hass, setup_entry, mock_api, value):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(heart_rate=value)
    await coordinator.async_refresh()
    assert not coordinator.last_update_success


@pytest.mark.xfail(
    strict=True,
    raises=KeyError,
    reason="AUDIT: polling auth reads email instead of username; roadmap PR 2",
)
async def test_coordinator_auth_error(hass, setup_entry, mock_api):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.side_effect = OwletAuthenticationError()
    try:
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()
    except KeyError as err:
        assert err.args == ("email",)
        raise


@pytest.mark.xfail(
    strict=True,
    raises=PollingOptionDefect,
    reason="AUDIT: saved options do not update running polling; roadmap PR 2",
)
async def test_saved_interval_applies(hass, setup_entry):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    hass.config_entries.async_update_entry(setup_entry, options={"scan_interval": 10})
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    if coordinator.update_interval == timedelta(seconds=5):
        raise PollingOptionDefect(
            "The saved interval is 10; the running interval remains 5"
        )
    assert coordinator.update_interval == timedelta(seconds=10)
