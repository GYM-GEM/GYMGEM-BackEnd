from .serializers import TrainerSerializer , TrainerSpecializationSerializer, TrainerExperienceSerializer
from .models import Trainer, TrainerSpecialization, TrainerExperience
from rest_framework.views import APIView
from rest_framework.response import Response
# Create your views here.

class TrainerView(APIView):
    
    def get(self, request):
        trainers = Trainer.objects.all()
        serializer = TrainerSerializer(trainers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TrainerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class TrainerUpdateView(APIView):
    def put(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)
        
        serializer = TrainerSerializer(trainer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    def delete(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)
        
        trainer.delete()
        return Response(status=204)
    
    def patch(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)
        
        serializer = TrainerSerializer(trainer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
class TrainerSpecializationView(APIView):
    
    def get(self, request):
        specializations = TrainerSpecialization.objects.all()
        serializer = TrainerSpecializationSerializer(specializations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TrainerSpecializationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class TrainerSpecializationUpdateView(APIView):
    def put(self, request, specialization_id):
        try:
            specialization = TrainerSpecialization.objects.get(id=specialization_id)
        except TrainerSpecialization.DoesNotExist:
            return Response({"error": "TrainerSpecialization not found"}, status=404)
        
        serializer = TrainerSpecializationSerializer(specialization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    def delete(self, request, specialization_id):
        try:
            specialization = TrainerSpecialization.objects.get(id=specialization_id)
        except TrainerSpecialization.DoesNotExist:
            return Response({"error": "TrainerSpecialization not found"}, status=404)
        
        specialization.delete()
        return Response(status=204)
    
    def patch(self, request, specialization_id):
        try:
            specialization = TrainerSpecialization.objects.get(id=specialization_id)
        except TrainerSpecialization.DoesNotExist:
            return Response({"error": "TrainerSpecialization not found"}, status=404)
        
        serializer = TrainerSpecializationSerializer(specialization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
class TrainerExperienceView(APIView):
    
    def get(self, request):
        experiences = TrainerExperience.objects.all()
        serializer = TrainerExperienceSerializer(experiences, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TrainerExperienceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class TrainerExperienceUpdateView(APIView):
    def put(self, request, experience_id):
        try:
            experience = TrainerExperience.objects.get(id=experience_id)
        except TrainerExperience.DoesNotExist:
            return Response({"error": "TrainerExperience not found"}, status=404)

        serializer = TrainerExperienceSerializer(experience, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, experience_id):
        try:
            experience = TrainerExperience.objects.get(id=experience_id)
        except TrainerExperience.DoesNotExist:
            return Response({"error": "TrainerExperience not found"}, status=404)

        experience.delete()
        return Response(status=204)

    def patch(self, request, experience_id):
        try:
            experience = TrainerExperience.objects.get(id=experience_id)
        except TrainerExperience.DoesNotExist:
            return Response({"error": "TrainerExperience not found"}, status=404)

        serializer = TrainerExperienceSerializer(experience, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)