"""Exception classes for the Temu Product Scraper SDK."""


class TemuScraperError(Exception):
    """Base exception for all SDK errors."""


class AuthenticationError(TemuScraperError):
    """Raised when the Apify API token is missing or invalid."""


class ActorRunError(TemuScraperError):
    """Raised when the actor run fails on Apify infrastructure."""


class ActorTimeoutError(TemuScraperError):
    """Raised when the actor run does not finish within the allowed timeout."""
