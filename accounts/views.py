from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from accounts.models import Account
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
# Create your views here.


@permission_classes([AllowAny])
class AccountsView(APIView):
    def post(self, request):
        # Create a new account
        if request.data.get("password") == request.data.get("confirm_password"):
            password = make_password(request.data.get("password"))
        else:
            return JsonResponse({"error": "Passwords do not match"}, status=400)
        
        account = Account.objects.create(
            username=request.data.get("username"),
            email=request.data.get("email"),
            password=password,
            first_name=request.data.get("first_name", ""),
            last_name=request.data.get("last_name", ""),
            status=request.data.get("status", ""),
        )
        return JsonResponse({"id": account.id}, status=201)
    
    def get(self, request, account_id=None):
        # Retrieve account(s)
        if account_id:
            try:
                account = Account.objects.get(id=account_id)
                data = {
                    "id": account.id,
                    "username": account.username,
                    "email": account.email,
                    "first_name": account.first_name,
                    "last_name": account.last_name,
                    "status": account.status,
                    "last_seen": account.last_seen,
                    "default_profile": account.default_profile,
                    "created_at": account.created_at,
                    "updated_at": account.updated_at,
                }
                return JsonResponse(data)
            except Account.DoesNotExist:
                return JsonResponse({"error": "Account not found"}, status=404)
        else:
            accounts = Account.objects.all()
            data = [
                {
                    "id": account.id,
                    "username": account.username,
                    "email": account.email,
                    "first_name": account.first_name,
                    "last_name": account.last_name,
                    "status": account.status,
                }
                for account in accounts
            ]
            return JsonResponse(data, safe=False)
        

    def put(self, request, account_id):
        # Update an existing account
        try:
            account = Account.objects.get(id=account_id)
            account.username = request.data.get("username", account.username)
            account.email = request.data.get("email", account.email)
            account.first_name = request.data.get("first_name", account.first_name)
            account.last_name = request.data.get("last_name", account.last_name)
            account.status = request.data.get("status", account.status)
            account.save()
            return JsonResponse({"message": "Account updated successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
        
    def patch(self, request, account_id):
        # Partially update an existing account
        try:
            account = Account.objects.get(id=account_id)
            if "username" in request.data:
                account.username = request.data["username"]
            if "email" in request.data:
                account.email = request.data["email"]
            if "first_name" in request.data:
                account.first_name = request.data["first_name"]
            if "last_name" in request.data:
                account.last_name = request.data["last_name"]
            if "status" in request.data:
                account.status = request.data["status"]
            account.save()
            return JsonResponse({"message": "Account partially updated successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
    
    
    def delete(self, request, account_id):
        # Delete an existing account
        try:
            account = Account.objects.get(id=account_id)
            account.delete()
            return JsonResponse({"message": "Account deleted successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
