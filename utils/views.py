from utils.serializers import SpecializationSerializer
from utils.models import Specialization
import jwt
from rest_framework import serializers, generics
from GymGem import settings
from accounts.models import Account
from .models import Category
from .serializers import CategorySerializer
from drf_spectacular.utils import extend_schema
import requests
import time


def get_account_from_token(request):
    auth_header = request.headers.get("Authorization")
    payload = None

    if not auth_header or not auth_header.startswith("Bearer "):
        raise serializers.ValidationError("Authorization header is missing or invalid.")

    token = auth_header.split(" ")[1]

    # Decode token safely
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise serializers.ValidationError("Token has expired.")
    except jwt.InvalidTokenError:
        raise serializers.ValidationError("Invalid token.")
    except Exception as e:
        raise serializers.ValidationError(f"Token decode error: {str(e)}")

    # Extract account_id
    account_id = payload.get("user_id")
    if not account_id:
        raise serializers.ValidationError("Account ID not found in token.")

    # Fetch account
    try:
        return Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        raise serializers.ValidationError("Account does not exist.")


def get_profile_id_from_token(request):
    """
    Extract profile_id from the access token in the request.
    """
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    payload = None

    print("TTTTTTT:", token)
    if token:

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except Exception as e:
            print("Token decode error:", str(e))
    profile_id = payload.get("current_profile", None) if payload else None
    return profile_id


def send_verification_email(account, request):
    from django.core.mail import send_mail
    from django.urls import reverse
    from django.conf import settings
    import jwt
    from datetime import datetime, timedelta, timezone

    token_payload = {
        "user_id": account.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    verification_link = request.build_absolute_uri(
        reverse("accounts-verify") + f"?token={token}"
    )
    print("Verification link:", verification_link)
    subject = "Verify your email address"
    message = f"Hi {account.first_name},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nThank you!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [account.email]
    print("Sending email to:", recipient_list)
    send_mail(subject, message, from_email, recipient_list)


@extend_schema(
    tags=["Utils"],
    summary="List categories",
    description="Return a list of all categories",
    responses={200: CategorySerializer(many=True)},
)
class CategoryListView(generics.ListAPIView):
    """Return a list of all categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = []


@extend_schema(
    tags=["Utils"],
    summary="List specializations",
    description="Return a list of all specializations",
    responses={200: SpecializationSerializer(many=True)},
)
class SpecializationListView(generics.ListAPIView):
    """Return a list of all specializations."""

    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = []



BASE_URL = "https://accept.paymob.com/api"


class PaymobService:
    DEFAULT_TIMEOUT = 25
    MAX_RETRIES = 3
    BACKOFF_SECONDS = 1

    @staticmethod
    def authenticate():
        for attempt in range(PaymobService.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{BASE_URL}/auth/tokens",
                    json={"api_key": settings.PAYMOB_API_KEY},
                    timeout=PaymobService.DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                return response.json()["token"]
            except requests.RequestException as e:
                if attempt < PaymobService.MAX_RETRIES - 1:
                    time.sleep(PaymobService.BACKOFF_SECONDS)
                    continue
                raise RuntimeError(f"Paymob auth failed: {e}")

    @staticmethod
    def create_order(auth_token, amount_cents):
        payload = {
            "auth_token": auth_token,
            "delivery_needed": "false",
            "amount_cents": amount_cents,
            "currency": "EGP",
            "items": []
        }
        for attempt in range(PaymobService.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{BASE_URL}/ecommerce/orders",
                    json=payload,
                    timeout=PaymobService.DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt < PaymobService.MAX_RETRIES - 1:
                    time.sleep(PaymobService.BACKOFF_SECONDS)
                    continue
                raise RuntimeError(f"Paymob order creation failed: {e}")

    @staticmethod
    def create_payment_key(auth_token, order_id, amount_cents, billing_data):
        payload = {
            "auth_token": auth_token,
            "amount_cents": amount_cents,
            "expiration": 3600,
            "order_id": order_id,
            "billing_data": billing_data,
            "currency": "EGP",
            "integration_id": settings.PAYMOB_CARD_INTEGRATION_ID
        }
        for attempt in range(PaymobService.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{BASE_URL}/acceptance/payment_keys",
                    json=payload,
                    timeout=PaymobService.DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                return response.json()["token"]
            except requests.RequestException as e:
                if attempt < PaymobService.MAX_RETRIES - 1:
                    time.sleep(PaymobService.BACKOFF_SECONDS)
                    continue
                raise RuntimeError(f"Paymob payment key failed: {e}")

    @staticmethod
    def refund_transaction(auth_token, transaction_id, amount_cents):
        """Attempt to refund a transaction via Paymob.
        Requires a valid auth_token, transaction_id, and amount in cents.
        """
        try:
            response = requests.post(
                f"{BASE_URL}/acceptance/void_refund/refund",
                json={
                    "auth_token": auth_token,
                    "transaction_id": transaction_id,
                    "amount_cents": amount_cents,
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Paymob refund failed: {e}")
