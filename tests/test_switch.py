"""Base-station switch calls are synthetic, mocked and never reach Owlet."""

import json

import pytest
from homeassistant.helpers import entity_registry as er
from pyowletapi.api import OwletAPI

from custom_components.owlet.const import DOMAIN

from .fixture_data import SERIAL, properties


@pytest.mark.parametrize(
    ("service", "expected"), [("turn_on", "true"), ("turn_off", "false")]
)
async def test_switch_commands(hass, setup_entry, mock_api, service, expected):
    entity_id = er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"{SERIAL}-base_station_on"
    )
    await hass.services.async_call(
        "switch", service, {"entity_id": entity_id}, blocking=True
    )
    mock_api.post_command.assert_awaited_once()
    client, serial, command, payload = mock_api.post_command.call_args.args
    assert isinstance(client, OwletAPI)
    assert serial == SERIAL
    assert command == "BASE_STATION_ON_CMD"
    assert json.loads(payload["datapoint"]["value"])["val"] == expected


async def test_switch_state_from_poll(hass, setup_entry, mock_api):
    entity_id = er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"{SERIAL}-base_station_on"
    )
    assert hass.states.get(entity_id).state == "on"
    mock_api.get_properties.return_value = properties(base_station_on=False)
    await hass.data[DOMAIN][setup_entry.entry_id][SERIAL].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"
    mock_api.post_command.assert_not_awaited()
