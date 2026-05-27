import pytest
from unittest.mock import patch


@pytest.fixture
def client():
    from app import app
    app.config["TESTING"] = True
    with patch("app.init_db"):
        with app.test_client() as c:
            yield c
