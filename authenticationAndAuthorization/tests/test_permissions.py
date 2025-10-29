from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser

from accounts.models import Account
from profiles.models import Profile
from authenticationAndAuthorization.permissions import required_roles


def dummy_view(request):
    return "ok"


class RequiredRolesDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.account = Account.objects.create_user(
            username="carol",
            email="carol@example.com",
            password="pass1234",
        )
        Profile.objects.create(account=self.account, profile_type="gym")

    def test_requires_authentication(self):
        request = self.factory.get("/any")
        request.user = AnonymousUser()

        protected = required_roles("gym")(dummy_view)
        response = protected(request)

        self.assertEqual(response.status_code, 401)

    def test_denies_when_missing_role(self):
        request = self.factory.get("/any")
        request.user = self.account

        protected = required_roles("trainer")(dummy_view)
        response = protected(request)

        self.assertEqual(response.status_code, 403)

    def test_allows_when_role_present(self):
        request = self.factory.get("/any")
        request.user = self.account

        protected = required_roles("gym")(dummy_view)
        response = protected(request)

        self.assertEqual(response, "ok")
        self.assertTrue(hasattr(request.user, "roles"))
        self.assertIn("gym", request.user.roles)

    def test_allows_when_no_roles_specified(self):
        request = self.factory.get("/any")
        request.user = self.account

        protected = required_roles()(dummy_view)
        response = protected(request)

        self.assertEqual(response, "ok")
