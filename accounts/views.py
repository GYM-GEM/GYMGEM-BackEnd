from django.conf import settings
from django.forms import model_to_dict
from django.http import JsonResponse
from rest_framework import status
import jwt
from rest_framework.views import APIView
from accounts.models import Account
from courses.models import Course, CourseEnrollment
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from authenticationAndAuthorization.permissions import HasRole
from utils.views import get_account_from_token
from rest_framework.permissions import IsAuthenticated

# Create your views here.


class AccountsListView(APIView):
    """Handles operations on the accounts collection"""

    permission_classes = [HasRole(["admin"])]

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_list",
        summary="List all accounts",
        description="Get all user accounts",
        responses={200: {"description": "List of accounts"}},
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
                "defaultProfile": (
                    {
                        "id": account.default_profile.id,
                        "profileType": account.default_profile.profile_type,
                    }
                    if account.default_profile
                    else None
                ),
            }
            for account in accounts
        ]
        return JsonResponse(data, safe=False)



class AccountsCreateView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_create",
        summary="Create new account",
        description="Create a new user account with username, email and password",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string"},
                    "confirmPassword": {"type": "string"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                },
                "required": ["username", "email", "password", "confirmPassword"],
            }
        },
        responses={
            201: {"description": "Account created"},
            400: {"description": "Bad request"},
        },
    )
    def post(self, request):
        """Create a new account"""
        if request.data.get("password") != request.data.get("confirmPassword"):
            return JsonResponse({"error": "Passwords do not match"}, status=400)
        if Account.objects.filter(username=request.data.get("username")).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)
        if Account.objects.filter(email=request.data.get("email")).exists():
            return JsonResponse({"error": "Email already exists"}, status=400)
        account = Account.objects.create(
            username=request.data.get("username"),
            email=request.data.get("email"),
            password=make_password(request.data.get("password")),
            first_name=request.data.get("firstName", ""),
            last_name=request.data.get("lastName", ""),
        )
        try:
            from utils.views import send_verification_email

            send_verification_email(account, request)
        except Exception as e:
            print("Failed to send verification email.", e)
        return JsonResponse({"id": account.id}, status=201)


class AccountsVerifyView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_verify",
        summary="Verify account email",
        description="Verify a user account using a verification token",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                },
                "required": ["token"],
            }
        },
        responses={
            200: {"description": "Account verified"},
            400: {"description": "Bad request"},
        },
    )
    def post(self, request):
        """Verify account email"""
        token = request.data.get("token")
        if not token:
            return JsonResponse({"error": "Token is required"}, status=400)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            account_id = payload.get("user_id")
            account = Account.objects.get(id=account_id)
            account.is_verified = True
            account.save()
            return JsonResponse({"message": "Account verified successfully"})
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=400)



class AccountsDetailView(APIView):
    permission_classes = [IsAuthenticated]
    """Handles operations on individual accounts"""

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_retrieve",
        summary="Retrieve account by ID",
        description="Get details of a specific account",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Account ID",
            ),
        ],
        responses={
            200: {"description": "Account data"},
            404: {"description": "Account not found"},
        },
    )
    def get(self, request, account_id):
        if (get_account_from_token(request).id != account_id) and (
            not request.user.is_superuser
        ):
            return JsonResponse({"error": "Forbidden"}, status=403)
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
                "defaultProfile": (
                    {
                        "id": account.default_profile.id,
                        "profileType": account.default_profile.profile_type,
                    }
                    if account.default_profile
                    else None
                ),
                "createdAt": account.created_at,
                "updatedAt": account.updated_at,
                "profiles": [
                    {
                        "id": profile.id,
                        "profileType": profile.profile_type,
                    }
                    for profile in account.profiles.all()
                ],
            }
            return JsonResponse(data)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_update",
        summary="Update account",
        description="Update an existing account with new data",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Account ID",
            ),
        ],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                },
            }
        },
        responses={
            200: {"description": "Account updated"},
            404: {"description": "Account not found"},
        },
    )
    def put(self, request, account_id):
        if (get_account_from_token(request).id != account_id) and (
            not request.user.is_superuser
        ):
            return JsonResponse({"error": "Forbidden"}, status=403)
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
        tags=["Accounts"],
        operation_id="accounts_partial_update",
        summary="Partially update account",
        description="Partially update an existing account",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Account ID",
            ),
        ],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                },
            }
        },
        responses={
            200: {"description": "Account updated"},
            404: {"description": "Account not found"},
        },
    )
    def patch(self, request, account_id):
        if (get_account_from_token(request).id != account_id) and (
            not request.user.is_superuser
        ):
            return JsonResponse({"error": "Forbidden"}, status=403)
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
            if "defaultProfileId" in request.data:
                from profiles.models import Profile

                try:
                    profile = Profile.objects.get(
                        id=request.data["defaultProfileId"], account=account
                    )
                    account.default_profile = profile
                except Profile.DoesNotExist:
                    return JsonResponse(
                        {
                            "error": "Default profile not found or does not belong to the account"
                        },
                        status=400,
                    )
            account.save()
            return JsonResponse({"message": "Account partially updated successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_delete",
        summary="Delete account",
        description="Delete an existing account",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Account ID",
            ),
        ],
        responses={
            200: {"description": "Account deleted"},
            404: {"description": "Account not found"},
        },
    )
    def delete(self, request):
        print("Request user:", request.user)
        account = get_account_from_token(request)
        if (request.user.id != account.id) and (not request.user.is_superuser):
            return JsonResponse({"error": "Forbidden"}, status=403)
        """Delete an account"""
        try:
            if account.has_usable_password():
                password = request.data.get("password", None)
                if not account.check_password(password):
                    return JsonResponse({"error": "Incorrect password"}, status=400)
            account = Account.objects.get(id=request.user.id)
            account.delete()
            return JsonResponse({"message": "Account deleted successfully"}, status=204)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)


class CurrentAccountView(APIView):
    """Handles retrieval of the current authenticated user's account"""

    @extend_schema(
        tags=["Accounts"],
        operation_id="current_account_retrieve",
        summary="Retrieve current user account",
        description="Get details of the currently authenticated user account",
        responses={
            200: {"description": "Current account data"},
            401: {"description": "Unauthorized"},
        },
    )
    def get(self, request):
        """Retrieve the current authenticated user's account"""
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        try:
            account = Account.objects.get(id=user.id)
            data = {
                "id": account.id,
                "username": account.username,
                "email": account.email,
                "firstName": account.first_name,
                "lastName": account.last_name,
                "defaultProfile": (
                    {
                        "id": account.default_profile.id,
                        "profileType": account.default_profile.profile_type,
                    }
                    if account.default_profile
                    else None
                ),
                "profiles": [
                    {
                        "id": profile.id,
                        "profileType": profile.profile_type,
                    }
                    for profile in account.profiles.all()
                ],
            }
            return JsonResponse(data)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)


class AccountsPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_change_password",
        summary="Change account password",
        description="Change the password of an existing account",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Account ID",
            ),
        ],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "currentPassword": {"type": "string"},
                    "newPassword": {"type": "string"},
                    "confirmPassword": {"type": "string"},
                },
                "required": ["currentPassword", "newPassword", "confirmPassword"],
            }
        },
        responses={
            200: {"description": "Password changed"},
            400: {"description": "Bad request"},
            404: {"description": "Account not found"},
        },
    )
    def post(self, request):
        """Change account password"""
        try:
            account = get_account_from_token(request)
            if account.has_usable_password():
                old_password = request.data.get("currentPassword")
                print("Old password provided:", old_password)
                if not account.check_password(old_password):
                    return JsonResponse(
                        {"error": "Old password is incorrect"}, status=400
                    )
            new_password = request.data.get("newPassword")
            confirm_password = request.data.get("confirmPassword")
            if new_password != confirm_password:
                return JsonResponse({"error": "New passwords do not match"}, status=400)
            account.set_password(new_password)
            account.save()
            return JsonResponse({"message": "Password changed successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)

class AccountsManageStatusView(APIView):
    """Handles updating the status of an account"""

    permission_classes = [HasRole(["admin"])]

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_update_status",
        summary="Update account status",
        description="Update the status of an existing account",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Account ID",
            ),
        ],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["active", "inactive", "suspended"]},
                },
                "required": ["status"],
            }
        },
        responses={
            200: {"description": "Account status updated"},
            400: {"description": "Bad request"},
            404: {"description": "Account not found"},
        },
    )
    def patch(self, request, account_id):
        """Update account status"""
        try:
            account = Account.objects.get(id=account_id)
            new_status = request.data.get("status")
            if new_status not in dict(Account.STATUS_CHOICES).keys():
                return JsonResponse({"error": "Invalid status value"}, status=400)
            account.status = new_status
            account.admin_deleted = new_status == "suspended"
            account.save()
            return JsonResponse({"message": "Account status updated successfully"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
        
    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_get_status",
        summary="get all data related with the account, it's profiles, detailed profiled data and courses and products if any",
        description="Get all data related with the account, it's profiles, detailed profiled data and courses and products if any",
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Account ID",
            ),
        ],
        responses={
            200: {"description": "Account data with profiles and detailed data"},
            404: {"description": "Account not found"},
        },
    )
    def get(self, request, account_id):
        """Get all data related with the account, it's profiles, detailed profiled data and courses and products if any"""
        try:
            account = Account.objects.get(id=account_id)
            profiles_data = []
            for profile in account.profiles.all():
                profile_data = {
                    "id": profile.id,
                    "profileType": profile.profile_type,
                    "status": profile.status,
                    "createdAt": profile.created_at,
                }
                detailed_data = profile.get_profile_data
                if detailed_data is None:
                    profile_data["profileData"] = {}
                else:
                    profile_data["profileData"] = model_to_dict(detailed_data)

                # Include courses/enrollments without serializers
                if profile.profile_type == "trainer":
                    trainer_courses = Course.objects.filter(
                        trainer_profile=profile, is_deleted=False
                    )
                    profile_data["courses"] = [
                        {
                            "id": course.id,
                            "title": course.title,
                            "status": course.status,
                            "price": course.price,
                            "createdAt": course.created_at,
                            "updatedAt": course.updated_at,
                        }
                        for course in trainer_courses
                    ]
                elif profile.profile_type == "trainee":
                    enrollments = CourseEnrollment.objects.filter(
                        trainee_profile=profile
                    ).select_related("course")
                    profile_data["enrollments"] = [
                        {
                            "course": {
                                "id": enrollment.course.id,
                                "title": enrollment.course.title,
                                "status": enrollment.course.status,
                                "price": enrollment.course.price,
                            },
                            "enrollmentDate": enrollment.enrollment_date,
                            "status": enrollment.status,
                            "rating": enrollment.rating,
                            "review": enrollment.review,
                            "reviewDate": enrollment.review_date,
                            "permanentAccess": enrollment.permanent_access,
                            "dueDate": enrollment.due_date,
                        }
                        for enrollment in enrollments
                    ]
                profiles_data.append(profile_data)

            data = {
                "id": account.id,
                "username": account.username,
                "email": account.email,
                "firstName": account.first_name,
                "lastName": account.last_name,
                "status": account.status,
                "createdAt": account.created_at,
                "updatedAt": account.updated_at,
                "profiles": profiles_data,
            }
            return JsonResponse(data)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
        
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_request_password_reset",
        summary="Request password reset",
        description="Request a password reset email",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                },
                "required": ["email"],
            }
        },
        responses={
            200: {"description": "Password reset email sent"},
            400: {"description": "Bad request"},
        },
    )
    def post(self, request):
        """Request password reset"""
        from utils.views import send_password_reset_email

        email = request.data.get("email")
        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)
        try:
            account = Account.objects.get(email=email)
            send_password_reset_email(account, request)
            return JsonResponse({"message": "Password reset email sent"})
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=400)
        
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Accounts"],
        operation_id="accounts_confirm_password_reset",
        summary="Confirm password reset",
        description="Reset password using a valid token",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "newPassword": {"type": "string"},
                    "confirmPassword": {"type": "string"},
                },
                "required": ["token", "newPassword", "confirmPassword"],
            }
        },
        responses={
            200: {"description": "Password reset successful"},
            400: {"description": "Bad request"},
        },
    )
    def post(self, request):
        """Confirm password reset"""
        token = request.data.get("token")
        new_password = request.data.get("newPassword")
        confirm_password = request.data.get("confirmPassword")
        if not token:
            return JsonResponse({"error": "Token is required"}, status=400)
        if new_password != confirm_password:
            return JsonResponse({"error": "Passwords do not match"}, status=400)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            account_id = payload.get("user_id")
            account = Account.objects.get(id=account_id)
            pw = make_password(new_password)
            account.password = pw
            account.save()
            return JsonResponse({"message": "Password reset successful"})
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        except Account.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=400)