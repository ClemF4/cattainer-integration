"""Binary sensor platform for Cattainer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import LOGGER, SIGNAL_CAT_DETECTED
from .entity import IntegrationBlueprintEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import BlueprintDataUpdateCoordinator
    from .data import IntegrationBlueprintConfigEntry

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="cattainer_cat_detected",
        name="Cat Detected",
        device_class=BinarySensorDeviceClass.MOTION,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: IntegrationBlueprintConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        IntegrationBlueprintBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class IntegrationBlueprintBinarySensor(IntegrationBlueprintEntity, BinarySensorEntity):
    """Cattainer binary_sensor class."""

    def __init__(
        self,
        coordinator: BlueprintDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._is_on = False

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""

        await super().async_added_to_hass()

        # Listen for the webhook signal
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_CAT_DETECTED,
                self._handle_webhook_update,
            )
        )

    @callback
    def _handle_webhook_update(self, data: dict[str, Any]) -> None:
        """Handle incoming webhook data."""
        LOGGER.warning(f"Cattainer Sensor RECEIVED Signal with data: {data}")

        # Check for "cat_detected" (default to False if missing)
        new_state = data.get("cat_detected", False)
        self._is_on = new_state

        # Force UI update
        self.async_write_ha_state()

        LOGGER.warning(f"Cattainer Sensor Updated State to: {self._is_on}")

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self._is_on
