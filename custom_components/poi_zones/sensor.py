"""Sensor platform for POI Zones."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CITY, CONF_POI_TYPE, CONF_ZONE_PREFIX, DOMAIN, POI_TYPES
from .coordinator import POIZonesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up POI Zones sensor."""
    coordinator: POIZonesCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([POISensor(coordinator, entry)])


class POISensor(CoordinatorEntity[POIZonesCoordinator], SensorEntity):
    """Sensor showing POIs found with full details in attributes."""

    def __init__(
        self,
        coordinator: POIZonesCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        poi_type = entry.data[CONF_POI_TYPE]
        city = entry.data[CONF_CITY]
        poi_config = POI_TYPES[poi_type]

        self._attr_name = f"{poi_config['name']} near {city}"
        self._attr_unique_id = f"{entry.entry_id}_sensor"
        self._attr_icon = poi_config["icon"]
        self._attr_native_unit_of_measurement = "locations"

    @property
    def native_value(self) -> int:
        """Return the number of POIs found."""
        if self.coordinator.data:
            return len(self.coordinator.data.get("pois", []))
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all POI data as attributes."""
        if not self.coordinator.data:
            return {}

        pois = self.coordinator.data.get("pois", [])
        
        attrs = {
            "city": self.coordinator.data.get("city"),
            "city_latitude": self.coordinator.data.get("city_lat"),
            "city_longitude": self.coordinator.data.get("city_lon"),
            "poi_type": self.coordinator.data.get("poi_type"),
            "poi_type_name": self.coordinator.data.get("poi_type_name"),
            "search_radius_km": self.coordinator.search_radius,
            "zone_radius_m": self.coordinator.zone_radius,
            "zone_ids": [],
            "locations": [],
        }

        # Get zone prefix from config
        zone_prefix = self._entry.data.get(CONF_ZONE_PREFIX, self.coordinator.poi_type)

        # Store zone IDs for easy automation access
        zone_ids = []

        # Add each POI
        for poi in pois:
            # Generate prefixed zone name and ID (matching __init__.py)
            prefixed_name = f"{zone_prefix}_{poi['name']}"
            zone_id = self._slugify(prefixed_name)
            zone_ids.append(zone_id)

            location = {
                "name": poi["name"],  # Original name for reference
                "zone_name": prefixed_name,  # Full prefixed name
                "latitude": poi["latitude"],
                "longitude": poi["longitude"],
                "zone_id": zone_id,
                "zone_entity_id": f"zone.{zone_id}",
            }
            
            # Add optional fields
            for field in ["address", "phone", "website", "opening_hours", 
                          "brand", "operator", "emergency", "cuisine",
                          "capacity", "fuel_types"]:
                if field in poi:
                    location[field] = poi[field]

            attrs["locations"].append(location)

        attrs["zone_ids"] = zone_ids
        return attrs

    @staticmethod
    def _slugify(text: str) -> str:
        """Create a slug from text."""
        import re
        slug = re.sub(r"[^a-z0-9]+", "_", text.lower())
        slug = slug.strip("_")
        slug = re.sub(r"_+", "_", slug)
        return slug[:50]
