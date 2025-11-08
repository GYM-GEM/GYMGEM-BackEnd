from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .serializers import MyTokenObtainPairSerializer, MyTokenRefreshSerializer
from accounts.models import Account
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample, OpenApiTypes


class MyTokenRefreshView(TokenRefreshView):
    """Custom TokenRefreshView to use MyTokenRefreshSerializer."""
    serializer_class = MyTokenRefreshSerializer

    @extend_schema(
        tags=['Authentication'],
        summary='Refresh JWT token',
        description='Refresh access token using refresh token from headers',
        request=MyTokenRefreshSerializer,
        responses={200: MyTokenRefreshSerializer}
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
        tags=['Authentication'],
        summary='Login with credentials',
        description='Login with username/email and password. Returns JWT tokens and account information.',
        request=MyTokenObtainPairSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string', 'description': 'Access token'},
                    'refresh': {'type': 'string', 'description': 'Refresh token'},
                    'account': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'profile_types': {'type': 'array', 'items': {'type': 'string'}}
                        }
                    }
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Invalid credentials'}
        }
    )
    def post(self, request, *args, **kwargs):
        # Support login via email or username: if email is provided and username is not,
        # resolve the username from the Account with that email.
        data = request.data.copy()
        if not data.get('username') and data.get('email'):
            email = data.get('email')
            qs = Account.objects.filter(email__iexact=email)
            if not qs.exists():
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
            if qs.count() > 1:
                return Response({'detail': 'Multiple accounts use this email. Please login with username.'}, status=status.HTTP_400_BAD_REQUEST)
            data['username'] = qs.first().username

        serializer = self.get_serializer(data=data)
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

        if request.user.is_authenticated:
            current_tokens = OutstandingToken.objects.filter(user=request.user)
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
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Authentication'],
        summary='Logout user',
        description='Logout the current user by blacklisting their refresh token. Requires Authentication header with Bearer token and refresh token in custom header.',
        parameters=[
            OpenApiParameter(
                name='Authorization',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Bearer token for authentication (e.g., "Bearer your_access_token")'
            ),
            OpenApiParameter(
                name='refresh',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Refresh token to be blacklisted'
            ),
        ],
        request=None,
        responses={
            205: OpenApiResponse(description='Successfully logged out'),
            400: OpenApiResponse(description='Bad request - missing refresh token'),
            401: OpenApiResponse(description='Unauthorized - invalid or missing access token'),
        },
        examples=[
            OpenApiExample(
                'Logout Request',
                summary='Example logout request',
                description='Headers required for logout',
                value={
                    'headers': {
                        'Authorization': 'Bearer your_access_token_here',
                        'refresh': 'your_refresh_token_here'
                    }
                },
                request_only=True,
            ),
        ]
    )
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
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Authentication'],
        summary='Logout from all devices',
        description='Logout the current user from all devices by blacklisting all their outstanding refresh tokens. Requires Authentication header with Bearer token.',
        parameters=[
            OpenApiParameter(
                name='Authorization',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Bearer token for authentication (e.g., "Bearer your_access_token")'
            ),
        ],
        request=None,
        responses={
            205: OpenApiResponse(description='Successfully logged out from all devices'),
            401: OpenApiResponse(description='Unauthorized - invalid or missing access token'),
        },
        examples=[
            OpenApiExample(
                'Logout All Request',
                summary='Example logout all devices request',
                description='Header required for logout from all devices',
                value={
                    'headers': {
                        'Authorization': 'Bearer your_access_token_here'
                    }
                },
                request_only=True,
            ),
        ]
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
