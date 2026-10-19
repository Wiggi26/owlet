"""Characterize Core title exposure separately from sanitized cloud failures."""

import logging
from importlib.metadata import version
from pathlib import Path

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType
from pyowletapi.exceptions import OwletAuthenticationError, OwletConnectionError

from custom_components.owlet.const import DOMAIN

from .fixture_data import INPUT, SERIAL, TOKENS

CORE_VERSION = version("homeassistant")
RETRY_PROFILE = {
    "2025.12.4": ("homeassistant.config_entries", logging.DEBUG),
    "2026.10.2": ("custom_components.owlet", logging.INFO),
}[CORE_VERSION]
TITLES = [
    pytest.param(INPUT["username"], id="default-username"),
    pytest.param("Synthetic room", id="custom-neutral"),
    pytest.param("Synthetic person alternate@example.invalid", id="custom-identifying"),
]
PRIVATE = {
    "username": INPUT["username"],
    "password": INPUT["password"],
    "access": TOKENS["api_token"],
    "refresh": TOKENS["refresh"],
    "device": SERIAL,
    "network": "192.0.2.218",
    "reading": "synthetic-core-private-reading",
    "unexpected": "synthetic-core-unreviewed-field",
    "cause": "synthetic-core-private-cause",
    "note": "synthetic-core-private-note",
}
LOGGERS = ("homeassistant.config_entries", "custom_components.owlet")


def cloud_error(kind):
    """Create independently invented nested data, a cause and a note."""
    error = kind({"unexpected": [{"nested": PRIVATE}]})
    error.__cause__ = ValueError(PRIVATE["cause"])
    error.add_note(PRIVATE["note"])
    return error


def relevant_records(caplog):
    """Include Core's integration logger routing and coordinator records."""
    return [
        record
        for record in caplog.records
        if any(
            record.name == name or record.name.startswith(f"{name}.")
            for name in LOGGERS
        )
    ]


def formatted(records):
    """Render messages and complete visible exception chains at DEBUG too."""
    formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
    return "\n".join(formatter.format(record) for record in records)


def assert_exposure(text, *, title=None):
    """Keep assertion output free of the nested exception payload."""
    for marker in PRIVATE.values():
        assert (marker in text) == (title is not None and marker in title)
    if title is not None:
        assert title in text


def entry_snapshot(entry):
    """Track account configuration independently of expected runtime state."""
    return (
        entry.entry_id,
        entry.unique_id,
        entry.title,
        entry.version,
        dict(entry.data),
        dict(entry.options),
    )


@pytest.fixture
def capture_core_logs(caplog):
    """Enable relevant real loggers without replacing Core's logging calls."""
    for name in LOGGERS:
        caplog.set_level(logging.DEBUG, logger=name)
    return caplog


@pytest.mark.parametrize("title", TITLES)
@pytest.mark.parametrize("stage", ["authenticate", "first-refresh"])
@pytest.mark.parametrize("failure", ["auth", "retry"])
async def test_core_setup_logs_title_but_not_raw_cloud_details(
    hass, config_entry, mock_api, capture_core_logs, title, stage, failure
):
    hass.config_entries.async_update_entry(config_entry, title=title)
    saved = entry_snapshot(config_entry)
    kind = OwletAuthenticationError if failure == "auth" else OwletConnectionError
    boundary = (
        mock_api.authenticate if stage == "authenticate" else mock_api.get_properties
    )
    boundary.side_effect = cloud_error(kind)
    capture_core_logs.clear()

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    records = relevant_records(capture_core_logs)
    core = [
        record
        for record in records
        if Path(record.pathname).name == "config_entries.py"
        and record.msg.startswith("Config entry '")
    ]
    assert len(core) == 1
    record = core[0]
    assert record.name == "homeassistant.config_entries"
    assert record.args[0] == title
    text = formatted(records)
    assert_exposure(text, title=title)
    if failure == "auth":
        assert record.levelno == logging.WARNING
        assert "could not authenticate" in record.getMessage()
        category = (
            "Credentials expired"
            if stage == "authenticate"
            else "Authentication failed"
        )
        assert category in record.getMessage()
        assert config_entry.state is ConfigEntryState.SETUP_ERROR
        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 1
        assert flows[0]["context"]["source"] == SOURCE_REAUTH
        assert flows[0]["context"]["entry_id"] == config_entry.entry_id
    else:
        assert record.levelno == RETRY_PROFILE[1]
        assert "Retrying in" in record.getMessage()
        assert config_entry.state is ConfigEntryState.SETUP_RETRY
        assert not hass.config_entries.flow.async_progress()
        if stage == "authenticate":
            assert "Error connecting to Owlet" in record.getMessage()

    trace_records = [record for record in records if record.exc_info]
    if CORE_VERSION == "2026.10.2":
        assert trace_records
        assert all(record.levelno == logging.DEBUG for record in trace_records)
        trace = formatted(trace_records)
        exception = (
            "ConfigEntryAuthFailed" if failure == "auth" else "ConfigEntryNotReady"
        )
        assert exception in trace
        if stage == "first-refresh" and failure == "retry":
            assert "UpdateFailed: Error connecting to Owlet" in trace
            assert "The above exception was the direct cause" in trace
    else:
        assert not trace_records
    assert entry_snapshot(config_entry) == saved


async def test_core_retry_after_reload_can_change_logger(
    hass, config_entry, mock_api, capture_core_logs
):
    mock_api.authenticate.side_effect = cloud_error(OwletConnectionError)
    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    saved = entry_snapshot(config_entry)
    capture_core_logs.clear()

    assert not await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    records = relevant_records(capture_core_logs)
    core = [
        record
        for record in records
        if Path(record.pathname).name == "config_entries.py"
        and record.msg.startswith("Config entry '")
    ]
    assert len(core) == 1
    assert (core[0].name, core[0].levelno) == RETRY_PROFILE
    assert "Error connecting to Owlet" in core[0].getMessage()
    assert_exposure(formatted(records), title=config_entry.title)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    assert entry_snapshot(config_entry) == saved


@pytest.mark.parametrize("title", TITLES)
async def test_polling_and_reauth_failure_logs_keep_sanitized_categories(
    hass, config_entry, mock_api, capture_core_logs, title
):
    hass.config_entries.async_update_entry(config_entry, title=title)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    saved = entry_snapshot(config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
    capture_core_logs.clear()
    mock_api.get_properties.side_effect = cloud_error(OwletAuthenticationError)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    records = relevant_records(capture_core_logs)
    text = formatted(records)
    assert_exposure(text)
    assert title not in text
    assert (
        "Authentication failed while fetching owlet data: Authentication failed" in text
    )
    trace_records = [record for record in records if record.exc_info]
    if CORE_VERSION == "2026.10.2":
        assert trace_records
        assert all(
            Path(record.pathname).name == "update_coordinator.py"
            for record in trace_records
        )
        assert "ConfigEntryAuthFailed: Authentication failed" in formatted(
            trace_records
        )
    else:
        assert not trace_records
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert flows[0]["context"]["entry_id"] == config_entry.entry_id
    assert flows[0]["context"]["title_placeholders"] == {"name": title}

    capture_core_logs.clear()
    mock_api.authenticate.side_effect = cloud_error(RuntimeError)
    result = await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"], {"password": INPUT["password"]}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    text = formatted(relevant_records(capture_core_logs))
    assert "Unexpected error reauthenticating with Owlet" in text
    assert_exposure(text)
    assert title not in text
    assert entry_snapshot(config_entry) == saved

    mock_api.authenticate.side_effect = None
    mock_api.get_properties.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"password": INPUT["password"]}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.state is ConfigEntryState.LOADED
    assert not hass.config_entries.flow.async_progress()
    assert entry_snapshot(config_entry) == saved
