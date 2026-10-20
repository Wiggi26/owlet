"""Reject coerced raw flags while retaining contracts for parser failures."""

import json
from copy import deepcopy

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
async def test_raw_alert_null_and_string_are_unknown_despite_library_coercion(
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
    assert hass.states.get(entity_id).state == "unknown"

    mock_api.get_properties.return_value = properties(
        version, low_heart_rate_alert=False
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"
    assert er.async_get(hass).async_get(entity_id) == registered


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(("value", "collapsed"), [(0.5, 0), (1.5, 1), ("0", 0)])
async def test_raw_invalid_charging_withholds_charging_sensitive_entities(
    hass, config_entry, mock_api, version, value, collapsed
):
    mock_api.get_properties.return_value = properties(version, charging=value)
    expected_raw = deepcopy(mock_api.get_properties.return_value["response"])
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    assert coordinator.last_update_success
    assert type(coordinator.sock.properties["charging"]) is int
    assert coordinator.sock.properties["charging"] == collapsed
    assert coordinator.sock.raw_properties == expected_raw
    charging = registered_id(hass, SERIAL, "binary_sensor", "charging")
    heart = registered_id(hass, SERIAL, "sensor", "heart_rate")
    assert hass.states.get(charging).state == "unknown"
    assert hass.states.get(heart).state == "unavailable"
    for platform, key in (
        ("sensor", "oxygen_saturation"),
        ("switch", "base_station_on"),
    ):
        entity_id = registered_id(hass, SERIAL, platform, key)
        assert hass.states.get(entity_id).state == "unavailable"
    if version == 3:
        for platform, key in (
            ("sensor", "sleep_state"),
            ("sensor", "oxygen_10_av"),
            ("binary_sensor", "sleep_state"),
        ):
            entity_id = registered_id(hass, SERIAL, platform, key)
            assert hass.states.get(entity_id).state == "unavailable"
    battery = registered_id(hass, SERIAL, "sensor", "battery_percentage")
    assert hass.states.get(battery).state == ("50.0" if version == 3 else "50")
    mock_api.post_command.assert_not_awaited()


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(("value", "collapsed"), [(None, False), ("false", True)])
async def test_raw_base_station_flag_invalid_state_is_withheld_on_both_versions(
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
    else:
        assert coordinator.sock.properties["base_station_on"] == value
    assert hass.states.get(switch).state == "unavailable"
    mock_api.post_command.assert_not_awaited()


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize("field", [*FLAGS, "charging", "base_station_on"])
async def test_known_raw_binary_flags_remain_valid(
    hass, config_entry, mock_api, version, field
):
    baseline = properties(version)
    if field in FLAGS:
        baseline["response"].setdefault(FLAGS[field], {"value": False})
    mock_api.get_properties.return_value = baseline
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    platform = "switch" if field == "base_station_on" else "binary_sensor"
    entity_id = registered_id(hass, SERIAL, platform, field)
    for value in (False, True, 0, 1):
        payload = properties(version)
        if field in FLAGS:
            payload["response"][FLAGS[field]] = {"value": value}
        else:
            payload = properties(version, **{field: value})
        mock_api.get_properties.return_value = payload
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert coordinator.last_update_success
        assert hass.states.get(entity_id).state == ("on" if value else "off")
    mock_api.post_command.assert_not_awaited()


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize("field", list(FLAGS))
async def test_all_exposed_raw_alert_flags_reject_non_binary_values(
    hass, config_entry, mock_api, version, field
):
    baseline = properties(version)
    baseline["response"].setdefault(FLAGS[field], {"value": False})
    mock_api.get_properties.return_value = baseline
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    entity_id = registered_id(hass, SERIAL, "binary_sensor", field)
    for value in (None, "false", "0", 0.5, 1.0, 2, [], {}):
        payload = properties(version)
        payload["response"][FLAGS[field]] = {"value": value}
        expected_raw = deepcopy(payload["response"])
        mock_api.get_properties.return_value = payload
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert coordinator.last_update_success
        assert coordinator.sock.raw_properties == expected_raw
        assert hass.states.get(entity_id).state == "unknown"
        heart = registered_id(hass, SERIAL, "sensor", "heart_rate")
        assert hass.states.get(heart).state == ("100.0" if version == 3 else "100")
    mock_api.get_properties.return_value = baseline
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"
    mock_api.post_command.assert_not_awaited()


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(
    "field", ["low_heart_rate_alert", "charging", "base_station_on"]
)
async def test_invalid_raw_flag_recovery_preserves_two_sock_bindings(
    hass, config_entry, mock_api, version, field
):
    second = "SYNTHETIC-SOCK-002"
    mock_api.get_devices.return_value = {"response": [device(), device(second, 2)]}
    mock_api.get_properties.return_value = properties(version)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinators = hass.data[DOMAIN][config_entry.entry_id]
    registry = er.async_get(hass)
    heart = registered_id(hass, SERIAL, "sensor", "heart_rate")
    registry.async_update_entity(heart, name="Synthetic custom heart", icon="mdi:heart")
    before = {
        entity.entity_id: (
            entity.unique_id,
            entity.device_id,
            entity.disabled_by,
            entity.name,
            entity.icon,
        )
        for entity in er.async_entries_for_config_entry(registry, config_entry.entry_id)
    }
    saved_entry = (dict(config_entry.data), dict(config_entry.options))
    platform = "switch" if field == "base_station_on" else "binary_sensor"
    entity_id = registered_id(hass, SERIAL, platform, field)
    second_flag = registered_id(hass, second, platform, field)

    for value in (0.5, "0", 1.0, 2, -1, False, True, 0):

        async def readings(_api, serial, reading=value):
            return (
                properties(version, **{field: reading})
                if serial == SERIAL
                else (properties(version, heart_rate=110))
            )

        mock_api.get_properties.side_effect = readings
        for coordinator in coordinators.values():
            await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert all(item.last_update_success for item in coordinators.values())
        valid = type(value) is bool or type(value) is int and value in (0, 1)
        expected = (
            ("on" if value else "off")
            if valid
            else ("unavailable" if field == "base_station_on" else "unknown")
        )
        assert hass.states.get(entity_id).state == expected
        first_heart = registered_id(hass, SERIAL, "sensor", "heart_rate")
        heart_available = field != "charging" or valid and not value
        assert hass.states.get(first_heart).state == (
            ("100.0" if version == 3 else "100") if heart_available else "unavailable"
        )
        battery = registered_id(hass, SERIAL, "sensor", "battery_percentage")
        assert hass.states.get(battery).state == ("50.0" if version == 3 else "50")
        assert hass.states.get(second_flag).state == (
            "on" if field == "base_station_on" else "off"
        )
        heart = registered_id(hass, second, "sensor", "heart_rate")
        assert hass.states.get(heart).state == ("110.0" if version == 3 else "110")

    assert {
        entity.entity_id: (
            entity.unique_id,
            entity.device_id,
            entity.disabled_by,
            entity.name,
            entity.icon,
        )
        for entity in er.async_entries_for_config_entry(registry, config_entry.entry_id)
    } == before
    assert (config_entry.data, config_entry.options) == saved_entry
    mock_api.post_command.assert_not_awaited()


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(
    "field", ["low_heart_rate_alert", "charging", "base_station_on"]
)
@pytest.mark.parametrize("missing_value", [False, True])
async def test_missing_raw_flag_or_value_is_withheld_and_recovers(
    hass, config_entry, mock_api, version, field, missing_value
):
    mock_api.get_properties.return_value = properties(version)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    payload = properties(version)
    if field in FLAGS or version == 2:
        raw_key = (
            FLAGS[field]
            if field in FLAGS
            else ("CHARGE_STATUS" if field == "charging" else "BASE_STATION_ON")
        )
        if missing_value:
            payload["response"][raw_key] = {}
        else:
            del payload["response"][raw_key]
    else:
        vitals = json.loads(payload["response"]["REAL_TIME_VITALS"]["value"])
        del vitals["chg" if field == "charging" else "bso"]
        payload["response"]["REAL_TIME_VITALS"]["value"] = json.dumps(vitals)
    mock_api.get_properties.return_value = payload
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    platform = "switch" if field == "base_station_on" else "binary_sensor"
    entity_id = registered_id(hass, SERIAL, platform, field)
    assert hass.states.get(entity_id).state == (
        "unavailable" if field == "base_station_on" else "unknown"
    )
    mock_api.get_properties.return_value = properties(version)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == (
        "on" if field == "base_station_on" else "off"
    )


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize(
    "field", ["low_heart_rate_alert", "charging", "base_station_on"]
)
async def test_aborting_raw_flag_container_withholds_whole_sock_then_recovers(
    hass, config_entry, mock_api, version, field
):
    mock_api.get_properties.return_value = properties(version)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(version, **{field: "0"})
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert field in coordinator.invalid_flags
    stored = dict(coordinator.sock.properties)
    payload = properties(version)
    raw_key = (
        FLAGS[field]
        if field in FLAGS
        else (
            "REAL_TIME_VITALS"
            if version == 3
            else ("CHARGE_STATUS" if field == "charging" else "BASE_STATION_ON")
        )
    )
    payload["response"][raw_key] = None
    mock_api.get_properties.return_value = payload
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not coordinator.last_update_success
    assert coordinator.sock.properties == stored
    for platform, key in (
        ("sensor", "heart_rate"),
        ("sensor", "battery_percentage"),
        ("binary_sensor", "charging"),
        ("switch", "base_station_on"),
    ):
        entity_id = registered_id(hass, SERIAL, platform, key)
        assert hass.states.get(entity_id).state == "unavailable"
    mock_api.get_properties.return_value = properties(version)
    expected_raw = deepcopy(mock_api.get_properties.return_value["response"])
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert field not in coordinator.invalid_flags
    assert coordinator.sock.raw_properties == expected_raw
    heart = registered_id(hass, SERIAL, "sensor", "heart_rate")
    assert hass.states.get(heart).state == ("100.0" if version == 3 else "100")
    mock_api.post_command.assert_not_awaited()
