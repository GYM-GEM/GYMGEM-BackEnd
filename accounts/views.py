from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from accounts.models import Account
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from drf_spectacular.types import OpenApiTypes
# Create your views here.


@permission_classes([AllowAny])
class AccountsListView(APIView):
    """Handles operations on the accounts collection"""
    
    @extend_schema(
        tags=['Accounts'],
        operation_id='accounts_list',
        summary='List all accounts',
        description='Get all user accounts',
        responses={200: {'description': 'List of accounts'}}
    )
    def get(self, request):
        """List all accounts"""
        accounts = Account.objects.all()
        data = [
            {
                "id": account.id,
                "username": account.username,
                "email": account.email,
                "firstName": account.first_name,
                "lastName": account.last_name,
                "createdAt": account.created_at,
                "updatedAt": account.updated_at,
            }
            for account in accounts
        ]
        return JsonResponse(data, safe=False)
    
    @extend_schema(
        tags=['Accounts'],
        operation_id='accounts_create',
        summary='Create new account',
        description='Create a new user account with username, email and password',
        request={'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string'},
                'confirmPassword': {'type': 'string'},
                'firstName': {'type': 'string'},
                'lastName': {'type': 'string'},
            },
            'required': ['username', 'email', 'password', 'confirmPassword']
        }},
        responses={201: {'description': 'Account created'}, 400: {'description': 'Bad request'}}
    )
    def post(self, request):
        """Create a new account"""
        if request.data.get("password") != request.data.get("confirmPassword"):
            return JsonResponse({"error": "Passwords do not match"}, status=400)
        
        account = Account.objects.create(
            username=request.data.get("username"),
            email=request.data.get("email"),
            password=make_password(request.data.get("password")),
            first_name=request.data.get("firstName", ""),
            last_name=request.data.get("lastName", ""),
        )
        return JsonResponse({"id": account.id}, status=201)


@permission_classes([AllowAny])
class AccountsDetailView(APIView):
    """Handles operations on individual accounts"""
    
    @extend_schema(
        tags=['Accounts'],
        operation_id='accounts_retrieve',
        summary='Retrieve account by ID',
        description='Get details of a specific account',
        parameters=[
            OpenApiParameter(
                name='account_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Account ID'
            ),
        ],
        responses={200: {'description': 'Account data'}, 404: {'description': 'Account not found'}}
    )
    def get(self, request, account_id):
        """Retrieve a specific account"""
        try:
            account = Account.objects.get(id=account_id)
            data = {
                "id": account.id,
                "username": account.username,
                "email": account.email,
                "firstName": account.first_name,
                "lastName": account.last_name,
                "lastSeen": account.last_seen,
                "defaultProfile": {
                    "id": account.default_profile.id,
                    "profileType": account.default_profile.profile_type,
                } if account.default_profile else None,
                "createdAt": account.created_at,
                "updatedAt": account.updated_at,
            }
            return JsonResponse(data)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
        
    @extend_schema(
        tags=['Accounts'],
        operation_id='accounts_update',
        summary='Update account',
        description='Update an existing account with new data',
        parameters=[
            OpenApiParameter(
                name='account_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Account ID'
            ),
        ],
        request={'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'firstName': {'type': 'string'},
                'lastName': {'type': 'string'},
            }
        }},
        responses={200: {'description': 'Account updated'}, 404: {'description': 'Account not found'}}
    )
    def put(self, request, account_id):
        """Update an account"""
        try:
            account = Account.objects.get(id=account_id)
            account.username = request.data.get("username", account.username)
            account.email = request.data.get("email", account.email)
            account.first_name = request.data.get("firstName", account.first_name)
            account.last_name = request.data.get("lastName", account.last_name)
            account.save()
            return JsonResponse({"message": "Account updated successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
        
    @extend_schema(
        tags=['Accounts'],
        operation_id='accounts_partial_update',
        summary='Partially update account',
        description='Partially update an existing account',
        parameters=[
            OpenApiParameter(
                name='account_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Account ID'
            ),
        ],
        request={'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'firstName': {'type': 'string'},
                'lastName': {'type': 'string'},
            }
        }},
        responses={200: {'description': 'Account updated'}, 404: {'description': 'Account not found'}}
    )
    def patch(self, request, account_id):
        """Partially update an account"""
        try:
            account = Account.objects.get(id=account_id)
            if "username" in request.data:
                account.username = request.data["username"]
            if "email" in request.data:
                account.email = request.data["email"]
            if "firstName" in request.data:
                account.first_name = request.data["firstName"]
            if "lastName" in request.data:
                account.last_name = request.data["lastName"]
            account.save()
            return JsonResponse({"message": "Account partially updated successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
    
    @extend_schema(
        tags=['Accounts'],
        operation_id='accounts_delete',
        summary='Delete account',
        description='Delete an existing account',
        parameters=[
            OpenApiParameter(
                name='account_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Account ID'
            ),
        ],
        responses={200: {'description': 'Account deleted'}, 404: {'description': 'Account not found'}}
    )
    def delete(self, request, account_id):
        """Delete an account"""
        try:
            account = Account.objects.get(id=account_id)
            account.delete()
            return JsonResponse({"message": "Account deleted successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)

