"""The Parkrun integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "parkrun"
PLATFORMS: list[Platform] = [Platform.SENSOR]
SERVICE_FORCE_UPDATE = "force_update"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Parkrun from a config entry."""
    _LOGGER.debug("Setting up Parkrun integration for user ID: %s", entry.data.get("user_id"))
    
    # Store the config entry data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Forward the setup to the sensor platform
    # The blocking call warning here is expected and safe for custom integrations
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register service to force update
    async def force_update_service(call: ServiceCall) -> None:
        """Handle force update service call."""
        _LOGGER.info("Force update service called")
        # Find all coordinators and force refresh
        coordinators = hass.data.get(DOMAIN, {}).get("coordinators", [])
        for coordinator in coordinators:
            if hasattr(coordinator, 'force_update'):
                await coordinator.force_update()
    
    hass.services.async_register(DOMAIN, SERVICE_FORCE_UPDATE, force_update_service)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove service if this was the last entry
        if not hass.data.get(DOMAIN):
            hass.services.async_remove(DOMAIN, SERVICE_FORCE_UPDATE)
        
    return unload_ok
