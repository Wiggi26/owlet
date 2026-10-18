"""Configuration, authentication and reauthentication baseline."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType
from pyowletapi.exceptions import (
    OwletConnectionError,
    OwletCredentialsError,
    OwletDevicesError,
    OwletEmailError,
    OwletPasswordError,
)

from custom_components.owlet.const import DOMAIN

from .fixture_data import INPUT, TOKENS


async def test_form(hass, mock_api):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]
    assert entry.unique_id == INPUT["username"]
    assert entry.data == {"region": "europe", "username": INPUT["username"], **TOKENS}
    assert entry.options == {"scan_interval": 5}
    assert CONF_PASSWORD not in entry.data
    assert entry.version == 1


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (OwletPasswordError(), {"password": "invalid_password"}),
        (OwletEmailError(), {"username": "invalid_email"}),
        (OwletCredentialsError(), {"base": "invalid_credentials"}),
        (OwletDevicesError(), {"base": "no_devices"}),
        (OwletConnectionError(), {"base": "unknown"}),
        (TimeoutError(), {"base": "unknown"}),
        (RuntimeError("synthetic failure"), {"base": "unknown"}),
    ],
)
async def test_flow_errors(hass, mock_api, error, expected):
    mock_api.authenticate.side_effect = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == expected


async def test_duplicate_account(hass, config_entry, mock_api):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_api.authenticate.assert_not_awaited()


async def test_reauth_success(hass, config_entry, mock_api):
    identity = config_entry.entry_id
    original = dict(config_entry.data)
    options = dict(config_entry.options)
    rotated = {
        "api_token": "rotated-synthetic-access",
        "refresh": "rotated-synthetic-refresh",
        "expiry": TOKENS["expiry"] + 100,
    }
    mock_api.authenticate.return_value = rotated
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_REAUTH, "entry_id": identity}
    )
    assert result["step_id"] == "reauth_confirm"
    with patch.object(
        hass.config_entries, "async_reload", new=AsyncMock(return_value=True)
    ) as reload_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "replacement-synthetic-password"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.entry_id == identity
    assert config_entry.data == {**original, **rotated}
    assert config_entry.options == options
    assert config_entry.version == 1
    assert "password" not in config_entry.data
    reload_entry.assert_awaited_once_with(identity)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (OwletPasswordError(), {"password": "invalid_password"}),
        (RuntimeError("synthetic"), {}),
    ],
)
async def test_reauth_errors(hass, config_entry, mock_api, error, expected):
    original = dict(config_entry.data)
    mock_api.authenticate.side_effect = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"password": "synthetic-password"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == expected
    assert config_entry.data == original


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="AUDIT: current-Core options property has no setter; roadmap PR 2 removes this marker",
)
async def test_options_flow(hass, config_entry):
    try:
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
    except AttributeError as err:
        assert "config_entry" in str(err) and "no setter" in str(err)
        raise
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 10}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"scan_interval": 10}
