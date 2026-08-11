import os
import tempfile

TEST_DATA_DIR = tempfile.mkdtemp(prefix="ai-novel-ide-test-")
os.environ["AI_NOVEL_DATA_DIR"] = TEST_DATA_DIR

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
