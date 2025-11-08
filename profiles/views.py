from django.shortcuts import render
from rest_framework.views import APIView
from .models import Profile 
from accounts.models import Account
from .serializers import ProfileSerializer
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
# Create your views here.

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
        serializer = ProfileSerializer(data=request.data)
        my_profiles = Profile.objects.filter(account=request.data.get('account'))
        if serializer.is_valid():
            serializer.save()
            if len(my_profiles) == 1:
                Account.objects.filter(id=serializer.data.get('account')).update(default_profile=serializer.data.get("id"))
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class ProfileUpdateView(APIView):
    
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
            profile = Profile.objects.get(id=profile_id)
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