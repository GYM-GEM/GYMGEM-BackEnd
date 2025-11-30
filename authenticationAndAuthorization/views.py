import jwt
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from .serializers import MyTokenObtainPairSerializer, MyTokenRefreshSerializer
from accounts.models import Account
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import permission_classes
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
    OpenApiTypes,
)
from profiles.models import Profile
from django.conf import settings


class MyTokenRefreshView(TokenRefreshView):
    """Custom TokenRefreshView to use MyTokenRefreshSerializer."""

    serializer_class = MyTokenRefreshSerializer

    @extend_schema(
        tags=["Authentication"],
        summary="Refresh JWT token",
        description="Refresh access token using refresh token from headers",
        request=MyTokenRefreshSerializer,
        responses={200: MyTokenRefreshSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.headers)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@permission_classes([AllowAny])
class AccountLoginView(TokenObtainPairView):
    """Login endpoint that returns JWT tokens plus basic account info."""

    serializer_class = MyTokenObtainPairSerializer

    @extend_schema(
        tags=["Authentication"],
        summary="Login with credentials",
        description="Login with username/email and password. Returns JWT tokens and account information.",
        request=MyTokenObtainPairSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access": {"type": "string", "description": "Access token"},
                    "refresh": {"type": "string", "description": "Refresh token"},
                    "account": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "string"},
                            "email": {"type": "string"},
                            "profile_types": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
            400: {"description": "Bad request"},
            401: {"description": "Invalid credentials"},
        },
    )
    def post(self, request, *args, **kwargs):
        # Support login via email or username: if email is provided and username is not,
        # resolve the username from the Account with that email.
        data = request.data.copy()
        if not data.get("username") and data.get("email"):
            email = data.get("email")
            qs = Account.objects.filter(email__iexact=email)
            if not qs.exists():
                return Response(
                    {"detail": "Invalid credentials."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if qs.count() > 1:
                return Response(
                    {
                        "detail": "Multiple accounts use this email. Please login with username."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data["username"] = qs.first().username

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Tokens from SimpleJWT
        tokens = serializer.validated_data

        # Resolve account and enrich response
        user = serializer.user
        account = Account.objects.filter(pk=user.pk).first()
        account_payload = {
            "id": account.pk if account else None,
            "username": user.username,
            "email": user.email,
            "current_profile": (
                account.default_profile.id
                if account and account.default_profile
                else None
            ),
            "profiles": (
                list(
                    zip(
                        account.profiles.values_list("profile_type", flat=True),
                        account.profiles.values_list("id", flat=True),
                    )
                )
                if account
                else []
            ),
        }

        if request.user.is_authenticated:
            current_tokens = OutstandingToken.objects.filter(user=request.user)
            if current_tokens.count() > 5:
                # Blacklist oldest tokens beyond the 5 most recent
                tokens_to_blacklist = current_tokens.order_by("created_at")[0]
                try:
                    BlacklistedToken.objects.get_or_create(token=tokens_to_blacklist)
                except Exception:
                    return Response(
                        {"detail": "Error blacklisting old tokens"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        return Response(
            {
                "access": tokens.get("access"),
                "refresh": tokens.get("refresh"),
                "account": account_payload,
            },
            status=status.HTTP_200_OK,
        )


class SwitchProfileView(APIView):
    """Switch the current profile in the JWT token."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Switch current profile",
        description="Switch the current profile in the JWT token. Requires Authentication header with Bearer token and profile_id in headers.",
        parameters=[
            OpenApiParameter(
                name="Authorization",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Bearer token for authentication (e.g., "Bearer your_access_token")',
            ),
            OpenApiParameter(
                name="profile_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.HEADER,
                required=True,
                description="ID of the profile to switch to",
            ),
        ],
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access": {
                        "type": "string",
                        "description": "New access token with switched profile",
                    },
                    "refresh": {"type": "string", "description": "Refresh token"},
                },
            },
            400: {"description": "Bad request - missing or invalid profile_id"},
            401: {"description": "Unauthorized - invalid or missing access token"},
        },
    )
    def post(self, request):
        profile_id = request.data.get("profile_id")
        if not profile_id:
            return Response(
                {"detail": "profile_id header is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        try:
            profile = Profile.objects.get(pk=profile_id)
        except Exception:
            return Response(
                {"detail": "Profile not found or does not belong to user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create new tokens with updated current_profile claim
        refresh = RefreshToken.for_user(user)
        refresh["current_profile"] = profile.pk

        access = refresh.access_token
        access["current_profile"] = profile.pk

        return Response(
            {"access": str(access), "refresh": str(refresh)}, status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Logout user",
        description="Logout the current user by blacklisting their refresh token. Requires Authentication header with Bearer token and refresh token in custom header.",
        parameters=[
            OpenApiParameter(
                name="Authorization",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Bearer token for authentication (e.g., "Bearer your_access_token")',
            ),
            OpenApiParameter(
                name="refresh",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Refresh token to be blacklisted",
            ),
        ],
        request=None,
        responses={
            205: OpenApiResponse(description="Successfully logged out"),
            400: OpenApiResponse(description="Bad request - missing refresh token"),
            401: OpenApiResponse(
                description="Unauthorized - invalid or missing access token"
            ),
        },
        examples=[
            OpenApiExample(
                "Logout Request",
                summary="Example logout request",
                description="Headers required for logout",
                value={
                    "headers": {
                        "Authorization": "Bearer your_access_token_here",
                        "refresh": "your_refresh_token_here",
                    }
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        refresh_token = request.headers.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            # Blacklist this refresh token
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid or already blacklisted token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class LogoutAllView(APIView):
    """Blacklist all outstanding refresh tokens for the authenticated user (logout all devices)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentication"],
        summary="Logout from all devices",
        description="Logout the current user from all devices by blacklisting all their outstanding refresh tokens. Requires Authentication header with Bearer token.",
        parameters=[
            OpenApiParameter(
                name="Authorization",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Bearer token for authentication (e.g., "Bearer your_access_token")',
            ),
        ],
        request=None,
        responses={
            205: OpenApiResponse(
                description="Successfully logged out from all devices"
            ),
            401: OpenApiResponse(
                description="Unauthorized - invalid or missing access token"
            ),
        },
        examples=[
            OpenApiExample(
                "Logout All Request",
                summary="Example logout all devices request",
                description="Header required for logout from all devices",
                value={"headers": {"Authorization": "Bearer your_access_token_here"}},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        user = request.user
        # OutstandingToken has a FK to user when token_blacklist app is enabled
        tokens = OutstandingToken.objects.filter(user=user)
        for t in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=t)
            except Exception:
                # Continue blacklisting the rest even if one fails
                continue
        return Response(status=status.HTTP_205_RESET_CONTENT)


@permission_classes([IsAuthenticated])
class TokenRenewView(APIView):
    """
    Create new JWT tokens without login credentials.
    Requires ONLY a valid refresh token.
    """

    @extend_schema(
        tags=["Authentication"],
        summary="Renew tokens using only refresh token",
        description="Provide a refresh token to get new access/refresh tokens plus account info.",
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string", "description": "Refresh token"},
            },
            "required": ["refresh"],
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                    "account": {"type": "object"},
                },
            },
            401: {"description": "Invalid or expired refresh token"},
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token_str = request.headers.get("refresh")
        new_profile_id = request.data.get("profile_id")
        if not refresh_token_str:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate the provided raw JWT refresh token by decoding it (do not
        # instantiate a RefreshToken object from it — we want to avoid using the
        # old refresh to construct the new tokens).
        try:
            payload = jwt.decode(refresh_token_str, settings.SECRET_KEY, algorithms=["HS256"])
        except Exception as e:
            return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Determine user id from claims (support account_id or standard user_id/sub)
        user_id = payload.get("account_id") or payload.get("user_id") or payload.get("sub")
        if not user_id:
            return Response({"detail": "Refresh token missing user information."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = Account.objects.get(pk=user_id)
        except Account.DoesNotExist:
            return Response({"detail": "User not found for provided refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Create new tokens (independent of the old refresh)
        new_refresh = RefreshToken.for_user(user)
        new_access = new_refresh.access_token

        # Optional: blacklist old refresh token if it exists in OutstandingToken
        try:
            old_outstanding = OutstandingToken.objects.filter(token=refresh_token_str).first()
            if old_outstanding:
                BlacklistedToken.objects.get_or_create(token=old_outstanding)
        except Exception:
            # Not critical; continue even if blacklisting fails
            pass

        # Limit outstanding tokens to 5 per user
        tokens = OutstandingToken.objects.filter(user=user)
        if tokens.count() > 5:
            oldest_token = tokens.order_by("created_at").first()
            try:
                BlacklistedToken.objects.get_or_create(token=oldest_token)
            except Exception:
                pass

        # Build account payload (same format as login)
        account = Account.objects.filter(pk=user.pk).first()
        account_payload = {
            "id": account.pk,
            "username": user.username,
            "email": user.email,
            "current_profile": (
                new_profile_id
                if new_profile_id
                else (account.default_profile.id if account and account.default_profile else None)
            ),
            "profiles": (
                list(
                    zip(
                        account.profiles.values_list("profile_type", flat=True),
                        account.profiles.values_list("id", flat=True),
                    )
                )
                if account
                else []
            ),
        }
        new_refresh["account_id"] = user.pk
        new_refresh["current_profile"] = (
            new_profile_id
            if new_profile_id
            else (account.default_profile.id if account and account.default_profile else None)
        )
        new_access["current_profile"] = (
            new_profile_id
            if new_profile_id
            else (account.default_profile.id if account and account.default_profile else None)
        )
        new_access["account_id"] = user.pk
        new_access["profiles"] = account_payload["profiles"]
        return Response(
            {
                "access": str(new_access),
                "refresh": str(new_refresh),
                "account": account_payload,
            },
            status=status.HTTP_200_OK,
        )
