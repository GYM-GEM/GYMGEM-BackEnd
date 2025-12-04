from .models import Gym , Gym_branch
from .serializers import GymBranchSerializer, GymSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
class StoreView(APIView):
    def get(self, request):
        gyms = Gym.objects.all()
        serializer = GymSerializer(gyms, many=True)     
        return Response(serializer.data)
    def post(self, request):
        serializer = GymSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class GymUpdateView(APIView):
    def put(self, request, gym_id):
        try:
            gym = Gym.objects.get(profile_id=gym_id)
        except Gym.DoesNotExist:
            return Response({"error": "Gym not found"}, status=404)

        serializer = GymSerializer(gym, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, gym_id):
        try:
            gym = Gym.objects.get(profile_id=gym_id)
        except Gym.DoesNotExist:
            return Response({"error": "Gym not found"}, status=404)

        gym.delete()
        return Response(status=204)

    def patch(self, request, gym_id):
        try:
            gym = Gym.objects.get(profile_id=gym_id)
        except Gym.DoesNotExist:
            return Response({"error": "Gym not found"}, status=404)

        serializer = GymSerializer(gym, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
class GymBranchView(APIView):
    def get(self, request):
        branches = Gym_branch.objects.all()
        serializer = GymBranchSerializer(branches, many=True)     
        return Response(serializer.data)
    def post(self, request):
        serializer = GymBranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class GymBranchUpdateView(APIView):
    def put(self, request, branch_id):
        try:
            branch = Gym_branch.objects.get(id=branch_id)
        except Gym_branch.DoesNotExist:
            return Response({"error": "Gym Branch not found"}, status=404)

        serializer = GymBranchSerializer(branch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, branch_id):
        try:
            branch = Gym_branch.objects.get(id=branch_id)
        except Gym_branch.DoesNotExist:
            return Response({"error": "Gym Branch not found"}, status=404)

        branch.delete()
        return Response(status=204)

    def patch(self, request, branch_id):
        try:
            branch = Gym_branch.objects.get(id=branch_id)
        except Gym_branch.DoesNotExist:
            return Response({"error": "Gym Branch not found"}, status=404)

        serializer = GymBranchSerializer(branch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)  