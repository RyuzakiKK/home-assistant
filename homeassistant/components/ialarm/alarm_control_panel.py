"""Interfaces with iAlarm control panels."""
import logging

from homeassistant.components.alarm_control_panel import (
    FORMAT_NUMBER,
    AlarmControlPanelEntity,
)
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from homeassistant.const import CONF_PIN
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up a iAlarm alarm control panel based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    pin = entry.data.get(CONF_PIN)
    async_add_entities([IAlarmPanel(coordinator, pin)], False)


class IAlarmPanel(AlarmControlPanelEntity, CoordinatorEntity):
    """Representation of an iAlarm device."""

    def __init__(self, coordinator, code):
        """Init the iAlarm device."""
        super().__init__(coordinator)
        self._unique_name = f"ialarm_{coordinator.host}"
        self._code = code

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Antifurto365 - Meian",
        }

    @property
    def unique_id(self):
        """Return a unique id."""
        return self._unique_name

    @property
    def name(self):
        """Return the name."""
        return self.unique_id

    @property
    def state(self):
        """Return the state of the device."""
        return self.coordinator.state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    @property
    def code_format(self):
        """Return one or more digits/characters."""
        return FORMAT_NUMBER

    def _validate_code(self, code):
        """Validate given code."""
        if self._code is None:
            return True
        return code == self._code

    def alarm_disarm(self, code=None):
        """Send disarm command."""
        if not self._validate_code(code):
            _LOGGER.warning("Wrong code entered for disarming")
            return
        self.coordinator.ialarm.disarm()

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        if not self._validate_code(code):
            _LOGGER.warning("Wrong code entered for arming")
            return
        self.coordinator.ialarm.arm_stay()

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        if not self._validate_code(code):
            _LOGGER.warning("Wrong code entered for arming")
            return
        self.coordinator.ialarm.arm_away()
