from django.shortcuts import render

from authenticationAndAuthorization.permissions import required_roles
from .serializers import TrainerSerializer
from .models import Trainer
from rest_framework.views import APIView
from rest_framework.response import Response
# Create your views here.

class TrainerView(APIView):
    
    def get(self, request):
        trainers = Trainer.objects.all()
        serializer = TrainerSerializer(trainers, many=True)
        return Response(serializer.data)

    @required_roles('trainer')
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
