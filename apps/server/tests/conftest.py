import os
import tempfile

TEST_DATA_DIR = tempfile.mkdtemp(prefix="ai-novel-ide-test-")
os.environ["AI_NOVEL_DATA_DIR"] = TEST_DATA_DIR
# 测试不依赖真实 AI 凭证：即使本机 .env 配置了 Key，也强制走"未配置"路径
os.environ["AI_NOVEL_DEEPSEEK_API_KEY"] = ""
os.environ["AI_NOVEL_SEEDREAM_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
