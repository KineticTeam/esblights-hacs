"""UI setup for ESB Lights.

This is the reason the integration exists rather than a YAML REST sensor: the
API address and key are typed into the Add Integration dialog and validated
before the entry is created, instead of being hand-written into secrets.yaml.

Notes:
09/01/2026 - Created so HACS install ends in a settings dialog, not a YAML edit
"""

from __future__ import annotations

import logging
from typing import Any

import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_PATH,
    CONF_API_KEY,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

VALIDATE_TIMEOUT = 20


def _normalise_host(host: str) -> str:
    """Accept what people actually type and turn it into a base URL."""
    host = host.strip().rstrip("/")

    #Bare host or host:port - assume plain http on the internal network
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"

    #Tolerate someone pasting the full endpoint rather than the base
    if host.endswith(API_PATH):
        host = host[: -len(API_PATH)]

    return host


async def _validate(hass, host: str, api_key: str | None) -> str | None:
    """Return None if the API answers correctly, else an error key."""
    session = async_get_clientsession(hass)
    params = {"apikey": api_key} if api_key else {}

    try:
        async with async_timeout.timeout(VALIDATE_TIMEOUT):
            response = await session.get(f"{host}{API_PATH}", params=params)

            if response.status == 401:
                return "invalid_auth"

            if response.status != 200:
                return "cannot_connect"

            payload = await response.json()

    except Exception:  # noqa: BLE001 - any failure here is "cannot connect"
        _LOGGER.debug("Validation request to %s failed", host, exc_info=True)
        return "cannot_connect"

    if not (payload or {}).get("content", {}).get("colorDescription"):
        return "unexpected_response"

    return None


class EsbLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles the Add Integration dialog."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = _normalise_host(user_input[CONF_HOST])
            api_key = (user_input.get(CONF_API_KEY) or "").strip() or None

            #One entry per API address
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            error = await _validate(self.hass, host, api_key)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title="ESB Lights",
                    data={CONF_HOST: host, CONF_API_KEY: api_key},
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        )
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=(user_input or {}).get(CONF_HOST, "192.168.123.114:4000"),
                ): str,
                vol.Optional(
                    CONF_API_KEY, default=(user_input or {}).get(CONF_API_KEY, "")
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EsbLightsOptionsFlow:
        return EsbLightsOptionsFlow(config_entry)


class EsbLightsOptionsFlow(config_entries.OptionsFlow):
    """Lets the poll interval be changed after setup without re-adding."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL)
                )
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
