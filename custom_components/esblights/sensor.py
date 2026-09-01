"""The ESB Lights sensor.

State is the color description ("purple", "signature white"). The hex codes,
the CIE xy/brightness triples and the occasion ride along as attributes, which
is what the dashboard card and the light automations read.

Notes:
09/01/2026 - Created with the config-flow rewrite
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_HEX_CODES,
    ATTR_REASON,
    ATTR_XYZ_CODES,
    DOMAIN,
)
from .coordinator import EsbLightsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EsbLightsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EsbLightColorSensor(coordinator, entry)])


class EsbLightColorSensor(CoordinatorEntity[EsbLightsCoordinator], SensorEntity):
    """Tonight's Empire State Building color scheme."""

    _attr_has_entity_name = True
    _attr_name = "Color"
    _attr_icon = "mdi:city-variant-outline"

    def __init__(
        self, coordinator: EsbLightsCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_color"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ESB Lights",
            manufacturer="Kinetic",
            model="Weathervane Lights",
            configuration_url=coordinator.host,
        )

    @property
    def native_value(self) -> str | None:
        """The color description. HA caps state at 255 chars; these are short."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("colorDescription")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {
            ATTR_HEX_CODES: data.get(ATTR_HEX_CODES, []),
            ATTR_XYZ_CODES: data.get(ATTR_XYZ_CODES, []),
            ATTR_REASON: data.get(ATTR_REASON, ""),
        }
