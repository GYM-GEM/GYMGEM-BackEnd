"""
Utility Views and Services Module.

This module provides utility functions, views, and services for the GYMGEM application:

- Token-based authentication utilities for extracting account and profile information
- Email verification functionality
- Category and Specialization list views with caching
- Complaint management system (create, view, update complaints)
- Paymob payment gateway integration service

Classes:
    CategoryListView: API view for listing all categories with caching
    SpecializationListView: API view for listing all specializations with caching
    SendComplaint: API view for submitting new complaints
    ComplaintStatusView: API view for viewing user's complaints
    ComplaintUpdateView: API view for admin to update complaint status
    CompaintAdminListView: API view for admin to list all complaints
    PaymobService: Service class for Paymob payment gateway operations

Functions:
    get_account_from_token: Extract Account object from JWT token
    get_profile_id_from_token: Extract profile ID from JWT token
    send_verification_email: Send email verification link to user
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
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from accounts.models import Account
from authenticationAndAuthorization.permissions import HasRole
from .models import Category, Complaints, Specialization
from .serializers import CategorySerializer, SpecializationSerializer


logger = logging.getLogger('gymgem')

# Paymob API base URL
BASE_URL = "https://accept.paymob.com/api"


def get_account_from_token(request: HttpRequest) -> Account:
    """
    Extract and return Account instance from JWT token in request Authorization header.
    
    This function validates the JWT token from the Authorization header, decodes it,
    and retrieves the corresponding Account object from the database.
    
    Args:
        request (HttpRequest): The HTTP request object containing Authorization header
                               with Bearer token.
    
    Returns:
        Account: The Account instance associated with the token's user_id.
    
    Raises:
        ValidationError: If Authorization header is missing or invalid.
        ValidationError: If token has expired.
        ValidationError: If token is invalid or cannot be decoded.
        ValidationError: If account ID is not found in token payload.
        ValidationError: If account does not exist in database.
    
    Example:
        >>> account = get_account_from_token(request)
        >>> print(account.email)
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
    Extract profile_id from the JWT access token in the request Authorization header.
    
    This function attempts to decode the JWT token and extract the 'current_profile'
    field. It gracefully handles missing or invalid tokens by returning None.
    
    Args:
        request (HttpRequest): The HTTP request object containing Authorization header
                               with Bearer token.
    
    Returns:
        Optional[int]: The profile ID if found in token payload, None otherwise.
                      Returns None if token is missing, invalid, or doesn't contain
                      'current_profile' field.
    
    Example:
        >>> profile_id = get_profile_id_from_token(request)
        >>> if profile_id:
        ...     print(f"Current profile: {profile_id}")
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
    Generate and send email verification link to the account's email address.
    
    Creates a JWT token valid for 15 minutes containing the account ID, builds
    an absolute verification URL, and sends it via email to the user.
    
    Args:
        account (Account): The Account instance to send verification email to.
        request (HttpRequest): The HTTP request object used to build absolute URI.
    
    Returns:
        None
    
    Raises:
        Exception: If email sending fails (logged and re-raised).
    
    Note:
        - Verification token expires after 15 minutes
        - Uses DEFAULT_FROM_EMAIL from settings
        - Logs both successful sends and failures
    
    Example:
        >>> send_verification_email(new_account, request)
    """
    token_payload = {
        "user_id": account.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    # Use frontend URL for verification link
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    verification_link = f"{frontend_url}/verify?token={token}"
    
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

def send_password_reset_email(account: Account, request: HttpRequest) -> None:
    """
    Generate and send password reset link to the account's email address.
    
    Creates a JWT token valid for 15 minutes containing the account ID, builds
    an absolute password reset URL, and sends it via email to the user.
    
    Args:
        account (Account): The Account instance to send password reset email to.
        request (HttpRequest): The HTTP request object used to build absolute URI.
    
    Returns:
        None
    
    Raises:
        Exception: If email sending fails (logged and re-raised).
    
    Note:
        - Password reset token expires after 15 minutes
        - Uses DEFAULT_FROM_EMAIL from settings
        - Logs both successful sends and failures
    
    Example:
        >>> send_password_reset_email(user_account, request)
    """
    token_payload = {
        "user_id": account.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    # Use frontend URL for password reset link
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:4040')
    reset_link = f"{frontend_url}/reset-password?token={token}"
    
    logger.info(
        "Sending password reset email to %s for account %s",
        account.email,
        account.id
    )
    
    subject = "Reset your password"
    message = (
        f"Hi {account.first_name},\n\n"
        f"You can reset your password by clicking the link below:\n"
        f"{reset_link}\n\n"
        f"If you did not request a password reset, please ignore this email."
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [account.email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info("Password reset email sent successfully to %s", account.email)
    except Exception as e:
        logger.error("Failed to send password reset email: %s", str(e))
        raise

@extend_schema(
    tags=["Utils"],
    summary="List all categories",
    description="""
    Retrieve a comprehensive list of all available categories in the system.
    
    This endpoint returns cached data to optimize performance. Categories are used 
    for classifying various entities throughout the application (trainers, courses, etc.).
    
    **Caching:** Results are cached for 1 hour to reduce database load.
    
    **Authentication:** Not required - publicly accessible endpoint.
    """,
    responses={
        200: OpenApiResponse(
            response=CategorySerializer(many=True),
            description="Successfully retrieved list of categories",
            examples=[
                OpenApiExample(
                    "Categories List",
                    value=[
                        {"id": 1, "name": "Fitness"},
                        {"id": 2, "name": "Yoga"},
                        {"id": 3, "name": "Nutrition"}
                    ],
                    response_only=True
                )
            ]
        ),
        500: OpenApiResponse(description="Internal server error")
    },
)
class CategoryListView(generics.ListAPIView):
    """
    API view to retrieve a list of all categories with Redis caching.
    
    This view provides a read-only endpoint that returns all Category objects.
    Results are cached in Redis to improve performance and reduce database queries.
    Cache is stored with key 'categories_list' and respects CACHE_TTL settings.
    
    Attributes:
        serializer_class: CategorySerializer for response serialization.
        permission_classes: Empty list, allows unauthenticated access.
    
    Cache:
        Key: 'categories_list'
        TTL: settings.CACHE_TTL.get('categories', 3600) seconds (default: 1 hour)
    
    HTTP Methods:
        GET: Returns list of all categories
    
    Response:
        200: List of category objects with id, name, and other fields
    """

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
    summary="List all specializations",
    description="""
    Retrieve a comprehensive list of all available specializations in the system.
    
    Specializations are used to categorize trainer expertise and course focus areas.
    Common examples include Weight Training, Cardio, CrossFit, Pilates, etc.
    
    **Caching:** Results are cached for 1 hour to reduce database load.
    
    **Authentication:** Not required - publicly accessible endpoint.
    """,
    responses={
        200: OpenApiResponse(
            response=SpecializationSerializer(many=True),
            description="Successfully retrieved list of specializations",
            examples=[
                OpenApiExample(
                    "Specializations List",
                    value=[
                        {"id": 1, "name": "Weight Training"},
                        {"id": 2, "name": "Cardio"},
                        {"id": 3, "name": "CrossFit"}
                    ],
                    response_only=True
                )
            ]
        ),
        500: OpenApiResponse(description="Internal server error")
    },
)
class SpecializationListView(generics.ListAPIView):
    """
    API view to retrieve a list of all specializations with Redis caching.
    
    This view provides a read-only endpoint that returns all Specialization objects.
    Results are cached in Redis to improve performance and reduce database queries.
    Cache is stored with key 'specializations_list' and respects CACHE_TTL settings.
    
    Attributes:
        serializer_class: SpecializationSerializer for response serialization.
        permission_classes: Empty list, allows unauthenticated access.
    
    Cache:
        Key: 'specializations_list'
        TTL: settings.CACHE_TTL.get('specializations', 3600) seconds (default: 1 hour)
    
    HTTP Methods:
        GET: Returns list of all specializations
    
    Response:
        200: List of specialization objects with id, name, and other fields
    """

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
    summary="Submit a new complaint",
    description="""
    Submit a complaint against a target entity (trainer, gym, course, etc.).
    
    The complaint will be associated with the authenticated user's current profile 
    and can be tracked through the complaint status endpoint.
    
    **Authentication:** Required - user must be logged in with valid JWT token.
    
    **Target Entity:** Can be any profile ID in the system (trainer, gym owner, etc.).
    """,
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "target_complaint": {
                    "type": "integer",
                    "description": "ID of the profile/entity being complained about",
                    "example": 123
                },
                "details": {
                    "type": "string",
                    "description": "Detailed description of the complaint",
                    "example": "The trainer was late to multiple sessions and unprofessional."
                }
            },
            "required": ["target_complaint"]
        }
    },
    responses={
        201: OpenApiResponse(
            description="Complaint submitted successfully",
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={"message": "Complaint sent successfully."},
                    response_only=True
                )
            ]
        ),
        400: OpenApiResponse(description="Invalid request data"),
        401: OpenApiResponse(description="Authentication credentials were not provided or invalid"),
        404: OpenApiResponse(description="Target entity not found"),
        500: OpenApiResponse(description="Internal server error")
    }
)
class SendComplaint(APIView):
    """
    API view for authenticated users to submit new complaints.
    
    Allows users to create complaints against specific target entities (profiles, gyms, etc.).
    The complaint is associated with the current user's profile extracted from their JWT token.
    
    Attributes:
        permission_classes: Requires IsAuthenticated - user must be logged in.
    
    HTTP Methods:
        POST: Create a new complaint
    
    Request Body:
        target_complaint (int): ID of the entity being complained about
        details (str, optional): Description of the complaint
    
    Response:
        201: Complaint sent successfully
    
    Example Request:
        POST /api/complaints/send/
        {
            "target_complaint": 123,
            "details": "Inappropriate behavior during session"
        }
    """
    
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
    summary="View user's complaint history",
    description="""
    Retrieve all complaints submitted by the authenticated user's current profile.
    
    Returns comprehensive information including complaint status, admin responses,
    and timestamps for tracking complaint resolution progress.
    
    **Authentication:** Required - user must be logged in with valid JWT token.
    
    **Status Values:**
    - `pending`: Complaint received, awaiting review
    - `in_review`: Complaint is being investigated by admin
    - `resolved`: Complaint has been addressed and closed
    - `rejected`: Complaint was reviewed and rejected
    """,
    responses={
        200: OpenApiResponse(
            description="Successfully retrieved user's complaints",
            examples=[
                OpenApiExample(
                    "User Complaints List",
                    value={
                        "complaints": [
                            {
                                "id": 1,
                                "target_complaint": 123,
                                "details": "The trainer was unprofessional during sessions.",
                                "created_at": "2026-01-03T10:30:00Z",
                                "status": "in_review",
                                "admin_response": "We are investigating this matter.",
                                "response_at": "2026-01-04T09:15:00Z"
                            },
                            {
                                "id": 2,
                                "target_complaint": 456,
                                "details": "Gym equipment was broken.",
                                "created_at": "2026-01-02T14:20:00Z",
                                "status": "resolved",
                                "admin_response": "Equipment has been repaired.",
                                "response_at": "2026-01-03T11:00:00Z"
                            }
                        ]
                    },
                    response_only=True
                )
            ]
        ),
        401: OpenApiResponse(description="Authentication credentials were not provided or invalid"),
        500: OpenApiResponse(description="Internal server error")
    }
)
class ComplaintStatusView(APIView):
    """
    API view for authenticated users to view their submitted complaints.
    
    Returns all complaints submitted by the current user's profile, including
    status updates and admin responses.
    
    Attributes:
        permission_classes: Requires IsAuthenticated - user must be logged in.
    
    HTTP Methods:
        GET: Retrieve list of user's complaints
    
    Response:
        200: JSON object with 'complaints' array containing:
            - id: Complaint ID
            - target_complaint: Target entity ID
            - details: Complaint description
            - created_at: Submission timestamp
            - status: Current status (pending/in_review/resolved/rejected)
            - admin_response: Admin's response text (if any)
            - response_at: Response timestamp (if any)
    
    Example Response:
        {
            "complaints": [
                {
                    "id": 1,
                    "target_complaint": 123,
                    "details": "Issue description",
                    "created_at": "2026-01-04T10:00:00Z",
                    "status": "in_review",
                    "admin_response": null,
                    "response_at": null
                }
            ]
        }
    """
    
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
                "status": c.status,
                "admin_response": c.admin_response,
                "response_at": c.response_at
            }
            for c in complaints
        ]
        return Response({"complaints": data})


@extend_schema(
    tags=["Complaints"],
    summary="Update complaint status and add response (Admin)",
    description="""
    Update the status of a complaint and optionally add an admin response.
    
    This endpoint allows administrators to manage complaints by updating their status
    and providing feedback to users. When an admin_response is provided, the 
    response_at timestamp is automatically set.
    
    **Authentication:** Required - admin role only.
    
    **Permissions:** Only users with 'admin' role can access this endpoint.
    
    **Status Options:**
    - `pending`: Initial state
    - `in_review`: Under investigation
    - `resolved`: Complaint addressed
    - `rejected`: Complaint dismissed
    """,
    parameters=[
        OpenApiParameter(
            "complaint_id",
            int,
            OpenApiParameter.PATH,
            description="Unique identifier of the complaint to update",
            required=True
        )
    ],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_review", "resolved", "rejected"],
                    "description": "New status for the complaint",
                    "example": "resolved"
                },
                "admin_response": {
                    "type": "string",
                    "description": "Admin's response message to the complainant",
                    "example": "We have investigated and taken appropriate action."
                }
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description="Complaint updated successfully",
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={"message": "Complaint updated successfully."},
                    response_only=True
                )
            ]
        ),
        400: OpenApiResponse(description="Invalid request data"),
        401: OpenApiResponse(description="Authentication credentials were not provided"),
        403: OpenApiResponse(description="User does not have admin permissions"),
        404: OpenApiResponse(
            description="Complaint not found",
            examples=[
                OpenApiExample(
                    "Not Found Error",
                    value={"error": "Complaint not found."},
                    response_only=True
                )
            ]
        ),
        500: OpenApiResponse(description="Internal server error")
    }
)
class ComplaintUpdateView(APIView):
    """
    API view for administrators to update complaint status and add responses.
    
    Allows admins to change the status of complaints and provide responses to users.
    Restricted to users with 'admin' role.
    
    Attributes:
        permission_classes: Requires HasRole(['admin']) - admin access only.
    
    HTTP Methods:
        PUT: Update complaint status and/or add admin response
    
    URL Parameters:
        complaint_id (int): ID of the complaint to update
    
    Request Body:
        status (str, optional): New status value
        admin_response (str, optional): Admin's response message
    
    Response:
        200: Complaint updated successfully
        404: Complaint not found
    
    Note:
        When admin_response is provided, response_at is automatically set to current UTC time.
    
    Example Request:
        PUT /api/complaints/update/1/
        {
            "status": "resolved",
            "admin_response": "Issue has been addressed with the trainer."
        }
    """
    
    permission_classes = [HasRole(["admin"])]
    
    def put(
        self,
        request: HttpRequest,
        complaint_id: int,
        *args: Any,
        **kwargs: Any
    ) -> Response:
        new_status = request.data.get("status", "")
        response = request.data.get("admin_response", "")
        try:
            complaint = Complaints.objects.get(id=complaint_id)
            if new_status:
                complaint.status = new_status
            complaint.save()
            if response:
                complaint.admin_response = response
                complaint.response_at = datetime.now(timezone.utc)
                complaint.save()
            logger.info(
                "Complaint %s status updated to '%s'",
                complaint_id,
                new_status
            )
            
            return Response({"message": "Complaint updated successfully."})
        except Complaints.DoesNotExist:
            return Response({"error": "Complaint not found."}, status=404)


@extend_schema(
    tags=["Complaints"],
    summary="List all complaints (Admin)",
    description="""
    Retrieve a complete list of all complaints submitted in the system.
    
    This admin-only endpoint provides a comprehensive view of all user complaints,
    including complaint details, submitter information, targets, statuses, and
    admin responses. Useful for complaint management and monitoring.
    
    **Authentication:** Required - admin role only.
    
    **Permissions:** Only users with 'admin' role can access this endpoint.
    
    **Use Cases:**
    - Monitor complaint trends
    - Track unresolved complaints
    - Review complaint history
    - Generate compliance reports
    """,
    responses={
        200: OpenApiResponse(
            description="Successfully retrieved all complaints",
            examples=[
                OpenApiExample(
                    "All Complaints List",
                    value={
                        "complaints": [
                            {
                                "id": 1,
                                "profile": 456,
                                "target_complaint": 123,
                                "details": "Trainer behavior was unprofessional.",
                                "created_at": "2026-01-03T10:30:00Z",
                                "status": "in_review",
                                "admin_response": "Under investigation.",
                                "response_at": "2026-01-04T09:00:00Z"
                            },
                            {
                                "id": 2,
                                "profile": 789,
                                "target_complaint": 456,
                                "details": "Gym facility hygiene issues.",
                                "created_at": "2026-01-02T14:20:00Z",
                                "status": "resolved",
                                "admin_response": "Issue addressed with gym management.",
                                "response_at": "2026-01-03T11:00:00Z"
                            }
                        ]
                    },
                    response_only=True
                )
            ]
        ),
        401: OpenApiResponse(description="Authentication credentials were not provided"),
        403: OpenApiResponse(description="User does not have admin permissions"),
        500: OpenApiResponse(description="Internal server error")
    }
)
class CompaintAdminListView(APIView):
    """
    API view for administrators to view all complaints in the system.
    
    Provides admins with a complete list of all complaints across all users,
    including complaint details, associated profiles, and response status.
    Note: Class name contains typo ('Compaint' should be 'Complaint').
    
    Attributes:
        permission_classes: Requires HasRole(['admin']) - admin access only.
    
    HTTP Methods:
        GET: Retrieve list of all complaints
    
    Response:
        200: JSON object with 'complaints' array containing:
            - id: Complaint ID
            - profile: ID of profile that submitted complaint
            - target_complaint: ID of entity being complained about
            - details: Complaint description
            - created_at: Submission timestamp
            - status: Current status
            - admin_response: Admin's response (if any)
            - response_at: Response timestamp (if any)
    
    Example Response:
        {
            "complaints": [
                {
                    "id": 1,
                    "profile": 456,
                    "target_complaint": 123,
                    "details": "Complaint details",
                    "created_at": "2026-01-04T10:00:00Z",
                    "status": "pending",
                    "admin_response": null,
                    "response_at": null
                }
            ]
        }
    """
    
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
                "status": c.status,
                "admin_response": c.admin_response,
                "response_at": c.response_at
            }
            for c in complaints
        ]
        return Response({"complaints": data})


class PaymobService:
    """
    Service class for interacting with Paymob payment gateway API.
    
    Provides methods for payment operations including authentication, order creation,
    payment key generation, and refunds. Implements retry logic with exponential backoff
    for improved reliability.
    
    Class Attributes:
        DEFAULT_TIMEOUT (int): Default timeout in seconds for API requests (25s)
        MAX_RETRIES (int): Maximum number of retry attempts for failed requests (3)
        BACKOFF_SECONDS (int): Base delay in seconds between retry attempts (1s)
    
    Methods:
        authenticate(): Authenticate with Paymob and get auth token
        create_order(): Create a payment order
        create_payment_key(): Generate payment key for iframe integration
        refund_transaction(): Process refund for a transaction
    
    Configuration Required:
        - settings.PAYMOB_API_KEY: API key for Paymob authentication
        - settings.PAYMOB_CARD_INTEGRATION_ID: Integration ID for card payments
    
    API Base URL:
        https://accept.paymob.com/api
    
    Note:
        All methods implement automatic retry logic with exponential backoff
        for transient failures. Errors are logged via Django's logging system.
    """
    
    DEFAULT_TIMEOUT: int = 25
    MAX_RETRIES: int = 3
    BACKOFF_SECONDS: int = 1

    @staticmethod
    def authenticate() -> str:
        """
        Authenticate with Paymob API and return authentication token.
        
        Sends API key to Paymob authentication endpoint and retrieves a token
        used for subsequent API calls. Implements retry logic for reliability.
        
        Returns:
            str: Authentication token for use in other Paymob API calls.
        
        Raises:
            RuntimeError: If authentication fails after MAX_RETRIES attempts.
        
        API Endpoint:
            POST https://accept.paymob.com/api/auth/tokens
        
        Request Body:
            {"api_key": settings.PAYMOB_API_KEY}
        
        Example:
            >>> auth_token = PaymobService.authenticate()
            >>> print(f"Token: {auth_token[:10]}...")
        """
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
        """
        Create a payment order in Paymob system.
        
        Creates an order record in Paymob with specified amount. This order ID
        is required for subsequent payment key generation.
        
        Args:
            auth_token (str): Authentication token from authenticate() method.
            amount_cents (int): Order amount in cents (e.g., 10000 for 100.00 EGP).
        
        Returns:
            Dict[str, Any]: Order object containing 'id' and other order details.
        
        Raises:
            RuntimeError: If order creation fails after MAX_RETRIES attempts.
        
        API Endpoint:
            POST https://accept.paymob.com/api/ecommerce/orders
        
        Request Body:
            {
                "auth_token": str,
                "delivery_needed": "false",
                "amount_cents": int,
                "currency": "EGP",
                "items": []
            }
        
        Example:
            >>> auth_token = PaymobService.authenticate()
            >>> order = PaymobService.create_order(auth_token, 50000)
            >>> print(f"Order ID: {order['id']}")
        """
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
        """
        Generate a payment key for Paymob iframe integration.
        
        Creates a payment key (token) required to initialize the Paymob payment iframe.
        This key contains order details and expires after specified duration.
        
        Args:
            auth_token (str): Authentication token from authenticate() method.
            order_id (int): Order ID from create_order() method.
            amount_cents (int): Payment amount in cents (must match order amount).
            billing_data (Dict[str, Any]): Customer billing information including:
                - first_name: Customer first name
                - last_name: Customer last name
                - email: Customer email
                - phone_number: Customer phone
                - apartment, floor, street, building, city, country, etc.
        
        Returns:
            str: Payment key token for iframe initialization.
        
        Raises:
            RuntimeError: If payment key creation fails after MAX_RETRIES attempts.
        
        API Endpoint:
            POST https://accept.paymob.com/api/acceptance/payment_keys
        
        Note:
            - Payment key expires after 3600 seconds (1 hour)
            - Uses PAYMOB_CARD_INTEGRATION_ID from settings
            - Currency is hardcoded to EGP
        
        Example:
            >>> billing = {
            ...     "first_name": "John",
            ...     "last_name": "Doe",
            ...     "email": "john@example.com",
            ...     "phone_number": "+201234567890"
            ... }
            >>> key = PaymobService.create_payment_key(token, order_id, 50000, billing)
        """
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
        """
        Process a refund for a completed Paymob transaction.
        
        Initiates a refund request for a specific transaction. Note that refunds
        may take time to process and are subject to Paymob's refund policies.
        
        Args:
            auth_token (str): Authentication token from authenticate() method.
            transaction_id (int): ID of the transaction to refund.
            amount_cents (int): Refund amount in cents (can be partial or full).
        
        Returns:
            Dict[str, Any]: Refund response object with refund status and details.
        
        Raises:
            RuntimeError: If refund request fails.
        
        API Endpoint:
            POST https://accept.paymob.com/api/acceptance/void_refund/refund
        
        Request Body:
            {
                "auth_token": str,
                "transaction_id": int,
                "amount_cents": int
            }
        
        Note:
            - Refunds are subject to Paymob's terms and processing times
            - Partial refunds are supported by specifying amount less than original
            - Transaction must be in a refundable state
        
        Example:
            >>> auth_token = PaymobService.authenticate()
            >>> refund = PaymobService.refund_transaction(auth_token, 12345, 50000)
            >>> print(f"Refund status: {refund.get('status')}")
        """
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

