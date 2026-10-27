import os
from pathlib import Path

os.environ.setdefault("AUTH_DB_PATH", str(Path(__file__).parent / "test-auth-bootstrap.sqlite3"))
os.environ.setdefault("SESSION_COOKIE_SECURE", "0")

from fastapi.testclient import TestClient
import auth_store
import api


def setup_accounts(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "api-auth.sqlite3"))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "unique-admin-password-2026")
    api.LOGIN_ATTEMPTS.clear()
    auth_store.init_auth_db()


def signup(client, email, name, role):
    response = client.post("/api/auth/register", json={
        "email": email,
        "display_name": name,
        "password": "a-strong-password-2026",
        "role": role,
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_farm_tenant_isolation_and_role_guards(monkeypatch, tmp_path):
    setup_accounts(monkeypatch, tmp_path)
    farmer_one = TestClient(api.app)
    farmer_two = TestClient(api.app)
    student = TestClient(api.app)
    admin = TestClient(api.app)

    one = signup(farmer_one, "one@example.com", "Farmer One", "farmer")
    signup(farmer_two, "two@example.com", "Farmer Two", "farmer")
    signup(student, "student@example.com", "Student", "student")

    create = farmer_one.post(
        "/api/farms",
        json={"name": "My North Field", "soil_moisture": 37.5},
        headers={"X-CSRF-Token": one["csrf_token"]},
    )
    assert create.status_code == 200
    farm_id = create.json()["id"]

    assert [farm["id"] for farm in farmer_one.get("/api/farms").json()] == [farm_id]
    assert farmer_two.get("/api/farms").json() == []
    assert farmer_two.get(f"/api/farms/{farm_id}").status_code == 404
    assert farmer_two.patch(
        f"/api/farms/{farm_id}",
        json={"name": "Unauthorized edit"},
        headers={"X-CSRF-Token": farmer_two.get("/api/auth/me").json()["csrf_token"]},
    ).status_code == 404
    assert student.get("/api/farms").status_code == 403

    admin_login = admin.post("/api/auth/login", json={
        "email": "admin@example.com", "password": "unique-admin-password-2026"
    })
    assert admin_login.status_code == 200
    admin_csrf = admin_login.json()["csrf_token"]
    assert admin.get("/api/farms").status_code == 403
    assert admin.get(f"/api/farms/{farm_id}").status_code == 403
    assert admin.post(
        "/api/farms", json={"name": "Admin must not create farms"},
        headers={"X-CSRF-Token": admin_csrf},
    ).status_code == 403
    assert admin.patch(
        f"/api/farms/{farm_id}", json={"name": "Admin must not edit farms"},
        headers={"X-CSRF-Token": admin_csrf},
    ).status_code == 403
    assert admin.delete(
        f"/api/farms/{farm_id}", headers={"X-CSRF-Token": admin_csrf}
    ).status_code == 403
    assert admin.get("/api/admin/users").status_code == 200


def test_authenticated_mutations_require_csrf(monkeypatch, tmp_path):
    setup_accounts(monkeypatch, tmp_path)
    farmer = TestClient(api.app)
    signup(farmer, "farmer@example.com", "Farmer", "farmer")
    response = farmer.post("/api/farms", json={"name": "No CSRF"})
    assert response.status_code == 403


def test_admin_is_not_publicly_registerable(monkeypatch, tmp_path):
    setup_accounts(monkeypatch, tmp_path)
    client = TestClient(api.app)
    response = client.post("/api/auth/register", json={
        "email": "attacker@example.com",
        "display_name": "Attacker",
        "password": "a-strong-password-2026",
        "role": "admin",
    })
    assert response.status_code == 422


def test_students_only_list_and_open_owned_lectures(monkeypatch, tmp_path):
    import sys
    import types

    setup_accounts(monkeypatch, tmp_path)
    student_one = TestClient(api.app)
    student_two = TestClient(api.app)
    admin = TestClient(api.app)
    one = signup(student_one, "lecture-one@example.com", "Student One", "student")
    two = signup(student_two, "lecture-two@example.com", "Student Two", "student")
    records = [
        {"id": "owned-one", "title": "Owned one", "owner_user_id": one["user"]["id"], "num_chunks": 1, "created_at": "2026-10-20T10:00:00"},
        {"id": "owned-two", "title": "Owned two", "owner_user_id": two["user"]["id"], "num_chunks": 1, "created_at": "2026-10-20T10:00:00"},
        {"id": "legacy", "title": "Legacy record", "owner_user_id": None, "num_chunks": 1, "created_at": "2026-10-19T10:00:00"},
    ]
    fake_store = types.ModuleType("core.vector_store")
    fake_store.list_lectures = lambda: records
    fake_store.get_lecture = lambda lecture_id: next((record for record in records if record["id"] == lecture_id), None)
    monkeypatch.setitem(sys.modules, "core.vector_store", fake_store)
    fake_summarizer = types.ModuleType("features.summarizer")
    fake_summarizer.summarize = lambda docs: "summary for owned lecture"
    monkeypatch.setitem(sys.modules, "features.summarizer", fake_summarizer)
    monkeypatch.setattr(api, "get_runtime", lambda lecture_id: {"docs": []})
    api.SUMMARIES.clear()

    assert [item["id"] for item in student_one.get("/api/lectures").json()] == ["owned-one"]
    assert student_one.get("/api/lectures/owned-two/summary").status_code == 404
    assert student_one.get("/api/lectures/legacy/summary").status_code == 404
    assert student_one.get("/api/lectures/owned-one/summary").json()["summary"] == "summary for owned lecture"

    admin_login = admin.post("/api/auth/login", json={
        "email": "admin@example.com", "password": "unique-admin-password-2026"
    })
    assert admin_login.status_code == 200
    assert {item["id"] for item in admin.get("/api/lectures").json()} == {"owned-one", "owned-two", "legacy"}

    eval_payload = {"items": [{"question": "What is tested?", "ground_truth": "Role access"}]}
    student_eval = student_one.post(
        "/api/lectures/owned-one/evaluate", json=eval_payload,
        headers={"X-CSRF-Token": one["csrf_token"]},
    )
    assert student_eval.status_code == 403

    fake_evaluator = types.ModuleType("features.evaluator")
    fake_evaluator.quick_evaluate = lambda engine, items: {
        "faithfulness": 0.9,
        "answer_relevancy": 0.8,
        "context_precision": 0.85,
        "context_recall": 0.75,
    }
    monkeypatch.setitem(sys.modules, "features.evaluator", fake_evaluator)
    monkeypatch.setattr(api, "get_engine", lambda *args: object())
    admin_eval = admin.post(
        "/api/lectures/owned-one/evaluate", json=eval_payload,
        headers={"X-CSRF-Token": admin_login.json()["csrf_token"]},
    )
    assert admin_eval.status_code == 200, admin_eval.text
    assert admin_eval.json()["n"] == 1
