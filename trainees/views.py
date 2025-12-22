from profiles.models import Profile
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.views import get_profile_id_from_token
from .models import Trainee, TraineeRecords
from .serializers import TraineeSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .serializers import TraineeRecordSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
# Create your views here.
class TraineeView(APIView):

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
        request=TraineeSerializer,
        responses={200: TraineeSerializer, 404: {"description": "Trainee not found"}, 400: {"description": "Validation error"}},
    )
    def put(self, request):
        try:
            trainee_id = get_profile_id_from_token(request)
            trainee = Profile.objects.get(id=trainee_id).get_profile_data
        except Profile.DoesNotExist:
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
        request=TraineeSerializer,
        responses={200: TraineeSerializer, 404: {"description": "Trainee not found"}, 400: {"description": "Validation error"}},
    )
    def patch(self, request, trainee_id):
        try:
            trainee = Profile.objects.get(id=trainee_id).get_profile_data
        except Profile.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        serializer = TraineeSerializer(trainee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
class TraineeDetailView(APIView):
    @extend_schema(
        tags=["Trainees"],
        summary="Retrieve trainee details",
        description="Get details of the authenticated trainee",
        responses={200: TraineeSerializer, 404: {"description": "Trainee not found"}},
    )
    def get(self, request):
        try:
            trainee_id = get_profile_id_from_token(request)
            trainee = Profile.objects.get(id=trainee_id).get_profile_data
        except Profile.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        serializer = TraineeSerializer(trainee)
        return Response(serializer.data)
    
@extend_schema_view(
    list=extend_schema(
        tags=["Trainee Records"],
        summary="List trainee records",
        description="Retrieve a list of trainee records for the authenticated trainee.",
        responses={200: TraineeRecordSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Trainee Records"],
        summary="Create a trainee record",
        description="Create a new trainee record for the authenticated trainee.",
        request=TraineeRecordSerializer,
        responses={201: TraineeRecordSerializer, 400: {"description": "Validation error"}},
    ),
    retrieve=extend_schema(
        tags=["Trainee Records"],
        summary="Retrieve a trainee record",
        description="Retrieve a specific trainee record by ID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainee Record ID",
            )
        ],
        responses={200: TraineeRecordSerializer, 404: {"description": "Not found"}},
    ),
    update=extend_schema(
        tags=["Trainee Records"],
        summary="Update a trainee record",
        description="Update an existing trainee record.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainee Record ID",
            )
        ],
        request=TraineeRecordSerializer,
        responses={200: TraineeRecordSerializer, 400: {"description": "Validation error"}, 404: {"description": "Not found"}},
    ),
    partial_update=extend_schema(
        tags=["Trainee Records"],
        summary="Partially update a trainee record",
        description="Partially update an existing trainee record.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainee Record ID",
            )
        ],
        request=TraineeRecordSerializer,
        responses={200: TraineeRecordSerializer, 400: {"description": "Validation error"}, 404: {"description": "Not found"}},
    ),
    destroy=extend_schema(
        tags=["Trainee Records"],
        summary="Delete a trainee record",
        description="Delete an existing trainee record.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainee Record ID",
            )
        ],
        responses={204: {"description": "Deleted"}, 404: {"description": "Not found"}},
    ),
)
class TraineeRecordViewSet(ModelViewSet):
    queryset = TraineeRecords.objects.all()
    serializer_class = TraineeRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        trainee_id = get_profile_id_from_token(self.request)
        return TraineeRecords.objects.filter(trainee_id__profile_id=trainee_id)

    def perform_create(self, serializer):
        trainee_id = get_profile_id_from_token(self.request)
        trainee = Profile.objects.get(id=trainee_id).get_profile_data
        serializer.save(trainee_id=trainee) 
    