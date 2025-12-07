import jwt
from rest_framework import serializers, generics
from GymGem import settings
from accounts.models import Account
from .models import Category
from .serializers import CategorySerializer


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


class CategoryListView(generics.ListAPIView):
    """Return a list of all categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = []
