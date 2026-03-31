"""memio REST API server — optional HTTP gateway for the memio library."""


def create_app(*args, **kwargs):
    """Lazy wrapper — imports FastAPI only when called."""
    from memio.server.app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__ = ["create_app"]
