"""Meteo Swiss Weather Data Client"""
from __future__ import annotations

import json
import zoneinfo

import aiohttp
import async_timeout
from datetime import datetime
from datetime import timedelta
from aiohttp.client_exceptions import ClientConnectorError
from aiohttp.client_exceptions import ServerDisconnectedError
from aiohttp.client_exceptions import ServerTimeoutError

from .exceptions import MeteoSwissApiError
from .exceptions import MeteoSwissError
from .exceptions import MeteoSwissNoDataError
from .exceptions import MeteoSwissPLZNotFoundError


class MeteoSwissData:
    """The class for handling the data retrieval"""

    """API url to fetch current versions"""
    dataset_version_url: str = (
        "https://www.meteoschweiz.admin.ch/product/output/versions.json"
    )

    """API url to fetch the forecast for the given plz, also needs the version"""
    dataset_forecast_url: str = "https://www.meteoschweiz.admin.ch/product/output/forecast-chart/version__{version}/de/{plz}00.json"

    """API url to fetch the current weather conditions and PLZ data"""
    dataset_weather_url: str = "https://www.meteoschweiz.admin.ch/product/output/weather-widget/forecast/version__{version}/de/{plz}00.json"

    request_timeout: float = 8.0
    session: aiohttp.client.ClientSession | None = None
    verify_ssl: bool | None = None
    _timestamp: str | None = None
    _plz: str = ""
    _version_forecast: str | None = None
    _version_weather: str | None = None

    def __init__(
        self,
        default_plz: str = 7310,
        session: aiohttp.client.ClientSession | None = None,
    ):
        """Initialize the api client"""
        self.data = {}
        self._plz = default_plz
        self.session = session

    async def check_for_newest_version(self):
        """Fetch the Version API to check for the current version"""

        try:
            if self.session is None:
                self.session = aiohttp.client.ClientSession()

                async with async_timeout.timeout(self.request_timeout):
                    response = await self.session.get(
                        url=self.dataset_version_url,
                        allow_redirects=False,
                        verify_ssl=self.verify_ssl,
                    )

                if response.status == 200:
                    contents = await response.read()
                    response.close()
                    # extract versions for used urls
                    versions = json.loads(contents)
                    self._version_forecast = versions["forecast-chart"]
                    self._version_weather = versions["weather-widget/forecast"]

                    return True
                raise MeteoSwissApiError(f"Got status {response.status} from meteo")

        except (
            ClientConnectorError,
            ServerTimeoutError,
            ServerDisconnectedError,
        ) as exc:
            if self.session is not None:
                await self.session.close()
                self.session = None
            raise MeteoSwissApiError(exc) from exc
        except (ValueError) as exc:
            raise MeteoSwissNoDataError(exc) from exc

    async def update(self) -> dict | None:
        """Return a list of all current forecast data"""
        if self._plz == "":
            return None
        # if self.last_update and (
        #     self.last_update + timedelta(minutes=10)
        #     > datetime.utcnow().replace(tzinfo=zoneInfo.ZoneInfo("UTC"))
        # ):
        #     return (
        #         self.data
        #     ) # Not time to update yet; we are just reading every 10 minutes

        try:
            if self.session is None:
                self.session = aiohttp.client.ClientSession()

            async with async_timeout.timeout(self.request_timeout):
                weather_url = self.dataset_weather_url.format(
                    version=self.last_update["weather-widget/forecast"], plz=self._plz
                )
                forecast_url = self.dataset_forecast_url.format(
                    version=self.last_update["forecast-chart"], plz=self._plz
                )
                response_weather = await self.session.get(
                    url=weather_url, allow_redirects=False, verify_ssl=self.verify_ssl
                )
                response_forecast = await self.session.get(
                    url=forecast_url, allow_redirects=False, verify_ssl=self.verify_ssl
                )

            if response_weather.status == 200:
                contents = await response_weather.read()
                response_weather.close()

                data = json.loads(contents)["data"]
                self._timestamp = json.loads(contents)["config"]["timestamp"]

                self.data[self._plz] = {
                    "weather": dict(data),
                    "forecast-chart": None,
                }

                if response_forecast.status == 200:
                    contents_forecast = await response_forecast.read()
                    response_forecast.close()

                    forecast_data = json.loads(contents_forecast)

                    self.data[self._plz]["forecast-chart"] = forecast_data
                return self.data

            raise MeteoSwissApiError(
                f"Got status {response_forecast.status} from meteo"
            )
        except (ClientConnectorError, ServerTimeoutError, MeteoSwissApiError) as exc:
            if self.session is not None:
                await self.session.close()
                self.session = None
            raise MeteoSwissApiError(exc) from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise MeteoSwissNoDataError(exc) from exc

    @property
    def last_update(self) -> dict | None:
        """Return the timestamp of the most recent data."""
        if self._version_forecast is not None:
            return {
                "forecast-chart": self._version_forecast,
                "weather-widget/forecast": self._version_weather,
            }
        return None

    async def __aenter__(self) -> MeteoSwissData:
        """Async enter.

        Returns:
            The MeteSwiss object.
        """
        return self

    async def __aexit__(self, *_exc_info) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.
        """
        if self.session is not None:
            await self.session.close()
            self.session = None
