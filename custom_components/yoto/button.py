"""Button for Yoto integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer

from .const import DOMAIN
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)

BUTTON_DESCRIPTIONS: Final[tuple[ButtonEntityDescription, ...]] = (
    ButtonEntityDescription(
        key="reboot",
        translation_key="reboot",
    ),
    ButtonEntityDescription(
        key="bluetooth_delete_bonds",
        translation_key="bluetooth_delete_bonds",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button platform."""
    coordinator = hass.data[DOMAIN][config_entry.unique_id]
    entities: list[YotoButton] = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        for description in BUTTON_DESCRIPTIONS:
            entities.append(YotoButton(coordinator, description, player))
    async_add_entities(entities)


class YotoButton(ButtonEntity, YotoEntity):
    """Yoto button class."""

    def __init__(
        self, coordinator, description: ButtonEntityDescription, player: YotoPlayer
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, player)
        self._description = description
        self._key = self._description.key
        self._attr_unique_id = f"{DOMAIN}_{player.id}_button_{self._key}"
        self._attr_translation_key = self._description.translation_key

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._key == "reboot":
            await self.coordinator.async_reboot_player(self.player.id)
        elif self._key == "bluetooth_delete_bonds":
            await self.coordinator.async_bluetooth_delete_bonds(self.player.id)
