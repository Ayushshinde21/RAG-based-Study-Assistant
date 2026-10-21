import auth_store


def prepare_db(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth-test.sqlite3"))
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    auth_store.init_auth_db()


def test_password_hash_and_session(monkeypatch, tmp_path):
    prepare_db(monkeypatch, tmp_path)
    user = auth_store.create_user("student@example.com", "Sample Student", "long-password-123", "student")
    assert user["role"] == "student"
    assert auth_store.authenticate_user("student@example.com", "long-password-123")["id"] == user["id"]
    assert auth_store.authenticate_user("student@example.com", "incorrect-password") is None
    token, csrf = auth_store.create_session(user["id"])
    session = auth_store.get_session(token)
    assert session["user"]["id"] == user["id"]
    assert session["csrf_token"] == csrf
    auth_store.revoke_session(token)
    assert auth_store.get_session(token) is None


def test_farmer_records_are_filterable_by_owner(monkeypatch, tmp_path):
    prepare_db(monkeypatch, tmp_path)
    one = auth_store.create_user("farmer1@example.com", "Farmer One", "long-password-123", "farmer")
    two = auth_store.create_user("farmer2@example.com", "Farmer Two", "long-password-456", "farmer")
    first_farm = auth_store.create_farm(one["id"], {"name": "Farm Alpha", "soil_moisture": 42.5})
    second_farm = auth_store.create_farm(two["id"], {"name": "Farm Beta", "temperature_c": 28})
    assert [farm["id"] for farm in auth_store.list_farms(one["id"])] == [first_farm["id"]]
    assert [farm["id"] for farm in auth_store.list_farms(two["id"])] == [second_farm["id"]]
    assert len(auth_store.list_farms()) == 2
    assert auth_store.update_farm(second_farm["id"], one["id"], {"name": "Intrusion"}) is None
    assert auth_store.delete_farm(second_farm["id"], one["id"]) is False
    assert auth_store.get_farm(second_farm["id"])["name"] == "Farm Beta"


def test_admin_bootstrap_and_disable_revokes_session(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth-test.sqlite3"))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "a-unique-admin-password")
    auth_store.init_auth_db()
    admin = auth_store.authenticate_user("admin@example.com", "a-unique-admin-password")
    assert admin["role"] == "admin"
    token, _ = auth_store.create_session(admin["id"])
    assert auth_store.set_user_active(admin["id"], False)
    assert auth_store.get_session(token) is None

def test_admin_bootstrap_is_safe_when_account_already_exists(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth-existing-admin.sqlite3"))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "a-unique-admin-password")
    auth_store.init_auth_db()
    auth_store.init_auth_db()
    admin = auth_store.authenticate_user("admin@example.com", "a-unique-admin-password")
    assert admin is not None
    assert admin["role"] == "admin"

