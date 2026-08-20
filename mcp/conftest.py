"""Pytest fixtures für Förder-Radar."""

import pytest

from match import load_catalog


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test.

    Clears catalog cache and reloads server.PROGRAMME from disk
    to ensure test isolation.
    """
    from match import _clear_catalog_cache

    _clear_catalog_cache()

    # Reset server.PROGRAMME to fresh catalog
    import server
    server.PROGRAMME[:] = load_catalog()
