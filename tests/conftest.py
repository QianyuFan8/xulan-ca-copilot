"""Assign a layer marker (unit / integration / system / acceptance / smoke) from each test's folder.

Run one layer with e.g. ``pytest -m unit``. Smoke tests are opt-in and skip unless their
environment variables are set (see tests/smoke/test_smoke.py).
"""

from pathlib import Path

import pytest

LAYERS = ('unit', 'integration', 'system', 'acceptance', 'smoke')


def pytest_collection_modifyitems(items):
    for item in items:
        layer = Path(str(item.fspath)).parent.name
        if layer in LAYERS:
            item.add_marker(getattr(pytest.mark, layer))
