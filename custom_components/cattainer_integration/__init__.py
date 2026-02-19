"""
Custom integration to integrate integration_blueprint with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/integration_blueprint
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components import frontend, webhook
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.loader import async_get_loaded_integration

from custom_components.cattainer_integration import entity  # noqa: F401

from .api import IntegrationBlueprintApiClient
from .const import DOMAIN, LOGGER, SIGNAL_CAT_DETECTED
from .coordinator import BlueprintDataUpdateCoordinator
from .data import IntegrationBlueprintData

if TYPE_CHECKING:
    from aiohttp import web
    from homeassistant.core import HomeAssistant

    from .data import IntegrationBlueprintConfigEntry

PLATFORMS: list[Platform] = [
    # Platform.SENSOR,
    Platform.BINARY_SENSOR,
    # Platform.SWITCH,
]

# This ID must match the URL you use in your curl command:
# http://.../api/webhook/cattainer_incoming_data
WEBHOOK_ID = "cattainer_incoming_data"


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntegrationBlueprintConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = BlueprintDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=1),
    )
    entry.runtime_data = IntegrationBlueprintData(
        client=IntegrationBlueprintApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Sidebar setup
    cattainer_ip = entry.data[CONF_HOST]
    sidebar_url = f"http://{cattainer_ip}:5000"
    LOGGER.info(f"Registering Cattainer panel with url: {sidebar_url}")

    frontend.async_remove_panel(hass, "cattainer")  # Remove any existing panels

    # Build the new panel
    frontend.async_register_built_in_panel(
        hass,
        component_name="iframe",  # Important since it makes the panel host a webserver
        sidebar_title="Cattainer",
        sidebar_icon="mdi:cat",
        frontend_url_path="cattainer",
        config={"url": sidebar_url},
        require_admin=False,
    )  # type: ignore  # noqa: PGH003

    # Webhook setup
    LOGGER.info(f"Registering Webhook: {WEBHOOK_ID}")
    webhook.async_register(
        hass,
        DOMAIN,
        "Cattainer Webhook",
        WEBHOOK_ID,
        handle_webhook,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: IntegrationBlueprintConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    # Clean up the sidebar
    frontend.async_remove_panel(hass, "cattainer")

    # Clean up the webhook
    webhook.async_unregister(hass, WEBHOOK_ID)

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: IntegrationBlueprintConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def handle_webhook(
    hass: HomeAssistant, _webhook_id: str, request: web.Request
) -> None:
    """Handle incoming webhook POST requests."""
    try:
        data = await request.json()
    except ValueError:
        return

    # Send the signal to binary_sensor.py
    dispatcher_send(hass, SIGNAL_CAT_DETECTED, data)
