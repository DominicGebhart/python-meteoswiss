"""Exceptions for Meteo Swiss."""


class MeteoSwissError(Exception):
    """Generic MeteoSwiss exception."""


class MeteoSwissPLZNotFoundError(MeteoSwissError):
    """MeteoSwiss PLZ weather not found."""


class MeteoSwissNoDataError(MeteoSwissError):
    """MeteoSwiss no data exception."""


class MeteoSwissApiError(MeteoSwissError):
    """MeteoSwiss api exception."""
