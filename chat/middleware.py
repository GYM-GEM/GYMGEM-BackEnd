"""
WebSocket Authentication Middleware for JWT tokens.

This middleware extracts JWT tokens from WebSocket connection query parameters
and authenticates the user before the WebSocket connection is established.
"""

from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Validates JWT token and returns the associated user.
    
    Args:
        token_string: JWT access token as string
        
    Returns:
        User instance if token is valid, AnonymousUser otherwise
    """
    try:
        # Validate the token
        UntypedToken(token_string)
        
        # Decode token to get user_id
        from rest_framework_simplejwt.tokens import AccessToken
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        
        # Get user from database
        user = User.objects.get(id=user_id)
        return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Expects token in query string: ws://domain/path/?token=<jwt_token>
    Sets scope['user'] to authenticated user or AnonymousUser.
    """
    
    async def __call__(self, scope, receive, send):
        # Parse query string to get token
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        # Authenticate user with token
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
