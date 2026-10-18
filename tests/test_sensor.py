"""Sensors, charging, V2 support, measurement validity and freshness."""

import json
from datetime import timedelta

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.owlet.const import DOMAIN
from custom_components.owlet.sensor import SENSORS, OwletSensor

from .fixture_data import SERIAL, properties
from .regressions import InvalidOxygenDefect, StaleMeasurementDefect


def sensor_id(hass, key):
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{SERIAL}-{key}")


@pytest.mark.parametrize(
    ("sleep", "expected"),
    [(8, "light_sleep"), (1, "awake"), (15, "deep_sleep"), (0, "unknown")],
)
async def test_sensor_values(hass, setup_entry, mock_api, sleep, expected):
    mock_api.get_properties.return_value = properties(sleep_state=sleep)
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 8
    for key, value in {
        "battery_percentage": "50.0",
        "battery_minutes": "400.0",
        "heart_rate": "100.0",
        "oxygen_saturation": "98.0",
        "oxygen_10_av": "97.0",
        "signal_strength": "-30.0",
        "skin_temperature": "34",
        "sleep_state": expected,
    }.items():
        assert hass.states.get(sensor_id(hass, key)).state == value


async def test_sensor_update_and_charging(hass, setup_entry, mock_api):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(charging=1, battery_percentage=80)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "battery_percentage")).state == "80.0"
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == "unavailable"
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "unavailable"
    assert hass.states.get(sensor_id(hass, "signal_strength")).state == "-30.0"


async def test_v2_sensors(hass, config_entry, mock_api):
    mock_api.get_properties.return_value = properties(version=2)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4
    assert hass.states.get(sensor_id(hass, "heart_rate")).state == "100"
    assert hass.states.get(sensor_id(hass, "oxygen_saturation")).state == "98"
    assert sensor_id(hass, "sleep_state") is None
    assert sensor_id(hass, "oxygen_10_av") is None


@pytest.mark.parametrize("average", [-1, 101, 255])
async def test_invalid_oxygen_average_unavailable(hass, setup_entry, mock_api, average):
    mock_api.get_properties.return_value = properties(oxygen_10_av=average)
    await hass.data[DOMAIN][setup_entry.entry_id][SERIAL].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(sensor_id(hass, "oxygen_10_av")).state == "unavailable"


@pytest.mark.xfail(
    strict=True,
    raises=InvalidOxygenDefect,
    reason="AUDIT: instantaneous oxygen sentinel validation missing; roadmap PR 3",
)
async def test_oxygen_sentinel_unavailable(hass, setup_entry, mock_api):
    mock_api.get_properties.return_value = properties(oxygen_saturation=255)
    await hass.data[DOMAIN][setup_entry.entry_id][SERIAL].async_refresh()
    await hass.async_block_till_done()
    state = hass.states.get(sensor_id(hass, "oxygen_saturation")).state
    if state == "255.0":
        raise InvalidOxygenDefect("Known oxygen sentinel 255 is still available")
    assert state == "unavailable"


@pytest.mark.xfail(
    strict=True,
    raises=StaleMeasurementDefect,
    reason="AUDIT: old source timestamps accepted; roadmap PR 3 defines freshness policy",
)
async def test_old_source_measurement_unavailable(hass, setup_entry, mock_api, freezer):
    freezer.move_to("2026-10-18T12:00:00Z")
    mock_api.get_properties.return_value = properties(updated_at="2000-01-01T00:00:00Z")
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.sock.properties["last_updated"] == "2000/01/01 00:00:00"
    state = hass.states.get(sensor_id(hass, "heart_rate")).state
    if state == "100.0":
        raise StaleMeasurementDefect(
            "A years-old source measurement remains available after a successful poll"
        )
    assert state == "unavailable"


async def test_identical_values_with_new_source_time(
    hass, setup_entry, mock_api, freezer
):
    freezer.move_to("2026-10-18T12:00:00Z")
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    for timestamp in ("2026-10-18T12:00:00Z", "2026-10-18T12:00:05Z"):
        mock_api.get_properties.return_value = properties(updated_at=timestamp)
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(sensor_id(hass, "heart_rate")).state == "100.0"
        freezer.tick(timedelta(seconds=5))
    assert coordinator.sock.properties["last_updated"] == "2026/10/18 12:00:05"


@pytest.mark.xfail(
    strict=True,
    raises=KeyError,
    reason="AUDIT: disappearing optional properties break getters; roadmap PR 3",
)
async def test_missing_measurement_is_unknown(hass, setup_entry, mock_api):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    payload = properties()
    vitals = json.loads(payload["response"]["REAL_TIME_VITALS"]["value"])
    del vitals["hr"]
    payload["response"]["REAL_TIME_VITALS"]["value"] = json.dumps(vitals)
    mock_api.get_properties.return_value = payload
    await coordinator._async_update_data()
    entity = OwletSensor(
        coordinator,
        next(description for description in SENSORS if description.key == "heart_rate"),
    )
    try:
        assert entity.native_value is None
    except KeyError as err:
        assert err.args == ("heart_rate",)
        raise
