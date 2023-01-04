"""Asynchronus Python client debugging"""
import asyncio

import src.meteoswiss.meteoswiss
from src.meteoswiss.exceptions import MeteoSwissError


async def main():
    """Sample of getting data"""
    try:
        async with src.meteoswiss.meteoswiss.MeteoSwissData(default_plz=9000) as meteo:
            await meteo.check_for_newest_version()
            print("Current Forecast Version: " + meteo.last_update["forecast-chart"])
            print(
                "Current Weather Widget Forecast Version: "
                + meteo.last_update["weather-widget/forecast"]
            )
            forecast = await meteo.update()
            plzs = forecast.keys()
            print("Got Following PLZ data")
            for plz in plzs:
                city_name = forecast[plz]["weather"]["city_name"]
                print(str(plz) + "- City Name: " + city_name)

    except (MeteoSwissError) as exc:
        print(exc)


if __name__ == "__main__":
    asyncio.run(main())
