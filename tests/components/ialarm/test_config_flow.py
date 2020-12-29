"""Test the Antifurto365 iAlarm config flow."""
from homeassistant import config_entries, setup
from homeassistant.components.ialarm.const import DOMAIN

from tests.async_mock import patch
from tests.common import MockConfigEntry

TEST_DATA = {
    "host": "1.1.1.1",
    "port": 18034,
    "pin": "1234",
}


async def test_form(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "homeassistant.components.ialarm.config_flow.IAlarm.get_status",
        return_value=1,
    ), patch(
        "homeassistant.components.ialarm.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.ialarm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_DATA
        )
        await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == TEST_DATA["host"]
    assert result2["data"] == TEST_DATA
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ialarm.config_flow.IAlarm.get_status",
        side_effect=ConnectionError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_DATA
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_exception(hass):
    """Test we handle unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.ialarm.config_flow.IAlarm.get_status",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_DATA
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "unknown"}


async def test_form_already_exists(hass):
    """Test that a flow with an existing host aborts."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_DATA["host"],
        data=TEST_DATA,
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_DATA
    )

    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"
