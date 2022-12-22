"""Meteo Swiss Weather Data Client"""
import json

import aiohttp
import async_timeout
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
    dataset_forecast_url: str = "https://www.meteoschweiz.admin.ch/product/output/forecast-chart/version__{}/de/{}.json"

    """API url to fetch the current weather conditions and PLZ data"""
    dataset_weather_url: str = "https://www.meteoschweiz.admin.ch/product/output/weather-widget/forecast/version__{}/de/731000.json"

    request_timeout: float = 8.0
    session: aiohttp.client.ClientSession | None = None
    verify_ssl: bool | None = None
    _timestamp: str | None = None
    _plz: str = ""
    _version_forecast: str = ""
    _version_weather: str = ""

    def __init__(
        self,
        default_plz: str = "7310",
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
