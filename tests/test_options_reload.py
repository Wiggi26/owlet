"""Saved polling options reload all socks without replacing registry identities."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pyowletapi.exceptions import OwletConnectionError

from custom_components.owlet.const import DOMAIN

from .fixture_data import SERIAL, device, properties


async def test_options_flow_reloads_all_socks(hass, config_entry, mock_api):
    """Saving options applies to both socks and retains existing customisations."""
    second = "SYNTHETIC-SOCK-002"
    mock_api.get_devices.return_value = {"response": [device(), device(second, 2)]}
    hass.config_entries.async_update_entry(
        config_entry,
        data={**config_entry.data, "synthetic_setting": "retained"},
        options={**config_entry.options, "synthetic_option": "retained"},
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    previous = dict(hass.data[DOMAIN][config_entry.entry_id])
    assert len(previous) == 2

    entities = er.async_get(hass)
    heart = entities.async_get_entity_id("sensor", DOMAIN, f"{SERIAL}-heart_rate")
    entities.async_update_entity(
        heart,
        new_entity_id="sensor.synthetic_custom_heart_rate",
        name="Synthetic custom name",
        icon="mdi:heart",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    devices = dr.async_get(hass)
    sock = next(
        entry
        for entry in dr.async_entries_for_config_entry(devices, config_entry.entry_id)
        if (DOMAIN, SERIAL) in entry.identifiers
    )
    devices.async_update_device(sock.id, name_by_user="Synthetic custom sock")
    entities_before = {
        entry.entity_id: (
            entry.id,
            entry.unique_id,
            entry.device_id,
            entry.name,
            entry.icon,
            entry.disabled_by,
        )
        for entry in er.async_entries_for_config_entry(entities, config_entry.entry_id)
    }
    devices_before = {
        entry.id: (entry.identifiers, entry.connections, entry.name_by_user)
        for entry in dr.async_entries_for_config_entry(devices, config_entry.entry_id)
    }
    saved_identity = (
        config_entry.entry_id,
        config_entry.unique_id,
        config_entry.version,
        config_entry.title,
    )
    saved_data = dict(config_entry.data)

    flow = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.config_entries.options.async_configure(
        flow["flow_id"], user_input={"scan_interval": 10}
    )
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.config_entries.async_get_entry(config_entry.entry_id) is config_entry
    assert saved_identity == (
        config_entry.entry_id,
        config_entry.unique_id,
        config_entry.version,
        config_entry.title,
    )
    assert config_entry.data == saved_data
    assert config_entry.options == {
        "scan_interval": 10,
        "synthetic_option": "retained",
    }
    running = hass.data[DOMAIN][config_entry.entry_id]
    assert set(running) == {SERIAL, second}
    for serial, coordinator in running.items():
        assert coordinator is not previous[serial]
        assert coordinator.update_interval == timedelta(seconds=10)
    assert len(config_entry.update_listeners) == 1
    assert len(entities_before) == 42
    assert {
        entry.entity_id: (
            entry.id,
            entry.unique_id,
            entry.device_id,
            entry.name,
            entry.icon,
            entry.disabled_by,
        )
        for entry in er.async_entries_for_config_entry(entities, config_entry.entry_id)
    } == entities_before
    assert {
        entry.id: (entry.identifiers, entry.connections, entry.name_by_user)
        for entry in dr.async_entries_for_config_entry(devices, config_entry.entry_id)
    } == devices_before
    reopened = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert reopened["data_schema"]({}) == {"scan_interval": 10}


async def test_data_updates_do_not_reload(hass, setup_entry, mock_api):
    """Persisting refreshed tokens must not restart polling or lose options."""
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    original = dict(setup_entry.data)
    rotated = {
        "api_token": "synthetic-rotated-access",
        "expiry": original["expiry"] + 300,
        "refresh": "synthetic-rotated-refresh",
    }
    mock_api.get_properties.return_value = {**properties(), "tokens": rotated}
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert setup_entry.data == {**original, **rotated}
    assert setup_entry.options == {"scan_interval": 5}
    assert hass.data[DOMAIN][setup_entry.entry_id][SERIAL] is coordinator
    mock_api.authenticate.assert_awaited_once()
    mock_api.get_devices.assert_awaited_once()
    assert len(setup_entry.update_listeners) == 1


async def test_listener_cleanup_and_repeated_options(hass, setup_entry, mock_api):
    """Repeated changes leave one listener, and unloading removes that listener."""
    for options, seconds in (
        ({"scan_interval": 10}, 10),
        ({}, 5),
        ({"scan_interval": 5}, 5),
    ):
        previous = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
        hass.config_entries.async_update_entry(setup_entry, options=options)
        await hass.async_block_till_done()
        current = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
        assert current is not previous
        assert current.update_interval == timedelta(seconds=seconds)
        assert setup_entry.options == options
        assert len(setup_entry.update_listeners) == 1

    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    assert setup_entry.state is ConfigEntryState.NOT_LOADED
    assert setup_entry.entry_id not in hass.data[DOMAIN]
    assert not setup_entry.update_listeners
    calls = mock_api.authenticate.await_count
    hass.config_entries.async_update_entry(setup_entry, options={"scan_interval": 15})
    await hass.async_block_till_done()
    assert setup_entry.state is ConfigEntryState.NOT_LOADED
    assert mock_api.authenticate.await_count == calls
    assert await hass.config_entries.async_setup(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert len(setup_entry.update_listeners) == 1
    assert hass.data[DOMAIN][setup_entry.entry_id][SERIAL].update_interval == timedelta(
        seconds=15
    )


async def test_options_reload_failure_and_recovery(hass, setup_entry, mock_api):
    """A transient reload failure retains the saved entry for a successful retry."""
    saved_data = dict(setup_entry.data)
    mock_api.authenticate.side_effect = OwletConnectionError()
    hass.config_entries.async_update_entry(setup_entry, options={"scan_interval": 10})
    await hass.async_block_till_done()
    assert setup_entry.state is ConfigEntryState.SETUP_RETRY
    assert setup_entry.entry_id not in hass.data[DOMAIN]
    assert not setup_entry.update_listeners
    assert setup_entry.data == saved_data
    assert setup_entry.options == {"scan_interval": 10}
    assert hass.config_entries.async_get_entry(setup_entry.entry_id) is setup_entry

    mock_api.authenticate.side_effect = None
    assert await hass.config_entries.async_reload(setup_entry.entry_id)
    await hass.async_block_till_done()
    assert setup_entry.state is ConfigEntryState.LOADED
    assert len(setup_entry.update_listeners) == 1
    assert setup_entry.data == saved_data
    assert setup_entry.options == {"scan_interval": 10}
    assert hass.data[DOMAIN][setup_entry.entry_id][SERIAL].update_interval == timedelta(
        seconds=10
    )
