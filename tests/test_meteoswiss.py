"""Tests MeteoSwiss"""
import json
import pathlib
import zoneinfo
from datetime import datetime

import aiohttp
import pytest
from aiohttp.client_exceptions import ClientConnectorError
from src.meteoswiss.exceptions import MeteoSwissApiError
from src.meteoswiss.exceptions import MeteoSwissNoDataError
from src.meteoswiss.exceptions import MeteoSwissPLZNotFoundError
from src.meteoswiss.meteoswiss import MeteoSwissData


@pytest.mark.asyncio
async def test_version(fix_versions) -> None:
    """Test version function"""

    meteoswiss = MeteoSwissData()
    await meteoswiss.check_for_newest_version()

    # picking few values to compare
    assert meteoswiss.last_update["forecast-chart"] == "20230104_1610"
    assert meteoswiss.last_update["weather-widget/forecast"] == "20230104_1508"


@pytest.mark.asyncio
async def test_version_fail(aresponses) -> None:
    """Test version function failing"""

    aresponses.add(
        "www.meteoschweiz.admin.ch",
        "/product/output/versions.json",
        "GET",
        aresponses.Response(text="error", status=500),
    )

    meteoswiss = MeteoSwissData()

    with pytest.raises(MeteoSwissApiError):
        await meteoswiss.check_for_newest_version()


@pytest.fixture
def fix_versions(aresponses):
    """Fixture to get versions"""
    data_versions = json.loads(
        pathlib.Path(__file__)
        .parent.joinpath("data_versions.json")
        .read_text(encoding="utf-8")
    )
    aresponses.add(
        "www.meteoschweiz.admin.ch",
        "/product/output/versions.json",
        "GET",
        response=data_versions,
    )
