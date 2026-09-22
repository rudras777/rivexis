import os, tempfile
os.environ["DATABASE_URL"]="sqlite:///./test_rivexis.db"
os.environ["RIVEXIS_AUTH_SECRET"]="test-secret-with-sufficient-entropy"
os.environ["ENABLE_DEMO_ADAPTER"]="true"
import pytest
from fastapi.testclient import TestClient
from rivexis_api.main import app
from rivexis_api.services.db import Base, engine
@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine);yield
@pytest.fixture
def client():
    with TestClient(app) as c:yield c
