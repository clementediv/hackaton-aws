import sys

import pytest


@pytest.fixture(autouse=True)
def _no_real_aws(monkeypatch):
    """The app reads and writes the event's AWS account when credentials exist;
    tests must not. Tests that need AWS use moto and call the functions directly."""
    monkeypatch.setenv("CA_AWS", "0")
    yield
    # A successful AWS check under moto must not survive into an offline UI test.
    if streamlit := sys.modules.get("streamlit"):
        streamlit.cache_data.clear()
