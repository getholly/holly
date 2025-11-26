from __future__ import annotations

import os
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient
from faker import Faker
import factory
import pytest

# Add project root to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Provide stub for missing mcp_python_client dependency
sys.modules.setdefault("mcp_python_client", SimpleNamespace(MCPClient=object))

fake = Faker()


class FileFactory(factory.Factory):
    class Meta:
        model = dict

    filename = factory.LazyFunction(lambda: fake.file_name())
    content = factory.LazyFunction(lambda: fake.binary(length=20))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BASE_DIR", str(tmp_path))
    from importlib import reload
    import rest_mcp_client.routes.files as files_route
    reload(files_route)
    from rest_mcp_client.main import app
    return TestClient(app)


def test_upload_single_file(client, tmp_path):
    file_data = FileFactory()
    files = [
        (
            "files",
            (file_data["filename"], file_data["content"], "application/octet-stream"),
        )
    ]
    response = client.post("/api/files/upload", files=files, data={"target_dir": "uploads"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["directory"] == "uploads"
    saved_path = tmp_path / "uploads" / file_data["filename"]
    assert saved_path.exists()
    assert saved_path.read_bytes() == file_data["content"]


def test_sanitize_directory(client, tmp_path):
    file_data = FileFactory()
    files = [
        (
            "files",
            (file_data["filename"], file_data["content"], "application/octet-stream"),
        )
    ]
    bad_dir = "../evil/../safe"
    response = client.post("/api/files/upload", files=files, data={"target_dir": bad_dir})
    assert response.status_code == 200
    data = response.json()
    assert data["directory"] == "evil/safe"
    saved_path = tmp_path / "evil" / "safe" / file_data["filename"]
    assert saved_path.exists()
