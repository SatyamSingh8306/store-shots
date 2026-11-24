import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path():
    """Portable temp directory fixture (avoids pytest's locked basetemp on Windows)."""
    path = Path(tempfile.mkdtemp(prefix="store-shots-test-"))
    yield path
    shutil.rmtree(path, ignore_errors=True)
