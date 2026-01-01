"""
Utility views and services.
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from accounts.models import Account
from authenticationAndAuthorization.permissions import HasRole
from .models import Category, Complaints, Specialization
from .serializers import CategorySerializer, SpecializationSerializer


logger = logging.getLogger('gymgem')

# Paymob API base URL
BASE_URL = "https://accept.paymob.com/api"


def get_account_from_token(request: HttpRequest) -> Account:
    """
    Extract and return Account from JWT token in request.
    
    Raises:
        ValidationError: If token is invalid or account not found.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise serializers.ValidationError("Authorization header is missing or invalid.")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise serializers.ValidationError("Token has expired.")
    except jwt.InvalidTokenError:
        raise serializers.ValidationError("Invalid token.")
    except Exception as e:
        logger.warning("Token decode error: %s", str(e))
        raise serializers.ValidationError(f"Token decode error: {str(e)}")

    account_id = payload.get("user_id")
    if not account_id:
        raise serializers.ValidationError("Account ID not found in token.")

    try:
        return Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        raise serializers.ValidationError("Account does not exist.")


def get_profile_id_from_token(request: HttpRequest) -> Optional[int]:
    """
    Extract profile_id from the access token in the request.
    
    Returns:
        The profile ID or None if not found.
    """
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("current_profile")
    except Exception as e:
        logger.warning("Token decode error in get_profile_id_from_token: %s", str(e))
        return None


def send_verification_email(account: Account, request: HttpRequest) -> None:
    """
    Send email verification link to the account's email address.
    """
    token_payload = {
        "user_id": account.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    verification_link = request.build_absolute_uri(
        reverse("accounts-verify") + f"?token={token}"
    )
    
    logger.info(
        "Sending verification email to %s for account %s",
        account.email,
        account.id
    )
    
    subject = "Verify your email address"
    message = (
        f"Hi {account.first_name},\n\n"
        f"Please verify your email by clicking the link below:\n"
        f"{verification_link}\n\n"
        f"Thank you!"
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [account.email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info("Verification email sent successfully to %s", account.email)
    except Exception as e:
        logger.error("Failed to send verification email: %s", str(e))
        raise


@extend_schema(
    tags=["Utils"],
    summary="List categories",
    description="Return a list of all categories (cached)",
    responses={200: CategorySerializer(many=True)},
)
class CategoryListView(generics.ListAPIView):
    """Return a list of all categories with caching."""

    serializer_class = CategorySerializer
    permission_classes = []
    
    def get_queryset(self):
        cache_key = 'categories_list'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        queryset = Category.objects.all()
        cache.set(cache_key, list(queryset), settings.CACHE_TTL.get('categories', 3600))
        return queryset


@extend_schema(
    tags=["Utils"],
    summary="List specializations",
    description="Return a list of all specializations (cached)",
    responses={200: SpecializationSerializer(many=True)},
)
class SpecializationListView(generics.ListAPIView):
    """Return a list of all specializations with caching."""

    serializer_class = SpecializationSerializer
    permission_classes = []
    
    def get_queryset(self):
        cache_key = 'specializations_list'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        queryset = Specialization.objects.all()
        cache.set(cache_key, list(queryset), settings.CACHE_TTL.get('specializations', 3600))
        return queryset


@extend_schema(
    tags=["Complaints"],
    summary="Send a complaint",
    description="Send a complaint about a target entity.",
    request={
        "application/json": {
            "target_complaint": 1,
            "details": "Details about the complaint."
        }
    },
    responses={
        201: OpenApiResponse(description="Complaint sent successfully.")
    }
)
class SendComplaint(APIView):
    """Submit a new complaint."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        target = request.data.get("target_complaint")
        details = request.data.get("details", "")
        profile_id = get_profile_id_from_token(request)
        
        complaint = Complaints.objects.create(
            profile_id=profile_id,
            target_complaint_id=target,
            details=details
        )
        
        logger.info(
            "Complaint created: id=%s, profile=%s, target=%s",
            complaint.id,
            profile_id,
            target
        )
        
        return Response({"message": "Complaint sent successfully."}, status=201)


@extend_schema(
    tags=["Complaints"],
    summary="List complaints for current profile",
    description="Return a list of all complaints submitted by the current profile.",
    responses={
        200: OpenApiResponse(description="List of complaints.")
    }
)
class ComplaintStatusView(APIView):
    """List complaints for the current user."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        profile_id = get_profile_id_from_token(request)
        complaints = Complaints.objects.filter(profile_id=profile_id)
        data = [
            {
                "id": c.id,
                "target_complaint": c.target_complaint.id if c.target_complaint else None,
                "details": c.details,
                "created_at": c.created_at,
                "status": c.status
            }
            for c in complaints
        ]
        return Response({"complaints": data})


@extend_schema(
    tags=["Complaints"],
    summary="Retrieve complaint details",
    description="Get details of a specific complaint by ID.",
    parameters=[
        OpenApiParameter(
            "complaint_id",
            int,
            OpenApiParameter.PATH,
            description="ID of the complaint"
        )
    ],
    responses={
        200: OpenApiResponse(description="Complaint details."),
        404: OpenApiResponse(description="Complaint not found.")
    }
)
class ComplaintDetailView(APIView):
    """Get details of a specific complaint."""
    
    permission_classes = [IsAuthenticated]
    
    def get(
        self,
        request: HttpRequest,
        complaint_id: int,
        *args: Any,
        **kwargs: Any
    ) -> Response:
        profile_id = get_profile_id_from_token(request)
        try:
            complaint = Complaints.objects.get(id=complaint_id, profile_id=profile_id)
            data = {
                "id": complaint.id,
                "target_complaint": (
                    complaint.target_complaint.id if complaint.target_complaint else None
                ),
                "details": complaint.details,
                "created_at": complaint.created_at,
                "status": complaint.status
            }
            return Response({"complaint": data})
        except Complaints.DoesNotExist:
            return Response({"error": "Complaint not found."}, status=404)


@extend_schema(
    tags=["Complaints"],
    summary="Update complaint status (admin only)",
    description="Update the status of a complaint.",
    parameters=[
        OpenApiParameter(
            "complaint_id",
            int,
            OpenApiParameter.PATH,
            description="ID of the complaint"
        )
    ],
    request={
        "application/json": {"status": "resolved"}
    },
    responses={
        200: OpenApiResponse(description="Complaint updated successfully."),
        404: OpenApiResponse(description="Complaint not found.")
    }
)
class ComplaintUpdateView(APIView):
    """Update complaint status (admin only)."""
    
    permission_classes = [HasRole(["admin"])]
    
    def put(
        self,
        request: HttpRequest,
        complaint_id: int,
        *args: Any,
        **kwargs: Any
    ) -> Response:
        new_status = request.data.get("status", "")
        try:
            complaint = Complaints.objects.get(id=complaint_id)
            if new_status:
                complaint.status = new_status
            complaint.save()
            
            logger.info(
                "Complaint %s status updated to '%s'",
                complaint_id,
                new_status
            )
            
            return Response({"message": "Complaint updated successfully."})
        except Complaints.DoesNotExist:
            return Response({"error": "Complaint not found."}, status=404)


class CompaintAdminListView(APIView):
    """List all complaints (admin only)."""
    
    permission_classes = [HasRole(["admin"])]
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        complaints = Complaints.objects.all()
        data = [
            {
                "id": c.id,
                "profile": c.profile.id if c.profile else None,
                "target_complaint": c.target_complaint.id if c.target_complaint else None,
                "details": c.details,
                "created_at": c.created_at,
                "status": c.status
            }
            for c in complaints
        ]
        return Response({"complaints": data})


class PaymobService:
    """Service for interacting with Paymob payment gateway."""
    
    DEFAULT_TIMEOUT: int = 25
    MAX_RETRIES: int = 3
    BACKOFF_SECONDS: int = 1

    @staticmethod
    def authenticate() -> str:
        """Authenticate with Paymob and return auth token."""
        for attempt in range(PaymobService.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{BASE_URL}/auth/tokens",
                    json={"api_key": settings.PAYMOB_API_KEY},
                    timeout=PaymobService.DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                logger.debug("Paymob authentication successful")
                return response.json()["token"]
            except requests.RequestException as e:
                if attempt < PaymobService.MAX_RETRIES - 1:
                    logger.warning(
                        "Paymob auth attempt %d failed: %s",
                        attempt + 1,
                        str(e)
                    )
                    time.sleep(PaymobService.BACKOFF_SECONDS)
                    continue
                logger.error("Paymob auth failed after %d attempts", PaymobService.MAX_RETRIES)
                raise RuntimeError(f"Paymob auth failed: {e}")

    @staticmethod
    def create_order(auth_token: str, amount_cents: int) -> Dict[str, Any]:
        """Create a Paymob order."""
        payload = {
            "auth_token": auth_token,
            "delivery_needed": "false",
            "amount_cents": amount_cents,
            "currency": "EGP",
            "items": []
        }
        for attempt in range(PaymobService.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{BASE_URL}/ecommerce/orders",
                    json=payload,
                    timeout=PaymobService.DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                order = response.json()
                logger.info("Paymob order created: id=%s", order.get("id"))
                return order
            except requests.RequestException as e:
                if attempt < PaymobService.MAX_RETRIES - 1:
                    logger.warning(
                        "Paymob order creation attempt %d failed: %s",
                        attempt + 1,
                        str(e)
                    )
                    time.sleep(PaymobService.BACKOFF_SECONDS)
                    continue
                logger.error(
                    "Paymob order creation failed after %d attempts",
                    PaymobService.MAX_RETRIES
                )
                raise RuntimeError(f"Paymob order creation failed: {e}")

    @staticmethod
    def create_payment_key(
        auth_token: str,
        order_id: int,
        amount_cents: int,
        billing_data: Dict[str, Any]
    ) -> str:
        """Create a Paymob payment key for iframe."""
        payload = {
            "auth_token": auth_token,
            "amount_cents": amount_cents,
            "expiration": 3600,
            "order_id": order_id,
            "billing_data": billing_data,
            "currency": "EGP",
            "integration_id": settings.PAYMOB_CARD_INTEGRATION_ID
        }
        for attempt in range(PaymobService.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{BASE_URL}/acceptance/payment_keys",
                    json=payload,
                    timeout=PaymobService.DEFAULT_TIMEOUT,
                )
                response.raise_for_status()
                logger.debug("Paymob payment key created for order %s", order_id)
                return response.json()["token"]
            except requests.RequestException as e:
                if attempt < PaymobService.MAX_RETRIES - 1:
                    logger.warning(
                        "Paymob payment key attempt %d failed: %s",
                        attempt + 1,
                        str(e)
                    )
                    time.sleep(PaymobService.BACKOFF_SECONDS)
                    continue
                logger.error(
                    "Paymob payment key failed after %d attempts",
                    PaymobService.MAX_RETRIES
                )
                raise RuntimeError(f"Paymob payment key failed: {e}")

    @staticmethod
    def refund_transaction(
        auth_token: str,
        transaction_id: int,
        amount_cents: int
    ) -> Dict[str, Any]:
        """Attempt to refund a transaction via Paymob."""
        try:
            response = requests.post(
                f"{BASE_URL}/acceptance/void_refund/refund",
                json={
                    "auth_token": auth_token,
                    "transaction_id": transaction_id,
                    "amount_cents": amount_cents,
                },
                timeout=10,
            )
            response.raise_for_status()
            logger.info(
                "Paymob refund successful: txn=%s, amount=%s",
                transaction_id,
                amount_cents
            )
            return response.json()
        except requests.RequestException as e:
            logger.error("Paymob refund failed: %s", str(e))
            raise RuntimeError(f"Paymob refund failed: {e}")
