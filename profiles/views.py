from django.http.response import JsonResponse
from django.forms.models import model_to_dict
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from authenticationAndAuthorization.permissions import HasRole
from utils.views import get_account_from_token, get_profile_id_from_token
from .models import CashoutReport, Profile 
from accounts.models import Account
from .serializers import ProfileSerializer
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
@permission_classes([AllowAny])
class ProfileView(APIView):
    
    @extend_schema(
        tags=['Profiles'],
        summary='List all profiles',
        description='Get all profiles',
        responses={200: ProfileSerializer(many=True)}
    )
    def get(self, request):
        profiles = Profile.objects.all().select_related('account')
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Profiles'],
        summary='Create new profile',
        description='Create a new profile for an account',
        request=ProfileSerializer,
        responses={201: ProfileSerializer, 400: {'description': 'Validation error'}}
    )
    def post(self, request):
        my_account = get_account_from_token(request)
        serializer = ProfileSerializer(data={**request.data, 'account': my_account.pk})
        if not my_account:
            return Response({"error": "Invalid account"}, status=400)
        my_profiles = Profile.objects.filter(account=my_account)
        if serializer.is_valid():
            serializer.save()
            if my_profiles.count() == 1:
                Account.objects.filter(id=my_account.id).update(default_profile=serializer.data.get("id"))
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
@permission_classes([AllowAny])
class ProfileUpdateView(APIView):
    @extend_schema(
        tags=['Profiles'],
        summary='Retrieve all profiles for the authenticated account',
        description='Get all profiles associated with the authenticated account',
        responses={200: ProfileSerializer(many=True)}
    )
    def get(self, request):
        account = get_account_from_token(request)
        profiles = Profile.objects.filter(account=account)
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)
        
    @extend_schema(
        tags=['Profiles'],
        summary='Update profile',
        description='Update an existing profile',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        request=ProfileSerializer,
        responses={200: ProfileSerializer, 404: {'description': 'Profile not found'}, 400: {'description': 'Validation error'}}
    )
    def put(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    @extend_schema(
        tags=['Profiles'],
        summary='Delete profile',
        description='Delete an existing profile',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        responses={204: {'description': 'Profile deleted'}, 404: {'description': 'Profile not found'}}
    )
    def delete(self, request, profile_id):
        try:
            
            password = request.data.get("password", None)
            token_profile_id = get_profile_id_from_token(request)
            if token_profile_id != profile_id:
                return Response({"error": "Profile ID from token does not match"}, status=400)
            profile = Profile.objects.get(pk=profile_id)
            account = get_account_from_token(request)
            try:
                if account.has_usable_password():
                    password = request.data.get("password", None)
                    if not account.check_password(password):
                        return JsonResponse({"error": "Incorrect password"}, status=400)
            except Account.DoesNotExist:
                return JsonResponse({"error": "Account not found"}, status=404)

            if account.default_profile and account.default_profile.id == profile.id:
                account.default_profile = account.profiles.exclude(id=profile.id).first()
                account.save()
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        
        profile.delete()
        return Response(status=204)
    
    @extend_schema(
        tags=['Profiles'],
        summary='Partially update profile',
        description='Partially update an existing profile',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        request=ProfileSerializer,
        responses={200: ProfileSerializer, 404: {'description': 'Profile not found'}, 400: {'description': 'Validation error'}}
    )
    def patch(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
   
   
class ProfileAdminView(APIView):
    permission_classes = [HasRole('admin')]
    @extend_schema(
        tags=['Profiles'],
        summary='Get profile by ID',
        description='Retrieve a profile by its ID',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        responses={200: ProfileSerializer, 404: {'description': 'Profile not found'}}
    )
    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
            profile_details = profile.get_profile_data
            if profile_details is None:
                return Response({"error": "Profile data not found"}, status=404)

            # Build a simple dict payload without serializers
            base_profile_data = model_to_dict(
                profile, fields=["id", "profile_type", "status", "account", "created_at"]
            )
            detailed_profile_data = model_to_dict(profile_details)

            return Response({
                "profile": base_profile_data,
                "profile_data": detailed_profile_data,
            })
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        
    @extend_schema(
        tags=['Profiles'],
        summary='Delete profile by ID',
        description='Delete a profile by its ID',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        responses={204: {'description': 'Profile deleted'}, 404: {'description': 'Profile not found'}}
    )
    def delete(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        
        profile.delete()
        return Response(status=204)
    
    @extend_schema(
        tags=['Profiles'],
        summary='suspend profile by ID',
        description='Suspend a profile by its ID',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        responses={200: {'description': 'Profile suspended'}, 404: {'description': 'Profile not found'}}
    )
    def post(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
            if not profile.admin_deleted:
                profile.status = "suspended"
                profile.admin_deleted = True
                profile.save()
                return Response({"message": "Profile suspended"})
            else:
                profile.admin_deleted = False
                profile.status = "active"
                profile.save()
                return Response({"message": "Profile reactivated"})
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

class ProfilesAdminListView(APIView):
    permission_classes = [HasRole('admin')]
    @extend_schema(
        tags=['Profiles'],
        summary='List all profiles (Admin)',
        description='Get all profiles with detailed information (Admin only)',
        responses={200: ProfileSerializer(many=True)}
    )
    def get(self, request):
        profiles = Profile.objects.all().select_related('account')
        detailed_profiles = []
        for profile in profiles:
            profile_details = profile.get_profile_data
            if profile_details is None:
                continue

            # Build a simple dict payload without serializers
            base_profile_data = model_to_dict(
                profile, fields=["id", "profile_type", "status", "account", "created_at"]
            )
            detailed_profile_data = model_to_dict(profile_details)

            detailed_profiles.append({
                "profile": base_profile_data,
                "profile_data": detailed_profile_data,
            })

        return Response(detailed_profiles)
 
class ProfileBalanceView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=['Profiles'],
        summary='Get profile balance',
        description='Retrieve the balance of the authenticated profile',
        responses={200: {'type': 'object', 'properties': {'balance': {'type': 'number'}}}, 404: {'description': 'Profile not found'}}
    )
    def get(self, request):
        profile_id = get_profile_id_from_token(request)
        try:
            profile = Profile.objects.get(id=profile_id).get_profile_data
            balance = profile.balance
            return Response({"balance": balance})
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        except Exception:
            return Response({"error": "Profile data is incomplete or corrupted"}, status=400)
            
class ProfileHideToggleView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=['Profiles'],
        summary='Toggle profile',
        description='Toggle the authenticated profile (soft delete)',
        responses={200: {'description': 'Profile hidden'}, 404: {'description': 'Profile not found'}}
    )
    def post(self, request):
        profile_id = get_profile_id_from_token(request)
        try:
            profile = Profile.objects.get(id=profile_id)
            if profile.admin_deleted:
                return Response({"error": "Profile has been deleted by admin and cannot be modified."}, status=403)
            profile.status = "inactive" if profile.status == "active" else "active"
            profile.save()
            return Response({"message": "Profile status toggled", "new_status": profile.status})
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        

class ProfileBalanceAdminView(APIView):
    permission_classes = [HasRole('admin')]
    @extend_schema(
        tags=['Profiles'],
        summary='Get profile balance by ID (Admin)',
        description='Retrieve the balance of a profile by its ID (Admin only)',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        responses={200: {'type': 'object', 'properties': {'balance': {'type': 'number'}}}, 404: {'description': 'Profile not found'}}
    )
    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id).get_profile_data
            balance = profile.balance
            return Response({"balance": balance})
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        except Exception:
            return Response({"error": "Profile data is incomplete or corrupted"}, status=400)
        
    @extend_schema(
        tags=['Profiles'],
        summary='Update profile balance by ID (Admin)',
        description='Update the balance of a profile by its ID (Admin only)',
        parameters=[
            OpenApiParameter(
                name='profile_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Profile ID'
            ),
        ],
        request={'type': 'object', 'properties': {'balance': {'type': 'number'}}},
        responses={200: {'description': 'Balance updated'}, 404: {'description': 'Profile not found'}, 400: {'description': 'Validation error'}}
    )
    def post(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id).get_profile_data
            new_balance = request.data.get("balance", None)
            operation = request.data.get("operation")  # 'set' or 'add'
            if new_balance is None:
                return Response({"error": "Balance value is required"}, status=400)
            try:
                new_balance = int(new_balance)
            except ValueError:
                return Response({"error": "Invalid balance value"}, status=400)
            if operation == 'set':
                profile.balance = new_balance
            elif operation == 'add':
                profile.balance += new_balance
            elif operation == 'subtract':
                profile.balance -= new_balance
            else:
                return Response({"error": "Invalid operation"}, status=400)
            profile.save()
            return Response({"message": "Balance updated"})
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        except Exception:
            return Response({"error": "Profile data is incomplete or corrupted"}, status=400)
        
class CashoutReportAdminView(APIView):
    permission_classes = [HasRole('admin')]
    @extend_schema(
        tags=['Profiles'],
        summary='List cashout reports (Admin)',
        description='Get all cashout reports (Admin only)',
        responses={200: {'type': 'array', 'items': {'type': 'object'}}}
    )
    def get(self, request):
        reports = CashoutReport.objects.all().select_related('profile', 'profile__account')
        report_list = []
        for report in reports:
            report_data = model_to_dict(report)
            report_data['profile'] = model_to_dict(report.profile, fields=["id", "profile_type", "status", "account", "created_at"])
            report_data['account'] = model_to_dict(report.profile.account, fields=["id", "username", "email"])
            report_list.append(report_data)
        return Response(report_list)
    
class CashoutReportAdminDetailView(APIView):
    permission_classes = [HasRole('admin')]
    @extend_schema(
        tags=['Profiles'],
        summary='Get cashout report by ID (Admin)',
        description='Retrieve a cashout report by its ID (Admin only)',
        parameters=[
            OpenApiParameter(
                name='report_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Cashout Report ID'
            ),
        ],
        responses={200: {'type': 'object'}, 404: {'description': 'Cashout report not found'}}
    )
    def get(self, request, report_id):
        try:
            report = CashoutReport.objects.select_related('profile', 'profile__account').get(id=report_id)
            report_data = model_to_dict(report)
            report_data['profile'] = model_to_dict(report.profile, fields=["id", "profile_type", "status", "account", "created_at"])
            report_data['account'] = model_to_dict(report.profile.account, fields=["id", "username", "email"])
            return Response(report_data)
        except CashoutReport.DoesNotExist:
            return Response({"error": "Cashout report not found"}, status=404)