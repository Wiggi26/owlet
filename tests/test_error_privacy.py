"""Synthetic privacy boundaries for cloud failures and malformed responses."""

import asyncio
import logging
import traceback
from contextlib import nullcontext
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletDevicesError,
    OwletEmailError,
    OwletError,
    OwletPasswordError,
)

from custom_components.owlet import async_setup_entry
from custom_components.owlet.const import DOMAIN

from .fixture_data import INPUT, SERIAL, TOKENS, properties

# All markers are independently invented; no account or device data is captured.
PRIVATE = {
    "username": INPUT["username"],
    "password": INPUT["password"],
    "access": TOKENS["api_token"],
    "refresh": TOKENS["refresh"],
    "device": SERIAL,
    "network": "192.0.2.217",
    "reading": "synthetic-private-reading",
    "unexpected": "synthetic-unreviewed-field",
}


def private_error(kind=RuntimeError):
    """Put nested private fields in text, notes and an explicit exception chain."""
    error = kind({"unexpected": [{"nested": PRIVATE}]})
    error.__cause__ = ValueError({"raw_response": PRIVATE})
    error.add_note(str({"note": PRIVATE}))
    return error


def assert_private_absent(text):
    """Report only a failed privacy assertion, never the captured payload."""
    assert not any(marker in text for marker in PRIVATE.values())


def captured_messages(caplog):
    """Include traceback formatting, not only the rendered log message."""
    return "\n".join(
        logging.Formatter().format(record)
        for record in caplog.records
        if record.name.startswith("custom_components.owlet")
    )


@pytest.mark.parametrize(
    "stage", ["constructor", "authenticate", "get_devices", "sock"]
)
@pytest.mark.parametrize(
    ("kind", "category", "raised"),
    [
        (OwletAuthenticationError, "Credentials expired", ConfigEntryAuthFailed),
        (OwletEmailError, "Credentials expired", ConfigEntryAuthFailed),
        (OwletPasswordError, "Credentials expired", ConfigEntryAuthFailed),
        (OwletConnectionError, "Error connecting", ConfigEntryNotReady),
        (OwletDevicesError, "No owlet devices", None),
        (OwletError, "Unexpected error setting up Owlet", None),
        (RuntimeError, "Unexpected error setting up Owlet", None),
    ],
)
async def test_setup_failure_privacy(
    hass, config_entry, mock_api, caplog, stage, kind, category, raised
):
    original, options = dict(config_entry.data), dict(config_entry.options)
    error = private_error(kind)
    mock_api.authenticate.return_value = None
    target = {
        "constructor": "custom_components.owlet.OwletAPI",
        "sock": "custom_components.owlet.Sock",
    }.get(stage)
    if target is None:
        getattr(mock_api, stage).side_effect = error
    with patch(target, side_effect=error) if target else nullcontext():
        if raised:
            with pytest.raises(raised) as caught:
                await async_setup_entry(hass, config_entry)
            rendered = "".join(traceback.format_exception(caught.value))
            assert caught.value.__cause__ is None
            assert caught.value.__suppress_context__
        else:
            assert not await async_setup_entry(hass, config_entry)
            rendered = ""
    text = captured_messages(caplog) + rendered
    assert_private_absent(text)
    assert category in text
    assert config_entry.data == original
    assert config_entry.options == options


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"response": {PRIVATE["unexpected"]: PRIVATE}},
        {"response": [{"device": PRIVATE["device"]}]},
        {"response": [{"device": {PRIVATE["unexpected"]: PRIVATE}}]},
        {"response": [], "tokens": [PRIVATE]},
    ],
    ids=["missing", "nested", "device-type", "missing-serial", "token-type"],
)
async def test_malformed_setup_privacy(hass, config_entry, mock_api, caplog, payload):
    mock_api.get_devices.return_value = payload
    assert not await async_setup_entry(hass, config_entry)
    text = captured_messages(caplog)
    assert_private_absent(text)
    assert "Unexpected error setting up Owlet" in text


@pytest.mark.parametrize(
    ("kind", "category", "raised"),
    [
        (OwletAuthenticationError, "Authentication failed", ConfigEntryAuthFailed),
        (OwletConnectionError, "Error connecting to Owlet", UpdateFailed),
        (OwletError, "Error updating Owlet data", UpdateFailed),
        (TimeoutError, "Timeout updating Owlet data", UpdateFailed),
        (RuntimeError, "Unexpected error updating Owlet data", UpdateFailed),
    ],
)
async def test_poll_failure_privacy(
    hass, setup_entry, mock_api, caplog, kind, category, raised
):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    saved = dict(setup_entry.data), dict(setup_entry.options)
    mock_api.get_properties.side_effect = private_error(kind)
    with pytest.raises(raised) as caught:
        await coordinator._async_update_data()
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__
    text = "".join(traceback.format_exception(caught.value))
    assert_private_absent(text)
    assert category in text
    if kind is not OwletAuthenticationError:
        await coordinator.async_refresh()
        assert not coordinator.last_update_success
        assert_private_absent(captured_messages(caplog))
        assert category in captured_messages(caplog)
        mock_api.get_properties.side_effect = None
        mock_api.get_properties.return_value = properties()
        await coordinator.async_refresh()
        assert coordinator.last_update_success
    assert (dict(setup_entry.data), dict(setup_entry.options)) == saved


@pytest.mark.parametrize("value", [PRIVATE["reading"], PRIVATE, [PRIVATE]])
async def test_malformed_poll_privacy(hass, setup_entry, mock_api, caplog, value):
    coordinator = hass.data[DOMAIN][setup_entry.entry_id][SERIAL]
    mock_api.get_properties.return_value = properties(heart_rate=value)
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    text = captured_messages(caplog)
    assert_private_absent(text)
    assert "Unexpected error updating Owlet data" in text


@pytest.mark.parametrize(
    ("reauth", "stage"),
    [
        (False, "constructor"),
        (False, "authenticate"),
        (False, "validate"),
        (False, "tokens"),
        (True, "constructor"),
        (True, "authenticate"),
        (True, "tokens"),
    ],
)
async def test_flow_unexpected_failure_privacy(
    hass, config_entry, mock_api, caplog, reauth, stage
):
    if reauth:
        context = {
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        }
        user_input = {"password": INPUT["password"]}
    else:
        # An existing unrelated account permits exercising the real user flow.
        hass.config_entries.async_update_entry(
            config_entry, unique_id="other@example.invalid"
        )
        context = {"source": config_entries.SOURCE_USER}
        user_input = INPUT
    result = await hass.config_entries.flow.async_init(DOMAIN, context=context)
    original, options = dict(config_entry.data), dict(config_entry.options)
    if stage == "tokens":
        mock_api.authenticate.return_value = [PRIVATE]
    elif stage != "constructor":
        getattr(
            mock_api, "validate_authentication" if stage == "validate" else stage
        ).side_effect = private_error()
    with (
        patch(
            "custom_components.owlet.config_flow.OwletAPI", side_effect=private_error()
        )
        if stage == "constructor"
        else nullcontext()
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == ({} if reauth else {"base": "unknown"})
    text = captured_messages(caplog)
    assert_private_absent(text)
    assert ("reauthenticating" if reauth else "authenticating") in text
    assert config_entry.data == original
    assert config_entry.options == options


@pytest.mark.parametrize("boundary", ["setup", "poll", "initial", "reauth"])
async def test_cancellation_propagates(hass, config_entry, mock_api, boundary):
    if boundary == "poll":
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        mock_api.get_properties.side_effect = asyncio.CancelledError()
        coordinator = hass.data[DOMAIN][config_entry.entry_id][SERIAL]
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_update_data()
        return
    mock_api.authenticate.side_effect = asyncio.CancelledError()
    if boundary == "setup":
        with pytest.raises(asyncio.CancelledError):
            await async_setup_entry(hass, config_entry)
        return
    if boundary == "reauth":
        context = {
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        }
        user_input = {"password": INPUT["password"]}
    else:
        hass.config_entries.async_update_entry(
            config_entry, unique_id="other@example.invalid"
        )
        context = {"source": config_entries.SOURCE_USER}
        user_input = INPUT
    result = await hass.config_entries.flow.async_init(DOMAIN, context=context)
    with pytest.raises(asyncio.CancelledError):
        await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
