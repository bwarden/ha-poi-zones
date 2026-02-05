"""Config flow for POI Zones integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_CITY,
    CONF_POI_TYPE,
    CONF_SEARCH_RADIUS,
    CONF_ZONE_RADIUS,
    DEFAULT_SEARCH_RADIUS,
    DEFAULT_ZONE_RADIUS,
    DOMAIN,
    NOMINATIM_URL,
    POI_TYPES,
)

_LOGGER = logging.getLogger(__name__)


class POIZonesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for POI Zones."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._city: str | None = None
        self._poi_type: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - select POI type."""
        errors = {}

        # Build POI type options sorted alphabetically by display name
        poi_options = [
            {"value": k, "label": v["name"]}
            for k, v in sorted(POI_TYPES.items(), key=lambda x: x[1]["name"])
        ]

        if user_input is not None:
            self._poi_type = user_input[CONF_POI_TYPE]
            return await self.async_step_location()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POI_TYPE): SelectSelector(
                        SelectSelectorConfig(
                            options=poi_options,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="poi_type",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the location configuration step."""
        errors = {}

        poi_config = POI_TYPES[self._poi_type]
        default_zone_radius = poi_config["radius"]

        if user_input is not None:
            city = user_input[CONF_CITY]
            
            # Validate the city by geocoding it
            if await self._validate_city(city):
                self._city = city
                
                # Check for duplicate entries
                await self.async_set_unique_id(f"{self._poi_type}_{city.lower()}")
                self._abort_if_unique_id_configured()

                title = f"{poi_config['name']} - {city}"
                
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_CITY: city,
                        CONF_POI_TYPE: self._poi_type,
                        CONF_SEARCH_RADIUS: user_input.get(
                            CONF_SEARCH_RADIUS, DEFAULT_SEARCH_RADIUS
                        ),
                        CONF_ZONE_RADIUS: user_input.get(
                            CONF_ZONE_RADIUS, default_zone_radius
                        ),
                    },
                )
            else:
                errors["base"] = "invalid_city"

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CITY): str,
                    vol.Optional(
                        CONF_SEARCH_RADIUS, default=DEFAULT_SEARCH_RADIUS
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=100,
                            step=1,
                            unit_of_measurement="km",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_ZONE_RADIUS, default=default_zone_radius
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=25,
                            max=1000,
                            step=25,
                            unit_of_measurement="m",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "poi_type": poi_config["name"],
            },
        )

    async def _validate_city(self, city: str) -> bool:
        """Validate the city by attempting to geocode it."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {"q": city, "format": "json", "limit": 1}
                headers = {
                    "User-Agent": "HomeAssistant-POIZones/1.0"
                }
                async with session.get(
                    NOMINATIM_URL, params=params, headers=headers
                ) as response:
                    if response.status != 200:
                        return False
                    data = await response.json()
                    return len(data) > 0
        except Exception:
            _LOGGER.exception("Error validating city")
            return False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return POIZonesOptionsFlow(config_entry)


class POIZonesOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for POI Zones."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        poi_type = self._config_entry.data[CONF_POI_TYPE]
        poi_config = POI_TYPES[poi_type]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SEARCH_RADIUS,
                        default=self._config_entry.options.get(
                            CONF_SEARCH_RADIUS,
                            self._config_entry.data.get(
                                CONF_SEARCH_RADIUS, DEFAULT_SEARCH_RADIUS
                            ),
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=100,
                            step=1,
                            unit_of_measurement="km",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_ZONE_RADIUS,
                        default=self._config_entry.options.get(
                            CONF_ZONE_RADIUS,
                            self._config_entry.data.get(
                                CONF_ZONE_RADIUS, poi_config["radius"]
                            ),
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=25,
                            max=1000,
                            step=25,
                            unit_of_measurement="m",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
