from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import AccountSerializer
from django.http import JsonResponse
from .models import Account
from django.contrib.auth.hashers import make_password


class AccountsView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=AccountSerializer,
        responses={201: AccountSerializer, 400: "Bad Request"},
    )
    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save(
                password=make_password(request.data.get("password"))
            )
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

    @swagger_auto_schema(responses={200: AccountSerializer(many=True)})
    def get(self, request, account_id=None):
        if account_id:
            try:
                account = Account.objects.get(id=account_id)
                serializer = AccountSerializer(account)
                return JsonResponse(serializer.data, safe=False)
            except Account.DoesNotExist:
                return JsonResponse({"error": "Account not found"}, status=404)
        else:
            accounts = Account.objects.all()
            serializer = AccountSerializer(accounts, many=True)
            return JsonResponse(serializer.data, safe=False)
