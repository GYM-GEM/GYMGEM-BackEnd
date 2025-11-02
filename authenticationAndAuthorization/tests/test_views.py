from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Account
from profiles.models import Profile


class AuthenticationViewsTests(APITestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="pass1234",
            first_name="Bob",
            last_name="Jones",
        )
        Profile.objects.create(account=self.account, profile_type="trainer")
        self.login_url = reverse("account_login")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")
        self.logout_all_url = reverse("logout_all")

    def _login(self, **payload):
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    def test_login_with_username(self):
        response = self.client.post(
            self.login_url,
            {"username": "bob", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        self.assertEqual(body["account"]["email"], "bob@example.com")
        self.assertIn("trainer", body["account"]["profile_types"])

    def test_login_with_email(self):
        response = self.client.post(
            self.login_url,
            {"email": "bob@example.com", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["account"]["username"], "bob")

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {"username": "bob", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_unknown_email(self):
        response = self.client.post(
            self.login_url,
            {"email": "unknown@example.com", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_returns_new_claims(self):
        tokens = self._login(username="bob", password="pass1234")
        refresh = tokens["refresh"]

        response = self.client.post(
            self.refresh_url,
            data={},
            format="json",
            HTTP_REFRESH=refresh,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)

    def test_logout_blacklists_refresh_token(self):
        tokens = self._login(username="bob", password="pass1234")
        refresh = tokens["refresh"]

        response = self.client.post(
            self.logout_url,
            data={},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_REFRESH=refresh,
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Subsequent logout with same token should fail
        response = self.client.post(
            self.logout_url,
            data={},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_REFRESH=refresh,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_requires_refresh_header(self):
        self._login(username="bob", password="pass1234")
        response = self.client.post(
            self.logout_url,
            data={},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self._login(username='bob', password='pass1234')['access']}",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_all_blacklists_all_tokens(self):
        tokens = self._login(username="bob", password="pass1234")
        access = tokens["access"]
        refresh = tokens["refresh"]

        # Authenticate request with access token
        response = self.client.post(
            self.logout_all_url,
            data={},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Try refreshing using previously issued token -> should fail due to blacklist
        response = self.client.post(
            self.refresh_url,
            data={},
            format="json",
            HTTP_REFRESH=refresh,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
