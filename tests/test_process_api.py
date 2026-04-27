from fastapi.testclient import TestClient

from app.main import app


def assert_process_response_format(data):
    assert "process_id" in data
    assert "status" in data
    assert "progress" in data
    assert "started_at" in data
    assert "estimated_completion" in data
    assert "results" in data

    assert "total_files" in data["progress"]
    assert "processed_files" in data["progress"]
    assert "percentage" in data["progress"]


def test_health_check():
    # No necesita DB: usa el cliente global solo para el health check
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_start_process(client):
    response = client.post("/process/start")

    assert response.status_code == 201

    data = response.json()

    assert_process_response_format(data)
    assert data["status"] in ["PENDING", "RUNNING", "COMPLETED"]


def test_list_processes(client):
    client.post("/process/start")

    response = client.get("/process/list")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_get_process_status(client):
    start_response = client.post("/process/start")
    process_id = start_response.json()["process_id"]

    response = client.get(f"/process/status/{process_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["process_id"] == process_id
    assert "status" in data
    assert "progress" in data


def test_get_process_not_found(client):
    # ID con formato inválido: el servicio lanza ValueError → 422
    response = client.get("/process/status/non-existing-process-id")
    assert response.status_code == 422


def test_get_process_logs(client):
    start_response = client.post("/process/start")
    process_id = start_response.json()["process_id"]

    response = client.get(f"/process/logs/{process_id}")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stop_process(client_no_bg):
    # Usa client_no_bg para que el proceso quede en PENDING y pueda detenerse
    start_response = client_no_bg.post("/process/start")
    process_id = start_response.json()["process_id"]

    response = client_no_bg.post(f"/process/stop/{process_id}")

    assert response.status_code == 200

    data = response.json()
    assert_process_response_format(data)
    assert data["process_id"] == process_id
    assert data["status"] == "STOPPED"


def test_get_process_results(client):
    start_response = client.post("/process/start")
    process_id = start_response.json()["process_id"]

    response = client.get(f"/process/results/{process_id}")

    assert response.status_code == 200

    data = response.json()
    assert_process_response_format(data)
    assert data["process_id"] == process_id
    assert data["status"] == "COMPLETED"
    assert data["results"]["total_words"] > 0
    assert len(data["results"]["files_processed"]) > 0


def test_stop_process_not_found(client):
    # ID no-UUID: stop_process no valida formato, va a la DB, no encuentra nada → 404
    response = client.post("/process/stop/non-existing-process-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Process not found"


def test_get_process_results_not_found(client):
    # ID con formato inválido → 422
    response = client.get("/process/results/non-existing-process-id")
    assert response.status_code == 422


def test_get_process_status_invalid_id(client):
    response = client.get("/process/status/12345")
    assert response.status_code == 422


def test_stop_process_invalid_state(client_no_bg):
    # Usa client_no_bg: proceso queda en PENDING, primer stop lo lleva a STOPPED,
    # segundo stop falla porque STOPPED no es un estado detenible
    start_response = client_no_bg.post("/process/start")
    process_id = start_response.json()["process_id"]

    client_no_bg.post(f"/process/stop/{process_id}")

    response = client_no_bg.post(f"/process/stop/{process_id}")
    assert response.status_code in [400, 404]


def test_process_results_empty_file(tmp_path, monkeypatch, client):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    from app.workers import document_worker
    monkeypatch.setattr(document_worker, "DEFAULT_TEXTS_FOLDER", str(tmp_path))

    response = client.post("/process/start")
    assert response.status_code == 201

    process_id = response.json()["process_id"]
    response = client.get(f"/process/results/{process_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["results"]["total_words"] == 0


def test_internal_error_handling(db_session, monkeypatch):
    # raise_server_exceptions=False: devuelve 500 en vez de re-lanzar la excepción
    from app.core.database import get_db
    from app.repositories import process_repository
    from app.services import process_service

    app.dependency_overrides[get_db] = lambda: db_session
    monkeypatch.setattr(process_service, "SessionLocal", lambda: db_session)
    def fail(*_args, **_kwargs):
        raise Exception("DB error simulado")

    monkeypatch.setattr(process_repository, "get_process_by_id", fail)

    test_client = TestClient(app, raise_server_exceptions=False)
    valid_uuid = "00000000-0000-0000-0000-000000000000"
    response = test_client.get(f"/process/status/{valid_uuid}")
    assert response.status_code == 500

    app.dependency_overrides.clear()
