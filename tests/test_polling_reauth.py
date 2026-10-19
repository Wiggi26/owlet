"""Polling authentication recovery through Home Assistant and the real reload."""

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pyowletapi.exceptions import OwletAuthenticationError

from custom_components.owlet.const import DOMAIN

from .fixture_data import SERIAL, TOKENS, device, properties


@pytest.mark.parametrize("region", ["europe", "world"])
async def test_polling_reauth_reload_preserves_two_socks(
    hass, config_entry, mock_api, region
):
    """An auth failure opens one entry-linked flow without disturbing its peer."""
    second = "SYNTHETIC-SOCK-002"
    hass.config_entries.async_update_entry(
        config_entry,
        data={**config_entry.data, "region": region, "preserved_data": "synthetic"},
        options={"scan_interval": 10, "preserved_option": "synthetic"},
    )
    mock_api.get_devices.return_value = {"response": [device(), device(second, 2)]}
    failing = False

    async def reading(_api, serial):
        if failing and serial == SERIAL:
            raise OwletAuthenticationError()
        return properties(heart_rate=100 if serial == SERIAL else 101)

    mock_api.get_properties.side_effect = reading
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    entry_id, unique_id, title, version = (
        config_entry.entry_id,
        config_entry.unique_id,
        config_entry.title,
        config_entry.version,
    )
    saved_data, saved_options = dict(config_entry.data), dict(config_entry.options)
    registry = er.async_get(hass)
    heart_id = registry.async_get_entity_id("sensor", DOMAIN, f"{SERIAL}-heart_rate")
    second_id = registry.async_get_entity_id("sensor", DOMAIN, f"{second}-heart_rate")
    movement_id = registry.async_get_entity_id("sensor", DOMAIN, f"{SERIAL}-movement")
    registry.async_update_entity(
        heart_id,
        new_entity_id="sensor.synthetic_custom_heart_rate",
        name="Synthetic custom heart rate",
    )
    heart_id = "sensor.synthetic_custom_heart_rate"
    registry.async_update_entity(movement_id, disabled_by=er.RegistryEntryDisabler.USER)
    devices = dr.async_get(hass)
    device_id = registry.async_get(heart_id).device_id
    devices.async_update_device(device_id, name_by_user="Synthetic custom device")
    await hass.async_block_till_done()

    def entity_bindings():
        return {
            (entry.domain, entry.unique_id): (
                entry.entity_id,
                entry.device_id,
                entry.config_entry_id,
                entry.name,
                entry.disabled_by,
            )
            for entry in er.async_entries_for_config_entry(registry, entry_id)
        }

    def device_bindings():
        return {
            entry.id: (entry.identifiers, entry.name_by_user)
            for entry in dr.async_entries_for_config_entry(devices, entry_id)
        }

    entities_before, devices_before = entity_bindings(), device_bindings()
    assert len(entities_before) == 42
    coordinators = hass.data[DOMAIN][entry_id]
    failed, healthy = coordinators[SERIAL], coordinators[second]
    failing = True
    await failed.async_refresh()
    await healthy.async_refresh()
    await hass.async_block_till_done()

    assert not failed.last_update_success
    assert isinstance(failed.last_exception, ConfigEntryAuthFailed)
    assert str(failed.last_exception) == "Authentication failed"
    assert hass.states.get(heart_id).state == "unavailable"
    assert healthy.last_update_success
    assert hass.states.get(second_id).state == "101.0"
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.data == saved_data
    assert config_entry.options == saved_options
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert flows[0]["context"]["entry_id"] == entry_id
    assert flows[0]["step_id"] == "reauth_confirm"
    assert entity_bindings() == entities_before
    assert device_bindings() == devices_before

    rotated = {
        "api_token": "reauth-synthetic-access",
        "expiry": TOKENS["expiry"] + 300,
        "refresh": "reauth-synthetic-refresh",
    }
    mock_api.authenticate.return_value = rotated
    failing = False
    result = await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"], {"password": "replacement-synthetic-password"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert not hass.config_entries.flow.async_progress()
    assert hass.config_entries.async_get_entry(entry_id) is config_entry
    assert config_entry.state is ConfigEntryState.LOADED
    assert (config_entry.unique_id, config_entry.title, config_entry.version) == (
        unique_id,
        title,
        version,
    )
    assert config_entry.data == {**saved_data, **rotated}
    assert config_entry.options == saved_options
    assert "password" not in config_entry.data
    assert entity_bindings() == entities_before
    assert device_bindings() == devices_before
    reloaded = hass.data[DOMAIN][entry_id]
    assert reloaded[SERIAL] is not failed
    assert reloaded[second] is not healthy
    for serial, entity_id, value in (
        (SERIAL, heart_id, "100.0"),
        (second, second_id, "101.0"),
    ):
        assert reloaded[serial].last_update_success
        assert reloaded[serial].sock.api._region == region
        assert hass.states.get(entity_id).state == value
