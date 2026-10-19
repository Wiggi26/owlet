"""Characterize retained raw-parser defects, without claiming field isolation."""

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.owlet.const import DOMAIN

from .fixture_data import FLAGS, SERIAL, device, properties


def registered_id(hass, serial, platform, key):
    """Find an existing entity through its stable platform unique ID."""
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{serial}-{key}")


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(
    ("field", "value", "error"),
    [("movement", None, TypeError), ("signal_strength", "bad", ValueError)],
)
async def test_raw_numeric_error_retains_stored_data_but_withholds_failed_sock(
    hass, config_entry, mock_api, version, field, value, error
):
    second = "SYNTHETIC-SOCK-002"
    mock_api.get_devices.return_value = {"response": [device(), device(second, 2)]}
    mock_api.get_properties.return_value = properties(version)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinators = hass.data[DOMAIN][config_entry.entry_id]
    first = coordinators[SERIAL]
    registry = er.async_get(hass)
    before = {
        entity.entity_id: (entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(registry, config_entry.entry_id)
    }
    saved_entry = (dict(config_entry.data), dict(config_entry.options))
    stored = dict(first.sock.properties)
    bad_payload = properties(version, heart_rate=120, **{field: value})

    async def readings(_api, serial):
        return bad_payload if serial == SERIAL else properties(version, heart_rate=110)

    mock_api.get_properties.side_effect = readings
    # The public update has already stored raw data when normalization raises.
    with pytest.raises(error):
        await first.sock.update_properties()
    assert first.sock.raw_properties == bad_payload["response"]
    assert first.sock.properties == stored
    for coordinator in coordinators.values():
        await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not first.last_update_success
    assert coordinators[second].last_update_success
    assert first.sock.properties == stored
    for platform, key in (
        ("sensor", "heart_rate"),
        ("sensor", "battery_percentage"),
        ("binary_sensor", "low_heart_rate_alert"),
        ("switch", "base_station_on"),
    ):
        assert hass.states.get(registered_id(hass, SERIAL, platform, key)).state == (
            "unavailable"
        )
    second_heart = registered_id(hass, second, "sensor", "heart_rate")
    assert hass.states.get(second_heart).state == ("110.0" if version == 3 else "110")

    mock_api.get_properties.side_effect = None
    mock_api.get_properties.return_value = properties(version, heart_rate=105)
    for coordinator in coordinators.values():
        await coordinator.async_refresh()
    await hass.async_block_till_done()
    for serial in (SERIAL, second):
        assert coordinators[serial].last_update_success
        heart = registered_id(hass, serial, "sensor", "heart_rate")
        assert hass.states.get(heart).state == ("105.0" if version == 3 else "105")
    assert {
        entity.entity_id: (entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(registry, config_entry.entry_id)
    } == before
    assert (config_entry.data, config_entry.options) == saved_entry
    mock_api.post_command.assert_not_awaited()


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(("value", "collapsed"), [(None, False), ("false", True)])
async def test_raw_alert_null_and_string_collapse_where_missing_remains_unknown(
    hass, config_entry, mock_api, version, value, collapsed
):
    mock_api.get_properties.return_value = properties(version)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    entity_id = registered_id(hass, SERIAL, "binary_sensor", "low_heart_rate_alert")
    registered = er.async_get(hass).async_get(entity_id)

    missing = properties(version)
    del missing["response"][FLAGS["low_heart_rate_alert"]]
    mock_api.get_properties.return_value = missing
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert hass.states.get(entity_id).state == "unknown"

    mock_api.get_properties.return_value = properties(
        version, low_heart_rate_alert=value
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert coordinator.sock.properties["low_heart_rate_alert"] is collapsed
    assert hass.states.get(entity_id).state == ("on" if collapsed else "off")

    mock_api.get_properties.return_value = properties(
        version, low_heart_rate_alert=False
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"
    assert er.async_get(hass).async_get(entity_id) == registered


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(("value", "collapsed"), [(0.5, 0), (True, 1)])
async def test_raw_charging_cast_loses_original_type(
    hass, config_entry, mock_api, version, value, collapsed
):
    mock_api.get_properties.return_value = properties(version, charging=value)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    assert coordinator.last_update_success
    assert type(coordinator.sock.properties["charging"]) is int
    assert coordinator.sock.properties["charging"] == collapsed
    charging = registered_id(hass, SERIAL, "binary_sensor", "charging")
    heart = registered_id(hass, SERIAL, "sensor", "heart_rate")
    assert hass.states.get(charging).state == ("on" if collapsed else "off")
    assert hass.states.get(heart).state == (
        "unavailable" if collapsed else "100.0" if version == 3 else "100"
    )


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(("value", "collapsed"), [(None, False), ("false", True)])
async def test_raw_base_station_flag_validity_differs_by_device_version(
    hass, config_entry, mock_api, version, value, collapsed
):
    mock_api.get_properties.return_value = properties(version, base_station_on=value)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    switch = registered_id(hass, SERIAL, "switch", "base_station_on")
    assert coordinator.last_update_success
    if version == 2:
        assert coordinator.sock.properties["base_station_on"] is collapsed
        assert hass.states.get(switch).state == ("on" if collapsed else "off")
    else:
        assert coordinator.sock.properties["base_station_on"] == value
        assert hass.states.get(switch).state == "unavailable"
    mock_api.post_command.assert_not_awaited()
