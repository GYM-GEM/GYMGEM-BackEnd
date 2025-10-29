from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from accounts.models import Account
from profiles.models import Profile
from authenticationAndAuthorization.serializers import (
    MyTokenObtainPairSerializer,
    MyTokenRefreshSerializer,
)


class MyTokenSerializerTests(TestCase):
    def setUp(self):
        self.account: Account = Account.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="pass1234",
            first_name="Alice",
            last_name="Smith",
        )
        Profile.objects.create(account=self.account, profile_type="store")

    def test_get_token_includes_custom_claims(self):
        token = MyTokenObtainPairSerializer.get_token(self.account)

        self.assertEqual(token["username"], "alice")
        self.assertEqual(token["email"], "alice@example.com")
        self.assertEqual(token["account_id"], self.account.pk)
        self.assertListEqual(token["profile_types"], ["store"])

    def test_refresh_serializer_rebuilds_access_claims(self):
        refresh = RefreshToken.for_user(self.account)

        serializer = MyTokenRefreshSerializer()
        validated = serializer.validate({"refresh": str(refresh)})

        self.assertIn("access", validated)
        self.assertIn("refresh", validated)

        new_access = AccessToken(validated["access"])
        self.assertEqual(new_access["username"], self.account.username)
        self.assertEqual(new_access["email"], self.account.email)
        self.assertEqual(new_access["account_id"], self.account.pk)
        self.assertListEqual(new_access["profile_types"], ["store"])
