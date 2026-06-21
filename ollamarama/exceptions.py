class OllamaramaError(Exception):
    """Base error for Ollamarama components."""


class NetworkError(OllamaramaError):
    """HTTP or connection failure talking to external services."""


class RuntimeFailure(OllamaramaError):
    """Unexpected runtime error."""

