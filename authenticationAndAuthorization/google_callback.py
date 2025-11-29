from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from accounts.models import Account


@permission_classes([AllowAny]) 
class GoogleLoginView(APIView):
    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"error": "No ID token provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
        except ValueError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        email = idinfo.get("email")
        if not email:
            return Response({"error": "Email missing in token"}, status=status.HTTP_400_BAD_REQUEST)

        # prepare sensible defaults
        username = email.split("@")[0]
        name = idinfo.get("name", "") or ""
        first_name = idinfo.get("given_name") or (name.split(" ", 1)[0] if name else "")
        last_name = idinfo.get("family_name") or (name.split(" ", 1)[1] if " " in name else "")

        user = Account.objects.filter(email=email).first()
        created = False
        if not user:
            # Prefer the manager create_user if available (handles hashing/flags)
            create_user_fn = getattr(Account.objects, "create_user", None)
            try:
                if callable(create_user_fn):
                    user = Account.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name)
                else:
                    user = Account.objects.create(username=username, email=email, first_name=first_name, last_name=last_name)
                    user.set_unusable_password()
                    user.save()
                created = True
            except Exception as exc:
                return Response({"error": "Failed creating user", "detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ensure user is actually saved (sanity)
        if not user.pk:
            return Response({"error": "User was not persisted to DB"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Use custom tokens with account_id and current_profile claims
        refresh = RefreshToken.for_user(user)
        refresh['account_id'] = user.pk
        refresh['current_profile'] = user.default_profile.id if user.default_profile else None
        
        access = refresh.access_token
        access['account_id'] = user.pk
        access['current_profile'] = user.default_profile.id if user.default_profile else None
        
        return Response({
            "access": str(access),
            "refresh": str(refresh),
            "user": {"id": user.id, "email": user.email, "username": getattr(user, "username", "")},
            "created": created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
