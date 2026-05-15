"""Client for the Sonance DSP amplifier HTTP API."""

import random
from collections.abc import Mapping
from typing import Any, Self

import aiohttp

from ._wire_models import WireEqSettings, WireGeneralSettings, WireInOutSettings
from .models import EqSettings, GeneralSettings, InOutSettings

JsonObject = dict[str, Any]


class SonanceDSP:
    """Represent a Sonance DSP amplifier exposed over its HTTP interface."""

    def __init__(
        self,
        host: str,
        *,
        port: int = 80,
        session: aiohttp.ClientSession | None = None,
        request_timeout: float = 10,
    ) -> None:
        self.host = host
        self.port = port
        self._session = session
        self._owns_session = session is None
        self._request_timeout = aiohttp.ClientTimeout(total=request_timeout)

    async def __aenter__(self) -> Self:
        await self._get_session()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.close()

    @property
    def base_url(self) -> str:
        """Base HTTP URL for the amplifier."""

        return f"http://{self.host}:{self.port}"

    async def close(self) -> None:
        """Close the owned HTTP session, if this client created one."""

        if self._owns_session and self._session is not None:
            await self._session.close()
        self._session = None

    async def read_general(self) -> GeneralSettings:
        """Read the general settings state."""

        data = await self._request(
            {
                "page": "general-settings",
                "action": "read",
            }
        )
        return WireGeneralSettings.model_validate(data).to_model()

    async def write_general(
        self, name: str, value: str | int | float | bool
    ) -> GeneralSettings:
        """Write a general setting and return the refreshed state."""

        data = await self._request(
            {
                "page": "general-settings",
                "action": "write",
                "name": name,
                "value": self._format_value(value),
            }
        )
        return WireGeneralSettings.model_validate(data).to_model()

    async def read_in_out(self) -> InOutSettings:
        """Read the input/output settings state."""

        data = await self._request(
            {
                "page": "in-out-settings",
                "action": "read",
            }
        )
        return WireInOutSettings.model_validate(data).to_model()

    async def write_in_out(
        self,
        name: str,
        index: int,
        value: str | int | float | bool,
    ) -> InOutSettings:
        """Write an indexed input/output setting and return the refreshed state."""

        data = await self._request(
            {
                "page": "in-out-settings",
                "action": "write",
                "name": name,
                "index": index,
                "value": self._format_value(value),
            }
        )
        return WireInOutSettings.model_validate(data).to_model()

    async def read_eq(self, preset: int = 0) -> EqSettings:
        """Read an EQ preset state."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "read",
                "eq-preset": preset,
            }
        )
        return WireEqSettings.model_validate(data).to_model()

    async def write_eq(
        self,
        name: str,
        value: str | int | float | bool,
        *,
        preset: int = 0,
    ) -> EqSettings:
        """Write an EQ preset-level setting and return the refreshed state."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "write",
                "eq-preset": preset,
                "name": name,
                "value": self._format_value(value),
            }
        )
        return WireEqSettings.model_validate(data).to_model()

    async def write_eq_indexed(
        self,
        name: str,
        index: int,
        value: str | int | float | bool,
        *,
        preset: int = 0,
        extra_params: Mapping[str, str | int | float | bool] | None = None,
    ) -> EqSettings:
        """Write an indexed EQ setting and return the refreshed state."""

        params: dict[str, str | int | float] = {
            "page": "eq-settings",
            "action": "write",
            "eq-preset": preset,
            "name": name,
            "index": index,
            "value": self._format_value(value),
        }
        if extra_params:
            params.update(
                {
                    key: self._format_value(extra_value)
                    for key, extra_value in extra_params.items()
                }
            )

        data = await self._request(params)
        return WireEqSettings.model_validate(data).to_model()

    async def write_eq_in_out(
        self,
        name: str,
        index: int,
        value: str | int | float | bool,
    ) -> EqSettings:
        """Write an in/out setting through the EQ page API."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "write",
                "name": name,
                "index": index,
                "value": self._format_value(value),
            }
        )
        return WireEqSettings.model_validate(data).to_model()

    async def do_eq(
        self,
        name: str,
        value: str | int | float | bool,
        *,
        preset: int = 0,
    ) -> EqSettings:
        """Execute an EQ action and return the refreshed state."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "do",
                "eq-preset": preset,
                "name": name,
                "value": self._format_value(value),
            }
        )
        return WireEqSettings.model_validate(data).to_model()

    async def _request(self, params: Mapping[str, str | int | float]) -> JsonObject:
        session = await self._get_session()
        request_params: dict[str, str | int | float] = dict(params)
        request_params["r"] = self._cache_buster()

        async with session.get(
            f"{self.base_url}/Web/Handler.php",
            params=request_params,
        ) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)

        if not isinstance(data, dict):
            msg = f"Expected JSON object from amplifier, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._request_timeout)
        return self._session

    @staticmethod
    def _format_value(value: str | int | float | bool) -> str | int | float:
        if isinstance(value, bool):
            return "on" if value else "off"
        return value

    @staticmethod
    def _cache_buster() -> float:
        # The web UI sends Math.random(); the endpoint only needs a changing value.
        return random.random()
