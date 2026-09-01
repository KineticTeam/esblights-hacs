"""Polls the esblights API and shares the result with every entity.

One coordinator per config entry. The API is a small internal service that
changes at most once a day, so this polls slowly and treats a failure as
"keep showing the last value" rather than something to retry aggressively.

Notes:
09/01/2026 - Created with the config-flow rewrite
"""

from __future__ import annotations

import logging
from datetime import timedelta

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_PATH, DOMAIN

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


class EsbLightsCoordinator(DataUpdateCoordinator):
    """Fetches tonight's color scheme from the esblights API."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        api_key: str | None,
        scan_interval: int,
    ) -> None:
        self.host = host.rstrip("/")
        self.api_key = api_key
        self._session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def _url(self) -> str:
        return f"{self.host}{API_PATH}"

    @property
    def _params(self) -> dict[str, str]:
        #The key is optional; the API only enforces it when REQUIRE_API_KEY is on
        return {"apikey": self.api_key} if self.api_key else {}

    async def _async_update_data(self) -> dict:
        """Fetch and unwrap the API payload.

        Raises UpdateFailed on any problem, which marks entities unavailable
        while keeping their last known state visible in the UI.
        """
        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(self._url, params=self._params)

                if response.status == 401:
                    raise UpdateFailed(
                        "Unauthorized - the API key is missing or wrong"
                    )

                if response.status != 200:
                    raise UpdateFailed(f"API returned HTTP {response.status}")

                payload = await response.json()

        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001 - surfaced to the user as-is
            raise UpdateFailed(f"Could not reach {self.host}: {err}") from err

        content = (payload or {}).get("content")
        if not content:
            raise UpdateFailed("API response had no 'content' object")

        return content
