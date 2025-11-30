import jwt
from rest_framework import serializers
from GymGem import settings
from accounts.models import Account


# Create your views here.
def get_account_from_token(request):
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = None
        if token:

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            except Exception as e:
                print("Token decode error:", str(e))

    # Alternative: if account_id is in the token payload
    # You can access it via request.auth or user attributes depending on your JWT setup
    print("Payload:", payload)
    account_id = payload.get("user_id", None) if payload else None
    print("Account ID from token:", account_id)
    if not account_id:
        raise serializers.ValidationError("Account ID not found in token.")

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
