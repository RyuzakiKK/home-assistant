"""iAlarm integration."""
import logging

from async_timeout import timeout
from pyialarm import IAlarm

from homeassistant.components.alarm_control_panel import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_COORDINATOR, DOMAIN

PLATFORM = "alarm_control_panel"
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up iAlarm components."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up iAlarm config."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    ialarm = IAlarm(host, port)

    coordinator = IAlarmDataUpdateCoordinator(
        hass,
        ialarm,
    )

    await coordinator.async_refresh()

    if not coordinator.data:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORM)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload iAlarm config."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, PLATFORM)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class IAlarmDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching iAlarm data."""

    def __init__(self, hass, ialarm):
        """Initialize global iAlarm data updater."""
        self.ialarm = ialarm
        self.state = None
        self.host = ialarm.host

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    def _update_data(self) -> dict:
        """Fetch data from iAlarm via sync functions."""
        status = self.ialarm.get_status()
        _LOGGER.debug("iAlarm status: %s", status)

        if status == self.ialarm.DISARMED:
            state = STATE_ALARM_DISARMED
        elif status == self.ialarm.ARMED_AWAY:
            state = STATE_ALARM_ARMED_AWAY
        elif status == self.ialarm.ARMED_STAY:
            state = STATE_ALARM_ARMED_HOME
        elif status == self.ialarm.TRIGGERED:
            state = STATE_ALARM_TRIGGERED
        else:
            state = None

        self.state = state

        return {
            "state": state,
        }

    async def _async_update_data(self) -> dict:
        """Fetch data from iAlarm."""
        try:
            async with timeout(10):
                return await self.hass.async_add_executor_job(self._update_data)
        except ConnectionError as error:
            raise UpdateFailed(error) from error
