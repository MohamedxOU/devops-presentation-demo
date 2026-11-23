import pytest

from app import create_app
from app.data import EXPOSES


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_version_expose_les_champs_attendus(client):
    data = client.get("/version").get_json()
    assert set(data) == {"version", "commit", "env"}


def test_page_accueil_liste_tous_les_exposes(client):
    html = client.get("/").get_data(as_text=True)
    for expose in EXPOSES:
        assert expose["titre"] in html


def test_api_liste(client):
    data = client.get("/api/exposes").get_json()
    assert len(data) == len(EXPOSES)


def test_api_expose_existant(client):
    data = client.get("/api/exposes/1").get_json()
    assert data["titre"] == "Culture DevOps et chaîne CI/CD"


def test_api_expose_inexistant(client):
    response = client.get("/api/exposes/99")
    assert response.status_code == 404


def test_chaque_expose_a_une_salle():
    assert all(e.get("salle") for e in EXPOSES)


def test_metrics_exposees(client):
    client.get("/health")
    body = client.get("/metrics").get_data(as_text=True)
    assert "app_http_requests_total" in body
    assert "app_build_info" in body
