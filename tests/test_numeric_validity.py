"""Numeric validity at the normalized sensor boundary and real parser paths."""

import json

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.owlet.const import DOMAIN
from custom_components.owlet.sensor import (
    SENSORS,
    OwletOxygenAverageSensor,
    OwletSensor,
)

from .fixture_data import SERIAL, device, properties
from .test_sensor import sensor_id


@pytest.mark.parametrize(
    "value",
    [None, True, False, "98", "bad", [], {}, float("nan"), float("inf"), -float("inf")],
)
async def test_normalized_invalid_numerics_are_unknown(hass, setup_entry, value):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    for description in (*SENSORS, OwletOxygenAverageSensor.entity_description):
        coordinator.sock.properties[description.key] = value
        assert OwletSensor(coordinator, description).native_value is None
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == "unknown"
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "unavailable"
    assert hass.states.get(sensor_id(hass, "oxygen_10_av")).state == "unavailable"
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == "100.0"
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "98.0"
    assert hass.states.get(sensor_id(hass, "oxygen_10_av")).state == "97.0"


@pytest.mark.parametrize("value", [-1000, 0, 1000, 1.25])
async def test_other_finite_numerics_keep_their_values(hass, setup_entry, value):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    for description in SENSORS:
        if description.key == "oxygen_saturation":
            continue
        coordinator.sock.properties[description.key] = value
        assert OwletSensor(coordinator, description).native_value == value


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize("oxygen", [-1, 0, 100, 101, 255])
async def test_oxygen_bounds_and_recovery_through_polling(
    hass, config_entry, mock_api, version, oxygen
):
    mock_api.get_properties.return_value = properties(version)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    entity_id = sensor_id(hass, "oxygen_saturation")
    registry = er.async_get(hass)
    before = registry.async_get(entity_id)
    mock_api.get_properties.return_value = properties(version, oxygen_saturation=oxygen)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes["unit_of_measurement"] == "%"
    assert state.state == (
        str(float(oxygen) if version == 3 else oxygen)
        if 0 <= oxygen <= 100
        else "unavailable"
    )
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == (
        "100.0" if version == 3 else "100"
    )
    mock_api.get_properties.return_value = properties(version)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == ("98.0" if version == 3 else "98")
    assert registry.async_get(entity_id) == before
    assert before.unique_id == f"{SERIAL}-oxygen_saturation"


@pytest.mark.parametrize("oxygen", [0.01, 99.99, -0.01, 100.01])
async def test_fractional_oxygen_boundaries(hass, setup_entry, mock_api, oxygen):
    mock_api.get_properties.return_value = properties(
        oxygen_saturation=oxygen, oxygen_10_av=oxygen
    )
    await hass.data[DOMAIN][setup_entry.entry_id][SERIAL].async_refresh()
    await hass.async_block_till_done()
    for key in ("oxygen_saturation", "oxygen_10_av"):
        assert hass.states.get(sensor_id(hass, key)).state == (
            str(oxygen) if 0 <= oxygen <= 100 else "unavailable"
        )


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), -float("inf"), "NaN", "Infinity"]
)
async def test_nonfinite_float_fields_through_polling(
    hass, setup_entry, mock_api, value
):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(
        oxygen_saturation=value, heart_rate=value, oxygen_10_av=value
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "unavailable"
    assert hass.states.get(sensor_id(hass, "oxygen_10_av")).state == "unavailable"
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == "unknown"
    mock_api.get_properties.return_value = properties()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == "100.0"
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "98.0"
    assert hass.states.get(sensor_id(hass, "oxygen_10_av")).state == "97.0"


async def test_missing_oxygen_and_average_are_unavailable_then_recover(
    hass, setup_entry, mock_api
):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    payload = properties()
    vitals = json.loads(payload["response"]["REAL_TIME_VITALS"]["value"])
    del vitals["ox"], vitals["oxta"]
    payload["response"]["REAL_TIME_VITALS"]["value"] = json.dumps(vitals)
    mock_api.get_properties.return_value = payload
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "unavailable"
    assert hass.states.get(sensor_id(hass, "oxygen_10_av")).state == "unavailable"
    mock_api.get_properties.return_value = properties()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "98.0"
    assert hass.states.get(sensor_id(hass, "oxygen_10_av")).state == "97.0"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("oxygen_saturation", None, TypeError),
        ("oxygen_saturation", "bad", ValueError),
        ("oxygen_saturation", [], TypeError),
        ("skin_temperature", float("nan"), ValueError),
        ("skin_temperature", float("inf"), OverflowError),
    ],
)
async def test_raw_parser_rejects_values_before_sensor_boundary(
    hass, setup_entry, mock_api, field, value, error
):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(**{field: value})
    with pytest.raises(error):
        await coordinator.sock.update_properties()
    mock_api.get_properties.return_value = properties()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "98.0"


@pytest.mark.parametrize("value", [True, "1"])
async def test_raw_parser_coerces_values_before_sensor_boundary(
    hass, setup_entry, mock_api, value
):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(heart_rate=value)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.sock.properties["heart_rate"] == 1.0
    assert type(coordinator.sock.properties["heart_rate"]) is float
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == "1.0"


async def test_invalid_oxygen_isolated_across_socks(hass, config_entry, mock_api):
    second = "SYNTHETIC-SOCK-002"
    mock_api.get_devices.return_value = {"response": [device(), device(second, 2)]}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    async def readings(_api, serial):
        return properties(oxygen_saturation=255 if serial == SERIAL else 99)

    mock_api.get_properties.side_effect = readings
    coordinators = hass.data[DOMAIN][config_entry.entry_id]
    for coordinator in coordinators.values():
        await coordinator.async_refresh()
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    second_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{second}-oxygen_saturation"
    )
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "unavailable"
    assert hass.states.get(second_id).state == "99.0"
