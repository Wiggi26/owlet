"""Device metadata must reflect valid cloud facts without changing identity."""

from copy import deepcopy

import pytest
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.owlet.const import DOMAIN
from custom_components.owlet.entity import OwletBaseEntity

from .fixture_data import SERIAL, device, properties

_METADATA_CASES = (
    ("2.1", "02:00:00:00:00:01", "2.1", {("mac", "02:00:00:00:00:01")}),
    ("absent", None, None, set()),
    ("set-null", None, None, set()),
    ("", "02:00:00:00:00:01", None, {("mac", "02:00:00:00:00:01")}),
    (123, "02:00:00:00:00:01", None, {("mac", "02:00:00:00:00:01")}),
    (None, "absent", None, set()),
    (None, None, None, set()),
    (None, "unknown", None, set()),
    (None, "not-a-mac", None, set()),
    (None, "00:00:00:00:00:00", None, set()),
    (None, "ff:ff:ff:ff:ff:ff", None, set()),
    (None, "01:00:5e:00:00:01", None, set()),
    (None, "02:00:00:00:00:01", None, {("mac", "02:00:00:00:00:01")}),
)


@pytest.mark.parametrize("sock_version", [2, 3])
async def test_device_info_uses_only_valid_metadata(
    hass, config_entry, mock_api, sock_version
):
    """V2 and V3 devices omit unsupported facts and retain valid metadata."""
    mock_api.get_devices.return_value = {"response": [device()]}
    mock_api.get_properties.return_value = properties(version=sock_version)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    sock = coordinator.sock
    for hardware, mac, expected_hardware, expected_connections in _METADATA_CASES:
        if hardware == "absent":
            if hasattr(sock, "hw_version"):
                del sock.hw_version
        elif hardware == "set-null":
            sock.hw_version = None
        elif hardware is not None:
            sock.hw_version = hardware
        elif hasattr(sock, "hw_version"):
            del sock.hw_version

        if mac == "absent":
            del sock._mac
        else:
            sock._mac = mac

        info = OwletBaseEntity(coordinator).device_info
        assert info["identifiers"] == {(DOMAIN, SERIAL)}
        assert info["name"] == f"Owlet Sock {SERIAL}"
        assert info["model"] == "Synthetic model"
        assert info["sw_version"] == "test"
        assert info["hw_version"] == expected_hardware
        assert (info.get("connections") or set()) == expected_connections
        if expected_connections:
            assert info["connections"] == expected_connections


async def test_invalid_mac_values_do_not_merge_two_socks(hass, config_entry, mock_api):
    """Invalid shared MAC placeholders cannot merge distinct serial devices."""
    second = "SYNTHETIC-SOCK-002"
    first_device = device()
    second_device = device(second, 2)
    first_device["device"]["mac"] = "unknown"
    second_device["device"]["mac"] = "unknown"
    mock_api.get_devices.return_value = {"response": [first_device, second_device]}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = dr.async_get(hass)
    entries = dr.async_entries_for_config_entry(registry, config_entry.entry_id)
    assert len(entries) == 2
    by_serial = {
        next(
            identifier[1] for identifier in entry.identifiers if identifier[0] == DOMAIN
        ): entry
        for entry in entries
    }
    assert set(by_serial) == {SERIAL, second}
    assert by_serial[SERIAL].id != by_serial[second].id
    assert by_serial[SERIAL].connections == set()
    assert by_serial[second].connections == set()


async def test_metadata_reload_preserves_registry_customizations(
    hass, config_entry, mock_api
):
    """Changing optional metadata during reload preserves established identities."""
    mock_api.get_devices.return_value = {"response": [device()]}
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    registered = next(
        item
        for item in dr.async_entries_for_config_entry(
            device_registry, config_entry.entry_id
        )
        if (DOMAIN, SERIAL) in item.identifiers
    )
    entities = er.async_entries_for_device(
        entity_registry, registered.id, include_disabled_entities=True
    )
    ids_before = {entry.unique_id: entry.entity_id for entry in entities}
    selected = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}-heart_rate"
    )
    entity_registry.async_update_entity(
        selected,
        name="Synthetic custom name",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    saved_data, saved_options = (
        deepcopy(dict(config_entry.data)),
        dict(config_entry.options),
    )

    changed_device = device()
    changed_device["device"]["mac"] = None
    changed_device["device"].pop("model")
    mock_api.get_devices.return_value = {"response": [changed_device]}
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    after = er.async_entries_for_device(
        entity_registry, registered.id, include_disabled_entities=True
    )
    assert {entry.unique_id: entry.entity_id for entry in after} == ids_before
    assert entity_registry.async_get(selected).name == "Synthetic custom name"
    assert (
        entity_registry.async_get(selected).disabled_by is er.RegistryEntryDisabler.USER
    )
    assert config_entry.data == saved_data
    assert config_entry.options == saved_options
