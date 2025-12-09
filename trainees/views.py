from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Trainee
from .serializers import TraineeSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

# Create your views here.
class TraineeView(APIView):
    
    @extend_schema(
        tags=["Trainees"],
        summary="List all trainees",
        description="Retrieve all trainees",
        responses={200: TraineeSerializer(many=True)},
    )
    def get(self, request):
        trainees = Trainee.objects.all().select_related(
            'profile_id',
            'profile_id__account'
        )
        serializer = TraineeSerializer(trainees, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Trainees"],
        summary="Create trainee profile",
        description="Create a new trainee",
        request=TraineeSerializer,
        responses={201: TraineeSerializer, 400: {"description": "Validation error"}},
    )
    def post(self, request):
        serializer = TraineeSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)  

class TraineeUpdateView(APIView):
    @extend_schema(
        tags=["Trainees"],
        summary="Update trainee",
        description="Update an existing trainee",
        parameters=[
            OpenApiParameter(
                name="trainee_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Trainee ID",
            )
        ],
        request=TraineeSerializer,
        responses={200: TraineeSerializer, 404: {"description": "Trainee not found"}, 400: {"description": "Validation error"}},
    )
    def put(self, request, trainee_id):
        try:
            trainee = Trainee.objects.get(id=trainee_id)
        except Trainee.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        serializer = TraineeSerializer(trainee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    @extend_schema(
        tags=["Trainees"],
        summary="Delete trainee",
        description="Delete an existing trainee",
        parameters=[
            OpenApiParameter(
                name="trainee_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Trainee ID",
            )
        ],
        responses={204: {"description": "Trainee deleted"}, 404: {"description": "Trainee not found"}},
    )
    def delete(self, request, trainee_id):
        try:
            trainee = Trainee.objects.get(id=trainee_id)
        except Trainee.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        trainee.delete()
        return Response(status=204)
    
    @extend_schema(
        tags=["Trainees"],
        summary="Partially update trainee",
        description="Partially update an existing trainee",
        parameters=[
            OpenApiParameter(
                name="trainee_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Trainee ID",
            )
        ],
        request=TraineeSerializer,
        responses={200: TraineeSerializer, 404: {"description": "Trainee not found"}, 400: {"description": "Validation error"}},
    )
    def patch(self, request, trainee_id):
        try:
            trainee = Trainee.objects.get(id=trainee_id)
        except Trainee.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        serializer = TraineeSerializer(trainee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    