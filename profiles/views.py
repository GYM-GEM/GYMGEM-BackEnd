from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from utils.views import get_account_from_token, get_profile_id_from_token
from .models import Profile 
from accounts.models import Account
from .serializers import ProfileSerializer
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import permission_classes

@permission_classes([AllowAny])
class ProfileView(APIView):
    
    @extend_schema(
        tags=['Profiles'],
        summary='List all profiles',
        description='Get all profiles',
        responses={200: ProfileSerializer(many=True)}
    )
    def get(self, request):
        profiles = Profile.objects.all()
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
    def delete(self, request):
        try:
            password = request.data.get("password", None)
            profile_id = get_profile_id_from_token(request)
            profile = Profile.objects.get(id=profile_id)
            account = get_account_from_token(request)
            if not account.check_password(password):
                return Response({"error": "Incorrect password"}, status=400)
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