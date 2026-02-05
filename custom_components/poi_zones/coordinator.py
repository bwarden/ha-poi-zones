"""DataUpdateCoordinator for POI Zones."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    NOMINATIM_URL,
    OVERPASS_URL,
    POI_TYPES,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class POIZonesCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch POI data from OpenStreetMap."""

    def __init__(
        self,
        hass: HomeAssistant,
        city: str,
        poi_type: str,
        search_radius: int,
        zone_radius: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{poi_type}_{city}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.city = city
        self.poi_type = poi_type
        self.search_radius = search_radius
        self.zone_radius = zone_radius
        self._city_coords: tuple[float, float] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch POI data from OpenStreetMap."""
        try:
            # First, geocode the city if we haven't already
            if self._city_coords is None:
                self._city_coords = await self._geocode_city()
                if self._city_coords is None:
                    raise UpdateFailed(f"Could not geocode city: {self.city}")

            # Fetch POIs
            pois = await self._fetch_pois()
            
            _LOGGER.info(
                "Found %d %s POIs near %s",
                len(pois),
                self.poi_type,
                self.city,
            )

            return {
                "city": self.city,
                "city_lat": self._city_coords[0],
                "city_lon": self._city_coords[1],
                "poi_type": self.poi_type,
                "poi_type_name": POI_TYPES[self.poi_type]["name"],
                "pois": pois,
            }

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching POI data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _geocode_city(self) -> tuple[float, float] | None:
        """Geocode city name to coordinates using Nominatim."""
        async with aiohttp.ClientSession() as session:
            params = {
                "q": self.city,
                "format": "json",
                "limit": 1,
            }
            headers = {
                "User-Agent": "HomeAssistant-POIZones/1.0 (https://github.com/tgoncalves/ha-poi-zones)"
            }

            async with session.get(
                NOMINATIM_URL, params=params, headers=headers
            ) as response:
                if response.status != 200:
                    _LOGGER.error("Nominatim API error: %s", response.status)
                    return None

                data = await response.json()
                if not data:
                    _LOGGER.error("No results for city: %s", self.city)
                    return None

                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                _LOGGER.debug("Geocoded %s to (%s, %s)", self.city, lat, lon)
                return (lat, lon)

    def _build_overpass_query(self) -> str:
        """Build Overpass QL query for the selected POI type."""
        poi_config = POI_TYPES[self.poi_type]
        filters = poi_config["filters"]
        
        lat, lon = self._city_coords
        radius_meters = self.search_radius * 1000  # Convert km to meters
        
        # Build query parts for each filter
        query_parts = []
        for f in filters:
            # Build tag filter string
            tags = "".join(f'["{k}"="{v}"]' for k, v in f.items())
            
            # Add queries for nodes, ways, and relations
            query_parts.append(f'node{tags}(around:{radius_meters},{lat},{lon});')
            query_parts.append(f'way{tags}(around:{radius_meters},{lat},{lon});')
            query_parts.append(f'relation{tags}(around:{radius_meters},{lat},{lon});')

        query = f"""
        [out:json][timeout:30];
        (
            {"".join(query_parts)}
        );
        out center;
        """
        
        _LOGGER.debug("Overpass query: %s", query)
        return query

    async def _fetch_pois(self) -> list[dict[str, Any]]:
        """Fetch POIs from Overpass API."""
        query = self._build_overpass_query()
        poi_config = POI_TYPES[self.poi_type]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                OVERPASS_URL,
                data={"data": query},
                headers={"User-Agent": "HomeAssistant-POIZones/1.0"},
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise UpdateFailed(f"Overpass API error {response.status}: {text}")

                data = await response.json()

        # Process results
        pois = []
        seen_locations = set()

        for element in data.get("elements", []):
            # Get coordinates (center for ways/relations)
            if element["type"] == "node":
                lat = element["lat"]
                lon = element["lon"]
            elif "center" in element:
                lat = element["center"]["lat"]
                lon = element["center"]["lon"]
            else:
                continue

            # Deduplicate by location (round to ~50m precision)
            location_key = (round(lat, 4), round(lon, 4))
            if location_key in seen_locations:
                continue
            seen_locations.add(location_key)

            tags = element.get("tags", {})
            name = tags.get("name")

            # Skip unnamed POIs
            if not name:
                continue

            # Calculate dynamic radius based on facility size if applicable
            if self.poi_type in ("hospital", "urgent_care"):
                calculated_radius = self._calculate_hospital_radius(element, tags)
            else:
                calculated_radius = self.zone_radius or poi_config["radius"]

            # Build POI entry
            poi = {
                "id": f"{element['type']}_{element['id']}",
                "osm_type": element["type"],
                "osm_id": element["id"],
                "name": name,
                "latitude": lat,
                "longitude": lon,
                "poi_type": self.poi_type,
                "poi_type_name": poi_config["name"],
                "icon": poi_config["icon"],
                "zone_radius": calculated_radius,
            }

            # Add optional tags
            if addr := self._build_address(tags):
                poi["address"] = addr
            if phone := tags.get("phone") or tags.get("contact:phone"):
                poi["phone"] = phone
            if website := tags.get("website") or tags.get("contact:website"):
                poi["website"] = website
            if opening_hours := tags.get("opening_hours"):
                poi["opening_hours"] = opening_hours
            if brand := tags.get("brand"):
                poi["brand"] = brand
            if operator := tags.get("operator"):
                poi["operator"] = operator

            # Add type-specific attributes
            if self.poi_type.startswith("hospital") or self.poi_type == "urgent_care":
                poi["emergency"] = tags.get("emergency") == "yes"
            if self.poi_type == "ev_charging":
                poi["capacity"] = tags.get("capacity")
                poi["socket_types"] = tags.get("socket:type2") or tags.get("socket:ccs") or tags.get("socket:chademo")
            if self.poi_type in ("restaurant", "fast_food", "cafe"):
                poi["cuisine"] = tags.get("cuisine")
            if self.poi_type == "gas_station":
                poi["brand"] = tags.get("brand")
                poi["fuel_types"] = self._get_fuel_types(tags)

            pois.append(poi)

        # Sort by name
        pois.sort(key=lambda x: x["name"])
        return pois

    def _build_address(self, tags: dict) -> str | None:
        """Build address string from OSM tags."""
        parts = []
        if street := tags.get("addr:street"):
            if housenumber := tags.get("addr:housenumber"):
                parts.append(f"{housenumber} {street}")
            else:
                parts.append(street)
        if city := tags.get("addr:city"):
            parts.append(city)
        if state := tags.get("addr:state"):
            parts.append(state)
        if postcode := tags.get("addr:postcode"):
            parts.append(postcode)
        
        return ", ".join(parts) if parts else None

    def _get_fuel_types(self, tags: dict) -> list[str]:
        """Extract fuel types from gas station tags."""
        fuels = []
        fuel_mapping = {
            "fuel:diesel": "Diesel",
            "fuel:octane_87": "Regular",
            "fuel:octane_89": "Mid-Grade",
            "fuel:octane_91": "Premium",
            "fuel:octane_93": "Premium",
            "fuel:e85": "E85",
        }
        for tag, name in fuel_mapping.items():
            if tags.get(tag) == "yes":
                fuels.append(name)
        return fuels

    def _calculate_hospital_radius(self, element: dict, tags: dict) -> int:
        """Calculate zone radius based on healthcare facility size indicators.

        Used for hospitals and urgent care facilities.
        Uses multiple factors to determine appropriate radius:
        - Number of beds (if available)
        - OSM element type (node/way/relation)
        - Healthcare type tags
        - Emergency status

        Returns radius in meters.
        """
        base_radius = self.zone_radius or POI_TYPES[self.poi_type]["radius"]

        # Buffer to account for OSM positioning variations (entrance vs center)
        # This ensures zones cover the entire building even if the point is slightly off
        positioning_buffer = 30  # meters

        # Check for explicit bed count (most reliable indicator)
        if beds_str := tags.get("beds"):
            try:
                beds = int(beds_str)
                # Scale radius based on bed count (with buffer)
                if beds < 50:
                    return 100 + positioning_buffer  # Small clinic/hospital
                elif beds < 150:
                    return 150 + positioning_buffer  # Medium hospital
                elif beds < 300:
                    return 200 + positioning_buffer  # Large hospital
                else:
                    return 250 + positioning_buffer  # Major medical center
            except ValueError:
                pass  # Fall through to other methods

        # Check healthcare type for clinics vs hospitals
        healthcare = tags.get("healthcare", "")
        if healthcare in ("clinic", "doctor", "dentist"):
            return 75 + positioning_buffer  # Small medical facility

        # Use OSM element type as size proxy
        element_type = element.get("type")
        if element_type == "node":
            # Point features are typically smaller clinics
            return 100 + positioning_buffer
        elif element_type == "relation":
            # Relations are typically large hospital complexes
            return min(250 + positioning_buffer, base_radius + positioning_buffer)
        elif element_type == "way":
            # Ways are buildings - add extra buffer since point might be at entrance
            # Check if it's marked as emergency
            if tags.get("emergency") == "yes":
                return 200 + positioning_buffer  # Emergency hospitals tend to be larger
            return 150 + positioning_buffer

        # Default to configured radius with buffer
        return base_radius + positioning_buffer
