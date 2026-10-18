"""Binary sensor states and unsupported sleep-state regression."""

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.owlet.binary_sensor import OwletAwakeSensor
from custom_components.owlet.const import DOMAIN

from .fixture_data import SERIAL, properties
from .regressions import UnknownSleepDefect


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


@pytest.mark.xfail(
    strict=True,
    raises=UnknownSleepDefect,
    reason="AUDIT: unknown sleep code becomes awake; roadmap PR 3",
)
async def test_unknown_sleep_not_awake(hass, setup_entry, mock_api):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(sleep_state=0)
    await coordinator._async_update_data()
    assert coordinator.sock.properties["sleep_state"] == 0
    sensor = OwletAwakeSensor(coordinator)
    if sensor.is_on is True:
        raise UnknownSleepDefect("Unknown sleep code 0 is interpreted as awake")
    assert sensor.is_on is None
