from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .serializers import MyTokenObtainPairSerializer
from accounts.models import Account
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

@permission_classes([AllowAny])
class AccountLoginView(TokenObtainPairView):
    """Login endpoint that returns JWT tokens plus basic account info."""
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Tokens from SimpleJWT
        tokens = serializer.validated_data

        # Resolve account and enrich response
        user = serializer.user
        account = Account.objects.filter(pk=user.pk).first()
        account_payload = {
            'id': account.pk if account else None,
            'username': user.username,
            'email': user.email,
            'profile_types': list(account.profiles.values_list('profile_type', flat=True)) if account else [],
        }

        return Response({
            'access': tokens.get('access'),
            'refresh': tokens.get('refresh'),
            'account': account_payload,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Blacklist the provided refresh token (logout current device)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            # Blacklist this refresh token
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid or already blacklisted token'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class LogoutAllView(APIView):
    """Blacklist all outstanding refresh tokens for the authenticated user (logout all devices)."""
    permission_classes = [IsAuthenticated]

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
