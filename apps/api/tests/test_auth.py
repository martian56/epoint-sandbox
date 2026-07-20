import pytest

from epoint_sandbox.config import DEFAULT_MERCHANTS, get_settings
from epoint_sandbox.services import auth, merchants
from epoint_sandbox.services.seed import seed_default_merchants

EMAIL = "admin@example.com"
PASSWORD = "staging-password"


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv("EPOINT_ADMIN_EMAIL", EMAIL)
    monkeypatch.setenv("EPOINT_ADMIN_PASSWORD", PASSWORD)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def login(client):
    return client.post("/_sandbox/auth/login", json={"email": EMAIL, "password": PASSWORD})


class TestOpenByDefault:
    def test_sandbox_endpoints_need_no_credentials(self, client):
        assert client.get("/_sandbox/merchants").status_code == 200

    def test_session_reports_no_auth_required(self, client):
        body = client.get("/_sandbox/auth/session").json()
        assert body["auth_required"] is False
        assert body["authenticated"] is True

    def test_login_is_a_no_op(self, client):
        body = login(client).json()
        assert body["auth_required"] is False


class TestSecured:
    def test_sandbox_endpoints_are_refused(self, client, secured):
        assert client.get("/_sandbox/merchants").status_code == 401

    def test_session_reports_a_login_is_needed(self, client, secured):
        body = client.get("/_sandbox/auth/session").json()
        assert body["auth_required"] is True
        assert body["authenticated"] is False
        assert body["email"] is None

    def test_login_grants_access(self, client, secured):
        assert login(client).status_code == 200
        assert client.get("/_sandbox/merchants").status_code == 200

    def test_session_reports_the_signed_in_email(self, client, secured):
        login(client)
        body = client.get("/_sandbox/auth/session").json()
        assert body["authenticated"] is True
        assert body["email"] == EMAIL

    def test_logout_revokes_access(self, client, secured):
        login(client)
        client.post("/_sandbox/auth/logout")
        assert client.get("/_sandbox/merchants").status_code == 401

    @pytest.mark.parametrize(
        ("email", "password"),
        [
            (EMAIL, "wrong"),
            ("someone@example.com", PASSWORD),
            ("", ""),
        ],
    )
    def test_bad_credentials_are_refused(self, client, secured, email, password):
        response = client.post("/_sandbox/auth/login", json={"email": email, "password": password})
        assert response.status_code == 401
        assert client.get("/_sandbox/merchants").status_code == 401

    def test_email_is_matched_case_insensitively(self, client, secured):
        response = client.post(
            "/_sandbox/auth/login", json={"email": EMAIL.upper(), "password": PASSWORD}
        )
        assert response.status_code == 200

    def test_scripts_authenticate_with_a_bearer_token(self, client, secured):
        response = client.get(
            "/_sandbox/merchants", headers={"Authorization": f"Bearer {PASSWORD}"}
        )
        assert response.status_code == 200

    def test_a_wrong_bearer_token_is_refused(self, client, secured):
        response = client.get("/_sandbox/merchants", headers={"Authorization": "Bearer nope"})
        assert response.status_code == 401

    def test_the_session_cookie_is_not_readable_from_javascript(self, client, secured):
        cookie = login(client).headers["set-cookie"]
        assert "HttpOnly" in cookie

    def test_health_stays_open_for_container_checks(self, client, secured):
        assert client.get("/_sandbox/health").status_code == 200

    def test_the_gateway_api_is_untouched(self, client, secured):
        """Signature auth already covers /api/1, and requiring more would break parity."""
        assert client.get("/api/heartbeat").status_code == 200

    def test_checkout_stays_open(self, client, secured, merchant):
        """Customers paying an invoice are not the dashboard admin."""
        assert client.get("/checkout/unknown-token").status_code in (200, 404)


class TestTokens:
    def test_a_token_from_different_credentials_is_refused(self, monkeypatch):
        monkeypatch.setenv("EPOINT_ADMIN_EMAIL", EMAIL)
        monkeypatch.setenv("EPOINT_ADMIN_PASSWORD", PASSWORD)
        get_settings.cache_clear()
        token = auth.issue_token()

        monkeypatch.setenv("EPOINT_ADMIN_PASSWORD", "rotated")
        get_settings.cache_clear()
        assert auth.token_valid(token) is False
        get_settings.cache_clear()

    def test_an_expired_token_is_refused(self, monkeypatch, secured):
        monkeypatch.setattr("time.time", lambda: 0)
        token = auth.issue_token()
        monkeypatch.undo()
        get_settings.cache_clear()
        monkeypatch.setenv("EPOINT_ADMIN_EMAIL", EMAIL)
        monkeypatch.setenv("EPOINT_ADMIN_PASSWORD", PASSWORD)
        get_settings.cache_clear()

        assert auth.token_valid(token) is False

    @pytest.mark.parametrize("token", ["", "junk", "123", "123.", ".abc", "abc.def"])
    def test_malformed_tokens_are_refused(self, secured, token):
        assert auth.token_valid(token) is False

    def test_tokens_are_refused_when_auth_is_off(self):
        get_settings.cache_clear()
        assert auth.token_valid("anything") is False


class TestSeededKeys:
    def test_published_keys_are_used_when_the_sandbox_is_open(self, session):
        get_settings.cache_clear()
        seeded = seed_default_merchants(session)
        assert seeded[0].private_key == DEFAULT_MERCHANTS[0][1]

    def test_generated_keys_are_used_when_a_password_is_set(self, session, secured):
        seeded = seed_default_merchants(session)

        published = {private for _, private, _ in DEFAULT_MERCHANTS}
        for merchant in seeded:
            assert merchant.private_key not in published
            assert len(merchant.private_key) == merchants.PRIVATE_KEY_LENGTH

    def test_public_keys_stay_predictable_either_way(self, session, secured):
        """Only the secret changes. Split payments still reference i000000002."""
        seeded = seed_default_merchants(session)
        assert [m.public_key for m in seeded] == [public for public, _, _ in DEFAULT_MERCHANTS]
