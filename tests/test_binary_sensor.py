"""Binary sensor states and unsupported sleep-state regression."""

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.owlet.binary_sensor import OwletAwakeSensor
from custom_components.owlet.const import DOMAIN
from custom_components.owlet.sensor import OwletSleepSensor

from .fixture_data import SERIAL, properties


def entity_id(hass, key):
    return er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"{SERIAL}-{key}"
    )


@pytest.mark.parametrize(
    ("sleep", "charging", "expected"),
    [(8, 0, "off"), (1, 0, "on"), (15, 0, "off"), (8, 1, "unavailable")],
)
async def test_binary_states(hass, setup_entry, mock_api, sleep, charging, expected):
    mock_api.get_properties.return_value = properties(
        sleep_state=sleep, charging=charging, high_heart_rate_alert=True
    )
    await hass.data[DOMAIN][setup_entry.entry_id][SERIAL].async_refresh()
    await hass.async_block_till_done()
    assert len(hass.states.async_all("binary_sensor")) == 10
    assert hass.states.get(entity_id(hass, "sleep_state")).state == expected
    assert hass.states.get(entity_id(hass, "charging")).state == (
        "on" if charging else "off"
    )
    assert hass.states.get(entity_id(hass, "high_heart_rate_alert")).state == "on"
    assert hass.states.get(entity_id(hass, "sock_off")).state == "off"


async def test_binary_sensors_v2(hass, config_entry, mock_api):
    mock_api.get_properties.return_value = properties(version=2)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("binary_sensor")) == 9
    assert entity_id(hass, "sleep_state") is None
    for key in (
        "charging",
        "low_heart_rate_alert",
        "high_heart_rate_alert",
        "low_oxygen_alert",
        "low_battery_alert",
        "critical_battery_alert",
        "critical_oxygen_alert",
        "sock_disconnected",
        "sock_off",
    ):
        assert hass.states.get(entity_id(hass, key)).state == "off"


@pytest.mark.parametrize(
    "sleep",
    [0, 2, 99],
)
async def test_unknown_sleep_not_awake(hass, setup_entry, mock_api, sleep):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(sleep_state=sleep)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, "sleep_state")).state == "unknown"
    enum_entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-sleep_state"
    )
    assert hass.states.get(enum_entity_id).state == "unknown"


@pytest.mark.parametrize("sleep", ["8", True, 8.0, None, [], {}])
async def test_malformed_sleep_state_is_unknown(hass, setup_entry, sleep):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    coordinator.sock.properties["sleep_state"] = sleep
    assert OwletAwakeSensor(coordinator).is_on is None
    assert OwletSleepSensor(coordinator).native_value == "unknown"


async def test_missing_sleep_state_is_unknown(hass, setup_entry):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    coordinator.sock.properties.pop("sleep_state")
    assert OwletAwakeSensor(coordinator).is_on is None
    assert OwletSleepSensor(coordinator).native_value == "unknown"


async def test_sleep_state_recovers_without_changing_identity(
    hass, setup_entry, mock_api
):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    registry = er.async_get(hass)
    awake_id = entity_id(hass, "sleep_state")
    enum_id = registry.async_get_entity_id("sensor", DOMAIN, f"{SERIAL}-sleep_state")
    awake_unique_id = registry.async_get(awake_id).unique_id
    enum_unique_id = registry.async_get(enum_id).unique_id

    mock_api.get_properties.return_value = properties(sleep_state=99)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(awake_id).state == "unknown"
    assert hass.states.get(enum_id).state == "unknown"

    mock_api.get_properties.return_value = properties(sleep_state=1)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(awake_id).state == "on"
    assert hass.states.get(enum_id).state == "awake"
    assert entity_id(hass, "sleep_state") == awake_id
    assert registry.async_get(awake_id).unique_id == awake_unique_id
    assert registry.async_get(enum_id).unique_id == enum_unique_id
