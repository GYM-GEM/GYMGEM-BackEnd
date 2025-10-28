from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .serializers import MyTokenObtainPairSerializer, MyTokenRefreshSerializer
from accounts.models import Account
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

class MyTokenRefreshView(TokenRefreshView):
    """Custom TokenRefreshView to use MyTokenRefreshSerializer."""
    serializer_class = MyTokenRefreshSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.headers)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


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

        user = request.user
        current_tokens = OutstandingToken.objects.filter(user=user)
        if current_tokens.count() > 5:
            # Blacklist oldest tokens beyond the 5 most recent
            tokens_to_blacklist = current_tokens.order_by('created_at')[0]
            try:
                BlacklistedToken.objects.get_or_create(token=tokens_to_blacklist)
            except Exception:
                return Response({'detail': 'Error blacklisting old tokens'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        return Response({
            'access': tokens.get('access'),
            'refresh': tokens.get('refresh'),
            'account': account_payload,
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):

    def post(self, request):
        refresh_token = request.headers.get('refresh')
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
