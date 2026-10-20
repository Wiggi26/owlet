"""Base class for Owlet entities."""

import re

from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OwletCoordinator


class OwletBaseEntity(CoordinatorEntity[OwletCoordinator], Entity):
    """Base class for Owlet Sock entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OwletCoordinator,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.sock = coordinator.sock

    def _property_value(self, key: str) -> object:
        """Read a normalized value, withholding flags rejected in this poll."""
        if key in self.coordinator.invalid_flags:
            return None
        return self.sock.properties.get(key)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info of the device."""
        mac = getattr(self.sock, "mac", None)
        connections = None
        if isinstance(mac, str):
            formatted_mac = format_mac(mac)
            if re.fullmatch(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", formatted_mac):
                mac_bytes = bytes.fromhex(formatted_mac.replace(":", ""))
                if any(mac_bytes) and (mac_bytes[0] & 1) == 0:
                    connections = {("mac", formatted_mac)}

        hw_version = getattr(self.sock, "hw_version", None)
        if not isinstance(hw_version, str) or not hw_version.strip():
            hw_version = None

        return DeviceInfo(
            identifiers={(DOMAIN, self.sock.serial)},
            name=f"Owlet Sock {self.sock.serial}",
            connections=connections,
            suggested_area="Nursery",
            configuration_url="https://my.owletcare.com/",
            manufacturer="Owlet Baby Care",
            model=getattr(self.sock, "model", None),
            sw_version=getattr(self.sock, "sw_version", None),
            hw_version=hw_version,
        )
