"""Config flow for Antifurto365 iAlarm integration."""
import logging

from pyialarm import IAlarm
import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.const import CONF_HOST, CONF_PIN, CONF_PORT

# pylint: disable=unused-import
from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_PIN): str,
    }
)


async def _validate_connection(hass: core.HomeAssistant, host, port):
    ialarm = IAlarm(host, port)
    status = await hass.async_add_executor_job(ialarm.get_status)
    return status


class IAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Antifurto365 iAlarm."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        try:
            result = await _validate_connection(self.hass, host, port)
            if result is None:
                errors["base"] = "cannot_connect"
        except ConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )

        return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)
