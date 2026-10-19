"""Battery transition contract through the pinned parser and HA entities."""

import json
from datetime import timedelta
from pathlib import Path

from homeassistant.helpers import entity_registry as er

from custom_components.owlet.const import DOMAIN
from tests.fixture_data import SERIAL, device, load_fixture


def _battery_fixture():
    return json.loads(
        Path(__file__)
        .with_name("fixtures")
        .joinpath("battery_transitions.json")
        .read_text()
    )


def _v3_response(vitals):
    response = load_fixture("update_properties_awake.json")
    response["response"]["REAL_TIME_VITALS"]["value"] = json.dumps(vitals)
    response["response"]["REAL_TIME_VITALS"]["data_updated_at"] = "2026-10-19T12:00:00Z"
    return response


async def test_v3_battery_transition_values_are_exposed_unchanged(
    hass, setup_entry, mock_api, freezer
):
    freezer.move_to("2026-10-19T12:00:00Z")
    steps = _battery_fixture()["v3"][:4]
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    registry = er.async_get(hass)
    percentage_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-battery_percentage"
    )
    minutes_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-battery_minutes"
    )
    assert registry.async_get(percentage_id).unique_id == f"{SERIAL}-battery_percentage"
    assert registry.async_get(minutes_id).unique_id == f"{SERIAL}-battery_minutes"

    for step in steps:
        mock_api.get_properties.return_value = _v3_response(step["vitals"])
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert (
            coordinator.sock.properties["battery_percentage"] == step["vitals"]["bat"]
        )
        assert hass.states.get(percentage_id).state == f"{step['vitals']['bat']}.0"
        assert (
            registry.async_get_entity_id(
                "sensor", DOMAIN, f"{SERIAL}-battery_percentage"
            )
            == percentage_id
        )
        if step["vitals"]["chg"]:
            assert hass.states.get(minutes_id).state == "unavailable"
        else:
            assert hass.states.get(minutes_id).state == f"{step['vitals']['btt']}.0"
        freezer.tick(timedelta(seconds=5))


async def test_v3_battery_spike_is_isolated_between_socks(hass, config_entry, mock_api):
    second_serial = "SYNTHETIC-SOCK-002"
    mock_api.get_devices.return_value = {
        "response": [device(), device(second_serial, 2)]
    }
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    fixture = _battery_fixture()["v3"]
    spike = _v3_response(fixture[1]["vitals"])
    baseline = _v3_response(fixture[0]["vitals"])

    async def response(_api, serial):
        return spike if serial == SERIAL else baseline

    mock_api.get_properties.side_effect = response
    coordinators = hass.data[DOMAIN][config_entry.entry_id]
    await coordinators[SERIAL].async_refresh()
    await coordinators[second_serial].async_refresh()
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    first_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-battery_percentage"
    )
    second_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{second_serial}-battery_percentage"
    )
    assert hass.states.get(first_id).state == "100.0"
    assert hass.states.get(second_id).state == "50.0"
    assert registry.async_get(first_id).unique_id == f"{SERIAL}-battery_percentage"
    assert (
        registry.async_get(second_id).unique_id == f"{second_serial}-battery_percentage"
    )


async def test_v3_missing_battery_and_unknown_charging_remain_explicit(
    hass, setup_entry, mock_api
):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    registry = er.async_get(hass)
    percentage_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-battery_percentage"
    )
    assert registry.async_get(percentage_id).unique_id == f"{SERIAL}-battery_percentage"
    minutes_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-battery_minutes"
    )
    steps = _battery_fixture()["v3"]

    mock_api.get_properties.return_value = _v3_response(steps[4]["vitals"])
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(percentage_id).state == "50.0"
    assert hass.states.get(minutes_id).state == "unavailable"

    mock_api.get_properties.return_value = _v3_response(steps[5]["vitals"])
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert "battery_percentage" not in coordinator.sock.properties
    assert hass.states.get(percentage_id).state == "unknown"
    assert hass.states.get(minutes_id).state == "400.0"


async def test_v2_battery_value_and_missing_minutes(hass, config_entry, mock_api):
    steps = _battery_fixture()["v2"]
    mock_api.get_properties.return_value = load_fixture("update_properties_v2.json")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    registry = er.async_get(hass)
    percentage_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-battery_percentage"
    )
    assert (
        registry.async_get_entity_id("sensor", DOMAIN, f"{SERIAL}-battery_minutes")
        is None
    )

    for step in steps:
        response = load_fixture("update_properties_v2.json")
        response["response"]["BATT_LEVEL"]["value"] = step["battery"]
        response["response"]["CHARGE_STATUS"]["value"] = step["charging"]
        mock_api.get_properties.return_value = response
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert coordinator.sock.properties["battery_percentage"] == step["battery"]
        assert hass.states.get(percentage_id).state == str(step["battery"])
        assert (
            registry.async_get_entity_id(
                "sensor", DOMAIN, f"{SERIAL}-battery_percentage"
            )
            == percentage_id
        )
