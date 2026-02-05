"""POI Zones integration for Home Assistant."""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components import zone
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_CITY,
    CONF_POI_TYPE,
    CONF_SEARCH_RADIUS,
    CONF_ZONE_RADIUS,
    DEFAULT_SEARCH_RADIUS,
    DEFAULT_ZONE_RADIUS,
    DOMAIN,
    POI_TYPES,
)
from .coordinator import POIZonesCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up POI Zones from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    city = entry.data[CONF_CITY]
    poi_type = entry.data[CONF_POI_TYPE]
    
    # Get config with options override
    search_radius = entry.options.get(
        CONF_SEARCH_RADIUS, entry.data.get(CONF_SEARCH_RADIUS, DEFAULT_SEARCH_RADIUS)
    )
    zone_radius = entry.options.get(
        CONF_ZONE_RADIUS,
        entry.data.get(CONF_ZONE_RADIUS, POI_TYPES[poi_type]["radius"]),
    )

    # Create coordinator
    coordinator = POIZonesCoordinator(
        hass,
        city=city,
        poi_type=poi_type,
        search_radius=search_radius,
        zone_radius=zone_radius,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "zones_created": [],
    }

    # Create zones for discovered POIs
    await _create_zones(hass, entry, coordinator)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Register services
    if not hass.services.has_service(DOMAIN, "refresh"):
        async def handle_refresh(call: ServiceCall) -> None:
            """Handle refresh service call."""
            for entry_id, data in hass.data[DOMAIN].items():
                if "coordinator" in data:
                    await data["coordinator"].async_refresh()

        hass.services.async_register(DOMAIN, "refresh", handle_refresh)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove created zones
    if entry.entry_id in hass.data[DOMAIN]:
        zone_ids = hass.data[DOMAIN][entry.entry_id].get("zones_created", [])
        await _remove_zones(hass, zone_ids)

    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


def _slugify(text: str) -> str:
    """Create a slug from text."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower())
    slug = slug.strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug[:50]  # Limit length


async def _create_zones(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: POIZonesCoordinator,
) -> None:
    """Create Home Assistant zones for discovered POIs using zone storage."""
    if not coordinator.data:
        return

    pois = coordinator.data.get("pois", [])
    poi_type = coordinator.poi_type
    created_zone_ids = []

    # Access zone storage collection
    if zone.DOMAIN not in hass.data:
        _LOGGER.warning("Zone integration not loaded, skipping zone creation")
        return

    # In modern HA, hass.data[zone.DOMAIN] is the ZoneStorageCollection itself
    storage_collection = hass.data[zone.DOMAIN]

    # Log available methods for debugging
    _LOGGER.debug(
        "Zone storage collection type: %s, methods: %s",
        type(storage_collection),
        [m for m in dir(storage_collection) if not m.startswith("_") and callable(getattr(storage_collection, m))]
    )

    # Verify it has the methods we need
    if not hasattr(storage_collection, "async_create_item"):
        _LOGGER.warning(
            "Zone storage collection does not support async_create_item. Type: %s",
            type(storage_collection)
        )
        return

    for poi in pois:
        # Check if zone already exists (by name, since we can't control IDs)
        existing_id = None
        existing_item = None
        try:
            for item in storage_collection.async_items():
                # Match by name to find existing POI zones
                if item.get("name") == poi["name"]:
                    existing_id = item.get("id")
                    existing_item = item
                    break
        except Exception as err:
            _LOGGER.debug("Could not check existing zones: %s", err)

        zone_data = {
            "name": poi["name"],
            "latitude": poi["latitude"],
            "longitude": poi["longitude"],
            "radius": float(poi["zone_radius"]),
            "icon": poi["icon"],
            "passive": False,
        }

        try:
            if existing_id:
                # Update existing zone
                _LOGGER.debug("Updating zone %s with data: %s", existing_id, zone_data)
                await storage_collection.async_update_item(existing_id, zone_data)
                created_zone_ids.append(existing_id)
                _LOGGER.debug("Updated zone: %s (ID: %s)", poi["name"], existing_id)
            else:
                # Create new zone - the collection will assign an ID
                _LOGGER.debug("Creating new zone with data: %s", zone_data)
                _LOGGER.debug("Zone data keys: %s", list(zone_data.keys()))
                result = await storage_collection.async_create_item(zone_data)
                # Get the ID from the result
                new_id = result.get("id") if isinstance(result, dict) else None
                if new_id:
                    created_zone_ids.append(new_id)
                    _LOGGER.debug("Created zone: %s (ID: %s)", poi["name"], new_id)

        except Exception as err:
            _LOGGER.warning("Failed to create/update zone %s: %s", poi["name"], err)
            _LOGGER.debug("Full error for %s: %s", poi["name"], err, exc_info=True)

    # Store created zone IDs for cleanup
    hass.data[DOMAIN][entry.entry_id]["zones_created"] = created_zone_ids
    _LOGGER.info(
        "Created/updated %d zones for %s in %s",
        len(created_zone_ids),
        POI_TYPES[poi_type]["name"],
        coordinator.city,
    )


async def _remove_zones(hass: HomeAssistant, zone_ids: list[str]) -> None:
    """Remove zones created by this integration."""
    # Access zone storage collection
    if zone.DOMAIN not in hass.data:
        _LOGGER.debug("Zone integration not loaded, skipping zone cleanup")
        return

    # In modern HA, hass.data[zone.DOMAIN] is the ZoneStorageCollection itself
    storage_collection = hass.data[zone.DOMAIN]

    for zone_id in zone_ids:
        try:
            await storage_collection.async_delete_item(zone_id)
            _LOGGER.debug("Removed zone: %s", zone_id)
        except Exception:
            _LOGGER.debug("Zone %s already removed or not found", zone_id)
