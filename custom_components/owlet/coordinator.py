"""Owlet integration coordinator class."""

from __future__ import annotations

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

    async def _async_update_data(self) -> None:
        """Fetch the data from the device."""
        try:
            properties = await self.sock.update_properties()
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
