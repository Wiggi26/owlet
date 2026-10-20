"""Owlet integration coordinator class."""

from __future__ import annotations

import json
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletError,
)
from pyowletapi.sock import Sock

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_RAW_ALERT_FLAGS = {
    "high_oxygen_alert": "HIGH_OX_ALRT",
    "low_battery_alert": "LOW_BATT_ALRT",
    "low_heart_rate_alert": "LOW_HR_ALRT",
    "high_heart_rate_alert": "HIGH_HR_ALRT",
    "low_oxygen_alert": "LOW_OX_ALRT",
    "lost_power_alert": "LOST_POWER_ALRT",
    "sock_disconnected": "SOCK_DISCON_ALRT",
    "sock_off": "SOCK_OFF",
    "critical_battery_alert": "CRIT_BATT_ALRT",
    "critical_oxygen_alert": "CRIT_OX_ALRT",
}


def _raw_value(raw: object, key: str) -> object:
    """Read a raw property value without interpreting a missing wrapper."""
    if not isinstance(raw, dict):
        return None
    wrapped = raw.get(key)
    return wrapped.get("value") if isinstance(wrapped, dict) else None


def _invalid_raw_flags(raw: object, version: int) -> frozenset[str]:
    """Identify non-binary flags in a successfully normalized raw snapshot."""
    values = {key: _raw_value(raw, source) for key, source in _RAW_ALERT_FLAGS.items()}
    values.update(charging=None, base_station_on=None)
    if version == 2:
        values.update(
            charging=_raw_value(raw, "CHARGE_STATUS"),
            base_station_on=_raw_value(raw, "BASE_STATION_ON"),
        )
    elif version == 3:
        try:
            vitals = json.loads(_raw_value(raw, "REAL_TIME_VITALS"))
        except (TypeError, ValueError):
            vitals = None
        if isinstance(vitals, dict):
            values.update(charging=vitals.get("chg"), base_station_on=vitals.get("bso"))
    return frozenset(
        key
        for key, value in values.items()
        if not (type(value) is bool or type(value) is int and value in (0, 1))
    )


class OwletCoordinator(DataUpdateCoordinator):
    """Coordinator is responsible for querying the device at a specified route."""

    def __init__(
        self, hass: HomeAssistant, sock: Sock, interval, entry: ConfigEntry
    ) -> None:
        """Initialise a custom coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.sock = sock
        self.config_entry: ConfigEntry = entry
        self.invalid_flags: frozenset[str] = frozenset()

    async def _async_update_data(self) -> None:
        """Fetch the data from the device."""
        try:
            properties = await self.sock.update_properties()
            self.invalid_flags = _invalid_raw_flags(
                self.sock.raw_properties, self.sock.version
            )
            if "tokens" in properties:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **properties["tokens"]},
                )
        except OwletAuthenticationError:
            raise ConfigEntryAuthFailed("Authentication failed") from None
        except OwletConnectionError:
            raise UpdateFailed("Error connecting to Owlet") from None
        except OwletError:
            raise UpdateFailed("Error updating Owlet data") from None
        except TimeoutError:
            raise UpdateFailed("Timeout updating Owlet data") from None
        except Exception:
            raise UpdateFailed("Unexpected error updating Owlet data") from None
