class OllamaramaError(Exception):
    """Base error for Ollamarama components."""


class ConfigurationError(OllamaramaError):
    """Invalid or missing configuration."""


class NetworkError(OllamaramaError):
    """HTTP or connection failure talking to external services."""


class AuthError(OllamaramaError):
    """Authentication or authorization failure."""


class RuntimeFailure(OllamaramaError):
    """Unexpected runtime error."""

