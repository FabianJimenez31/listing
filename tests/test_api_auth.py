"""Integration tests for /api/v1/auth endpoints."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "user@example.com",
            "password": "SecurePass1",
            "full_name": "Jane Doe",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "user@example.com"
        assert data["full_name"] == "Jane Doe"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "Pass1234", "full_name": "A"}
        client.post("/api/v1/auth/register", json=payload)
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_short_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "x@example.com", "password": "abc", "full_name": "X",
        })
        assert resp.status_code == 422

    def test_register_blank_name(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "x@example.com", "password": "Pass1234", "full_name": "   ",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "not-an-email", "password": "Pass1234", "full_name": "X",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "login@example.com", "password": "SecurePass1", "full_name": "Login User",
        })
        resp = client.post("/api/v1/auth/login", json={
            "email": "login@example.com", "password": "SecurePass1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "bad@example.com", "password": "Correct1", "full_name": "Bad",
        })
        resp = client.post("/api/v1/auth/login", json={
            "email": "bad@example.com", "password": "WrongPass",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "ghost@example.com", "password": "any",
        })
        assert resp.status_code == 401

    def test_login_no_password_asks_for_password(self, client):
        # Non-staff account, email only → backend asks for the password.
        client.post("/api/v1/auth/register", json={
            "email": "nopw@example.com", "password": "SecurePass1", "full_name": "N",
        })
        resp = client.post("/api/v1/auth/login", json={"email": "nopw@example.com"})
        assert resp.status_code == 200
        assert resp.json()["password_required"] is True
        assert resp.json().get("access_token") is None


class TestRefresh:
    def test_refresh_success(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "refresh@example.com", "password": "Pass1234!", "full_name": "R",
        })
        tokens = client.post("/api/v1/auth/login", json={
            "email": "refresh@example.com", "password": "Pass1234!",
        }).json()
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_with_access_token_fails(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "refresh2@example.com", "password": "Pass1234!", "full_name": "R2",
        })
        tokens = client.post("/api/v1/auth/login", json={
            "email": "refresh2@example.com", "password": "Pass1234!",
        }).json()
        # Pass access token where refresh token is expected
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
        assert resp.status_code == 401


class TestLoginOtp:
    """Email 2FA for staff logins (gated by OTP_2FA_ENABLED)."""

    FIXED_CODE = "123456"

    @pytest.fixture
    def otp_on(self, monkeypatch):
        monkeypatch.setenv("OTP_2FA_ENABLED", "true")
        monkeypatch.setattr("src.auth.login_otp.generate_code", lambda: self.FIXED_CODE)

    def _login(self, client, email, password="Password123"):
        return client.post("/api/v1/auth/login", json={"email": email, "password": password})

    def test_flag_off_admin_gets_tokens(self, client, admin_user):
        # 2FA disabled by default → admin logs in directly (back-compatible).
        data = self._login(client, "admin@test.com").json()
        assert data["access_token"]
        assert not data.get("otp_required")

    def test_admin_login_requires_otp(self, client, admin_user, otp_on):
        data = self._login(client, "admin@test.com").json()
        assert data["otp_required"] is True
        assert data["challenge_id"]
        assert data.get("access_token") is None

    def test_agent_login_requires_otp(self, client, agent_user, otp_on):
        assert self._login(client, "agent@test.com").json()["otp_required"] is True

    def test_verify_correct_code_returns_tokens(self, client, admin_user, otp_on):
        challenge = self._login(client, "admin@test.com").json()["challenge_id"]
        resp = client.post("/api/v1/auth/login/verify", json={"challenge_id": challenge, "code": self.FIXED_CODE})
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    def test_verify_wrong_code_rejected(self, client, admin_user, otp_on):
        challenge = self._login(client, "admin@test.com").json()["challenge_id"]
        resp = client.post("/api/v1/auth/login/verify", json={"challenge_id": challenge, "code": "000000"})
        assert resp.status_code == 401

    def test_code_is_single_use(self, client, admin_user, otp_on):
        challenge = self._login(client, "admin@test.com").json()["challenge_id"]
        client.post("/api/v1/auth/login/verify", json={"challenge_id": challenge, "code": self.FIXED_CODE})
        again = client.post("/api/v1/auth/login/verify", json={"challenge_id": challenge, "code": self.FIXED_CODE})
        assert again.status_code == 401

    def test_staff_login_passwordless_no_password(self, client, admin_user, otp_on):
        # No password sent — staff still get the OTP step (passwordless).
        resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com"})
        assert resp.json()["otp_required"] is True

    def test_non_staff_bypasses_otp(self, client, otp_on):
        client.post("/api/v1/auth/register", json={
            "email": "buyer@example.com", "password": "Password123", "full_name": "Buyer",
        })
        data = self._login(client, "buyer@example.com").json()
        assert data["access_token"]
        assert not data.get("otp_required")


class TestMe:
    def test_me_authenticated(self, client, agent_user, agent_token):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {agent_token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "agent@test.com"

    def test_me_no_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401
