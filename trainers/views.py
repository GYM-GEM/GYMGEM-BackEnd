from .serializers import TrainerSerializer , TrainerSpecializationSerializer, TrainerExperienceSerializer
from .models import Trainer, TrainerSpecialization, TrainerExperience
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
# Create your views here.

class TrainerView(APIView):
    
    @extend_schema(
        tags=['Trainers'],
        summary='List all trainers',
        responses=TrainerSerializer(many=True)
    )
    def get(self, request):
        trainers = Trainer.objects.all()
        serializer = TrainerSerializer(trainers, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Trainers'],
        summary='Create new trainer',
        request=TrainerSerializer,
        responses=TrainerSerializer
    )
    def post(self, request):
        serializer = TrainerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class TrainerUpdateView(APIView):
    
    @extend_schema(
        tags=['Trainers'],
        summary='Update trainer',
        description='Update an existing trainer',
        parameters=[
            OpenApiParameter(
                name='trainer_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Trainer ID'
            ),
        ],
        request=TrainerSerializer,
        responses={200: TrainerSerializer, 404: {'description': 'Trainer not found'}, 400: {'description': 'Validation error'}}
    )
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
    
    @extend_schema(
        tags=['Trainers'],
        summary='Delete trainer',
        description='Delete an existing trainer',
        parameters=[
            OpenApiParameter(
                name='trainer_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Trainer ID'
            ),
        ],
        responses={204: {'description': 'Trainer deleted'}, 404: {'description': 'Trainer not found'}}
    )
    def delete(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)
        
        trainer.delete()
        return Response(status=204)
    
    @extend_schema(
        tags=['Trainers'],
        summary='Partially update trainer',
        description='Partially update an existing trainer',
        parameters=[
            OpenApiParameter(
                name='trainer_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Trainer ID'
            ),
        ],
        request=TrainerSerializer,
        responses={200: TrainerSerializer, 404: {'description': 'Trainer not found'}, 400: {'description': 'Validation error'}}
    )
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
    
    @extend_schema(
        tags=['Trainers'],
        summary='List all trainer specializations',
        description='Get all trainer specializations',
        responses={200: TrainerSpecializationSerializer(many=True)}
    )
    def get(self, request):
        specializations = TrainerSpecialization.objects.all()
        serializer = TrainerSpecializationSerializer(specializations, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Trainers'],
        summary='Create new trainer specialization',
        description='Create a new trainer specialization',
        request=TrainerSpecializationSerializer,
        responses={201: TrainerSpecializationSerializer, 400: {'description': 'Validation error'}}
    )
    def post(self, request):
        serializer = TrainerSpecializationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class TrainerSpecializationUpdateView(APIView):
    
    @extend_schema(
        tags=['Trainers'],
        summary='Update trainer specialization',
        description='Update an existing trainer specialization',
        parameters=[
            OpenApiParameter(
                name='specialization_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Specialization ID'
            ),
        ],
        request=TrainerSpecializationSerializer,
        responses={200: TrainerSpecializationSerializer, 404: {'description': 'TrainerSpecialization not found'}, 400: {'description': 'Validation error'}}
    )
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
    
    @extend_schema(
        tags=['Trainers'],
        summary='Delete trainer specialization',
        description='Delete an existing trainer specialization',
        parameters=[
            OpenApiParameter(
                name='specialization_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Specialization ID'
            ),
        ],
        responses={204: {'description': 'TrainerSpecialization deleted'}, 404: {'description': 'TrainerSpecialization not found'}}
    )
    def delete(self, request, specialization_id):
        try:
            specialization = TrainerSpecialization.objects.get(id=specialization_id)
        except TrainerSpecialization.DoesNotExist:
            return Response({"error": "TrainerSpecialization not found"}, status=404)
        
        specialization.delete()
        return Response(status=204)
    
    @extend_schema(
        tags=['Trainers'],
        summary='Partially update trainer specialization',
        description='Partially update an existing trainer specialization',
        parameters=[
            OpenApiParameter(
                name='specialization_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Specialization ID'
            ),
        ],
        request=TrainerSpecializationSerializer,
        responses={200: TrainerSpecializationSerializer, 404: {'description': 'TrainerSpecialization not found'}, 400: {'description': 'Validation error'}}
    )
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
    
    @extend_schema(
        tags=['Trainers'],
        summary='List all trainer experiences',
        description='Get all trainer experiences',
        responses={200: TrainerExperienceSerializer(many=True)}
    )
    def get(self, request):
        experiences = TrainerExperience.objects.all()
        serializer = TrainerExperienceSerializer(experiences, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Trainers'],
        summary='Create new trainer experience',
        description='Create a new trainer experience',
        request=TrainerExperienceSerializer,
        responses={201: TrainerExperienceSerializer, 400: {'description': 'Validation error'}}
    )
    def post(self, request):
        serializer = TrainerExperienceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class TrainerExperienceUpdateView(APIView):
    
    @extend_schema(
        tags=['Trainers'],
        summary='Update trainer experience',
        description='Update an existing trainer experience',
        parameters=[
            OpenApiParameter(
                name='experience_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Experience ID'
            ),
        ],
        request=TrainerExperienceSerializer,
        responses={200: TrainerExperienceSerializer, 404: {'description': 'TrainerExperience not found'}, 400: {'description': 'Validation error'}}
    )
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

    @extend_schema(
        tags=['Trainers'],
        summary='Delete trainer experience',
        description='Delete an existing trainer experience',
        parameters=[
            OpenApiParameter(
                name='experience_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Experience ID'
            ),
        ],
        responses={204: {'description': 'TrainerExperience deleted'}, 404: {'description': 'TrainerExperience not found'}}
    )
    def delete(self, request, experience_id):
        try:
            experience = TrainerExperience.objects.get(id=experience_id)
        except TrainerExperience.DoesNotExist:
            return Response({"error": "TrainerExperience not found"}, status=404)

        experience.delete()
        return Response(status=204)

    @extend_schema(
        tags=['Trainers'],
        summary='Partially update trainer experience',
        description='Partially update an existing trainer experience',
        parameters=[
            OpenApiParameter(
                name='experience_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description='Experience ID'
            ),
        ],
        request=TrainerExperienceSerializer,
        responses={200: TrainerExperienceSerializer, 404: {'description': 'TrainerExperience not found'}, 400: {'description': 'Validation error'}}
    )
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