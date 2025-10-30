from django.shortcuts import render
from rest_framework.views import APIView
from .models import Profile 
from accounts.models import Account
from .serializers import ProfileSerializer
from rest_framework.response import Response
# Create your views here.

class ProfileView(APIView):
    
    def get(self, request):
        profiles = Profile.objects.all()
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ProfileSerializer(data=request.data)
        my_profiles = Profile.objects.filter(account=request.data.get('account'))
        if serializer.is_valid():
            serializer.save()
            if len(my_profiles) < 1:
                Account.objects.filter(id=serializer.data.get('account')).update(default_profile=serializer.data.get("id"))
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class ProfileUpdateView(APIView):
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
    
    def delete(self, request, profile_id):
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
        
        profile.delete()
        return Response(status=204)
    
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