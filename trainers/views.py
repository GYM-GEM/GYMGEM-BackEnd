from django.db.models import Prefetch  # add at top
from decimal import Decimal, InvalidOperation
from drf_spectacular.utils import OpenApiExample
from authenticationAndAuthorization.permissions import HasRole
from profiles.models import Profile
from utils.views import get_profile_id_from_token
from .serializers import (
    TrainerCalendarSlotSerializer,
    TrainerRecordSerializer,
    TrainerSerializer,
    TrainerSpecializationSerializer,
    TrainerExperienceSerializer,
)
from .models import (
    Trainer,
    TrainerCalendarSlot,
    TrainerRecord,
    TrainerSpecialization,
    TrainerExperience,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
# Create your views here.


class TrainerView(APIView):

    permission_classes = [HasRole(["trainer", "trainee","gym"])]

    @extend_schema(
        tags=["Trainers"],
        summary="Create new trainer",
        request=TrainerSerializer,
        responses=TrainerSerializer,
    )
    def post(self, request):
        serializer = TrainerSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    @extend_schema(
        tags=["Trainers"],
        summary="Get trainer profile",
        description="Retrieve trainer profile with specializations, experiences, and calendar slots by profile_id query param.",
        parameters=[
            OpenApiParameter(
                name="profile_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Profile ID of the trainer",
            ),
        ],
        responses={
            200: TrainerSerializer,
            404: {"description": "Trainer or Profile not found"},
        },
    )
    def get(self, request):
        try:
            profile_id = request.query_params.get("profile_id", None)
            my_profile = Profile.objects.get(pk=profile_id, status="active")
            trainer = Trainer.objects.get(profile_id=my_profile)
            serializer = TrainerSerializer(trainer)
            specializations = TrainerSpecialization.objects.filter(trainer=trainer).select_related(
                'specialization'
            )
            experiences = TrainerExperience.objects.filter(trainer=trainer).select_related(
                'trainer'
            )
            calendar_slots = TrainerCalendarSlot.objects.filter(trainer=my_profile).select_related(
                'trainer'
            )
            return Response({
                "trainer": {k: v for k, v in serializer.data.items() if k not in ["zip_code","balance","created_at","updated_at"]},
                "specializations": TrainerSpecializationSerializer(specializations, many=True).data,
                "experiences": TrainerExperienceSerializer(experiences, many=True).data,
                "calendar_slots": TrainerCalendarSlotSerializer(calendar_slots, many=True).data,
            })
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

class MyTrainerView(APIView):

    permission_classes = [HasRole(["trainer"])]

    @extend_schema(
        tags=["Trainers"],
        summary="Get my trainer profile",
        description="Retrieve authenticated trainer's profile with specializations, experiences, and calendar slots.",
        responses={
            200: TrainerSerializer,
            404: {"description": "Trainer or Profile not found"},
        },
    )
    def get(self, request):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(pk=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
            serializer = TrainerSerializer(trainer)
            specializations = TrainerSpecialization.objects.filter(trainer=trainer).select_related(
                'specialization'
            )
            experiences = TrainerExperience.objects.filter(trainer=trainer).select_related(
                'trainer'
            )
            return Response({
                "trainer": serializer.data,
                "specializations": TrainerSpecializationSerializer(specializations, many=True).data,
                "experiences": TrainerExperienceSerializer(experiences, many=True).data,
            })
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

class TrainerListView(APIView):
    permission_classes = [HasRole(["trainer", "trainee"])]

    @extend_schema(
        tags=["Trainers"],
        summary="List all trainers",
        description="List all trainers with optional filtering.",
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Search by trainer name"),
            OpenApiParameter(name="specialization", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Filter by specialization name"),
            OpenApiParameter(name="gender", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, enum=["male", "female"], description="Filter by gender"),
            OpenApiParameter(name="min_price", type=OpenApiTypes.DECIMAL, location=OpenApiParameter.QUERY, description="Minimum hourly rate"),
            OpenApiParameter(name="max_price", type=OpenApiTypes.DECIMAL, location=OpenApiParameter.QUERY, description="Maximum hourly rate"),
            OpenApiParameter(name="location", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, enum=["online", "offline", "both"], description="Filter by service location"),
        ],
        responses=TrainerSerializer(many=True),
    )
    def get(self, request):
        queryset = Trainer.objects.filter(profile_id__status="active").select_related(
            "profile_id",
            "profile_id__account",
        ).prefetch_related(
            Prefetch(
                "trainerspecialization_set",
                queryset=TrainerSpecialization.objects.select_related("specialization"),
            ),
            Prefetch(
                "trainerexperience_set",
                queryset=TrainerExperience.objects.select_related("trainer"),
            ),
        )
        

        # Filtering
        search_query = request.query_params.get("search")
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        specialization_query = request.query_params.get("specialization")
        if specialization_query:
            queryset = queryset.filter(trainerspecialization__specialization__name__icontains=specialization_query)

        gender_query = request.query_params.get("gender")
        if gender_query:
            queryset = queryset.filter(gender__iexact=gender_query)

        min_price = request.query_params.get("min_price")
        if min_price:
            try:
                min_price_dec = Decimal(min_price)
                queryset = queryset.filter(rate__gte=min_price_dec)
            except (InvalidOperation, TypeError):
                pass  # ignore invalid min_price

        max_price = request.query_params.get("max_price")
        if max_price:
            try:
                max_price_dec = Decimal(max_price)
                queryset = queryset.filter(rate__lte=max_price_dec)
            except (InvalidOperation, TypeError):
                pass  # ignore invalid max_price

        location_query = request.query_params.get("location")
        if location_query:
            queryset = queryset.filter(trainerspecialization__service_location__iexact=location_query)
        
        queryset = queryset.distinct()

        trainers_data = []
        for trainer in queryset:
            base = TrainerSerializer(trainer).data
            base["id"] = trainer.pk  # ensure id is present
            base["specializations"] = TrainerSpecializationSerializer(
                trainer.trainerspecialization_set.all(), many=True
            ).data
            base["experiences"] = TrainerExperienceSerializer(
                trainer.trainerexperience_set.all(), many=True
            ).data
            base["calendar_slots"] = TrainerCalendarSlotSerializer(
                TrainerCalendarSlot.objects.filter(trainer=trainer.profile_id), many=True
            ).data
            trainers_data.append(base)

        return Response(trainers_data)


class TrainerUpdateView(APIView):
    permission_classes = [HasRole(["trainer"])]

    @extend_schema(
        tags=["Trainers"],
        summary="Update trainer",
        description="Update an existing trainer",
        parameters=[
            OpenApiParameter(
                name="trainer_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Trainer ID",
            ),
        ],
        request=TrainerSerializer,
        responses={
            200: TrainerSerializer,
            404: {"description": "Trainer not found"},
            400: {"description": "Validation error"},
        },
    )
    def put(self, request):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(id=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        serializer = TrainerSerializer(
            trainer, data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @extend_schema(
        tags=["Trainers"],
        summary="Delete trainer",
        description="Delete the authenticated trainer profile",
        responses={
            204: {"description": "Trainer deleted"},
            404: {"description": "Trainer not found"},
        },
    )
    def delete(self, request):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(id=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        trainer.delete()
        return Response(status=204)


class TrainerSpecializationView(APIView):
    permission_classes = [HasRole(["trainer"])]

    @extend_schema(
        tags=["Trainers"],
        summary="List my trainer specializations",
        description="Get all specializations for the authenticated trainer. Each specialization includes the area of expertise, years of experience, service location (online/offline/both), optional description, and timestamps.",
        responses={200: TrainerSpecializationSerializer(many=True)},
    )
    def get(self, request):
        profile_id = get_profile_id_from_token(request)
        my_profile = Profile.objects.get(pk=profile_id)
        trainer = Trainer.objects.get(profile_id=my_profile)
        specializations = TrainerSpecialization.objects.filter(trainer=trainer).select_related(
            'trainer',
            'trainer__profile_id',
            'specialization'
        )
        serializer = TrainerSpecializationSerializer(specializations, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Trainers"],
        summary="Create new trainer specialization",
        description="Create a new trainer specialization for the authenticated trainer. Includes specialization details, years of experience, service location, and an optional description.",
        request=TrainerSpecializationSerializer,
        responses={
            201: TrainerSpecializationSerializer,
            400: {"description": "Validation error"},
        },
        examples=[
            OpenApiExample(
                name="Create Specialization",
                description="Example of creating a new specialization for a trainer",
                value={
                    "specialization": 1,
                    "years_of_experience": 5,
                    "service_location": "both",
                    "description": "Specialized in strength training and muscle building with focus on powerlifting techniques"
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = TrainerSpecializationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class TrainerSpecializationUpdateView(APIView):
    permission_classes = [HasRole(["trainer"])]

    @extend_schema(
        tags=["Trainers"],
        summary="Update trainer specialization",
        description="Update an existing trainer specialization. You can update years of experience, service location (online/offline/both), and the description. Timestamps are automatically managed.",
        parameters=[
            OpenApiParameter(
                name="specialization_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Specialization ID",
            ),
        ],
        request=TrainerSpecializationSerializer,
        responses={
            200: TrainerSpecializationSerializer,
            404: {"description": "TrainerSpecialization not found"},
            400: {"description": "Validation error"},
        },
    )
    def put(self, request, specialization_id):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(pk=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
            specialization = TrainerSpecialization.objects.get(id=specialization_id, trainer=trainer)
        except TrainerSpecialization.DoesNotExist:
            return Response({"error": "TrainerSpecialization not found"}, status=404)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        serializer = TrainerSpecializationSerializer(
            specialization, data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @extend_schema(
        tags=["Trainers"],
        summary="Delete trainer specialization",
        description="Delete an existing trainer specialization",
        parameters=[
            OpenApiParameter(
                name="specialization_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Specialization ID",
            ),
        ],
        responses={
            204: {"description": "TrainerSpecialization deleted"},
            404: {"description": "TrainerSpecialization not found"},
        },
    )
    def delete(self, request, specialization_id):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(pk=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
            specialization = TrainerSpecialization.objects.get(id=specialization_id, trainer=trainer)
        except TrainerSpecialization.DoesNotExist:
            return Response({"error": "TrainerSpecialization not found"}, status=404)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        specialization.delete()
        return Response(status=204)

    @extend_schema(
        tags=["Trainers"],
        summary="Partially update trainer specialization",
        description="Partially update an existing trainer specialization",
        parameters=[
            OpenApiParameter(
                name="specialization_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Specialization ID",
            ),
        ],
        request=TrainerSpecializationSerializer,
        responses={
            200: TrainerSpecializationSerializer,
            404: {"description": "TrainerSpecialization not found"},
            400: {"description": "Validation error"},
        },
    )
    def patch(self, request, specialization_id):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(pk=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
            specialization = TrainerSpecialization.objects.get(id=specialization_id, trainer=trainer)
        except TrainerSpecialization.DoesNotExist:
            return Response({"error": "TrainerSpecialization not found"}, status=404)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        serializer = TrainerSpecializationSerializer(
            specialization, data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class TrainerExperienceView(APIView):
    permission_classes = [HasRole(["trainer"])]

    @extend_schema(
        tags=["Trainers"],
        summary="List my trainer experiences",
        description="Get all work experiences for the authenticated trainer. Includes timestamps showing when each experience was created and last updated.",
        responses={200: TrainerExperienceSerializer(many=True)},
    )
    def get(self, request):
        profile_id = get_profile_id_from_token(request)
        my_profile = Profile.objects.get(pk=profile_id)
        trainer = Trainer.objects.get(profile_id=my_profile)
        experiences = TrainerExperience.objects.filter(trainer=trainer).select_related(
            'trainer',
            'trainer__profile_id'
        )
        serializer = TrainerExperienceSerializer(experiences, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Trainers"],
        summary="Create new trainer experience",
        description="Create a new work experience entry for the authenticated trainer. Include workplace, position, dates, and description. Timestamps are automatically tracked.",
        request=TrainerExperienceSerializer,
        responses={
            201: TrainerExperienceSerializer,
            400: {"description": "Validation error"},
        },
        examples=[
            OpenApiExample(
                name="Create Experience (Current Job)",
                description="Example for a current position (no end date)",
                value={
                    "work_place": "Gold's Gym",
                    "position": "Senior Personal Trainer",
                    "start_date": "2022-01-15",
                    "end_date": None,
                    "description": "Leading personal training programs and mentoring junior trainers"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Create Experience (Past Job)",
                description="Example for a previous position with end date",
                value={
                    "work_place": "Fitness First",
                    "position": "Personal Trainer",
                    "start_date": "2019-03-01",
                    "end_date": "2021-12-31",
                    "description": "Provided one-on-one training sessions and group classes"
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        data = request.data.copy()
        end_date = request.data.get("end_date")

        if end_date is not None and (isinstance(end_date, str) and len(end_date.strip()) == 0):
            data["end_date"] = None

        serializer = TrainerExperienceSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class TrainerExperienceUpdateView(APIView):
    permission_classes = [HasRole(["trainer"])]

    @extend_schema(
        tags=["Trainers"],
        summary="Update trainer experience",
        description="Update an existing work experience entry. You can modify workplace, position, dates, and description. The updated_at timestamp is automatically updated.",
        parameters=[
            OpenApiParameter(
                name="experience_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Experience ID",
            ),
        ],
        request=TrainerExperienceSerializer,
        responses={
            200: TrainerExperienceSerializer,
            404: {"description": "TrainerExperience not found"},
            400: {"description": "Validation error"},
        },
    )
    def put(self, request, experience_id):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(pk=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
            experience = TrainerExperience.objects.get(id=experience_id, trainer=trainer)
        except TrainerExperience.DoesNotExist:
            return Response({"error": "TrainerExperience not found"}, status=404)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        serializer = TrainerExperienceSerializer(
            experience, data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @extend_schema(
        tags=["Trainers"],
        summary="Delete trainer experience",
        description="Delete an existing trainer experience",
        parameters=[
            OpenApiParameter(
                name="experience_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Experience ID",
            ),
        ],
        responses={
            204: {"description": "TrainerExperience deleted"},
            404: {"description": "TrainerExperience not found"},
        },
    )
    def delete(self, request, experience_id):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(pk=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
            experience = TrainerExperience.objects.get(id=experience_id, trainer=trainer)
        except TrainerExperience.DoesNotExist:
            return Response({"error": "TrainerExperience not found"}, status=404)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        experience.delete()
        return Response(status=204)

    @extend_schema(
        tags=["Trainers"],
        summary="Partially update trainer experience",
        description="Partially update an existing trainer experience",
        parameters=[
            OpenApiParameter(
                name="experience_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Experience ID",
            ),
        ],
        request=TrainerExperienceSerializer,
        responses={
            200: TrainerExperienceSerializer,
            404: {"description": "TrainerExperience not found"},
            400: {"description": "Validation error"},
        },
    )
    def patch(self, request, experience_id):
        try:
            profile_id = get_profile_id_from_token(request)
            my_profile = Profile.objects.get(pk=profile_id)
            trainer = Trainer.objects.get(profile_id=my_profile)
            experience = TrainerExperience.objects.get(id=experience_id, trainer=trainer)
        except TrainerExperience.DoesNotExist:
            return Response({"error": "TrainerExperience not found"}, status=404)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        serializer = TrainerExperienceSerializer(
            experience, data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class TrainerCalendarSlotView(APIView):
    @extend_schema(
        tags=["Calendar"],
        summary="Create calendar slot",
        description=(
            "Create a new 30-minute trainer calendar slot. End time is auto-set "
            "to start time + 30 minutes and overlapping slots are rejected."
        ),
        operation_id="calendar_slots_create",
        request=TrainerCalendarSlotSerializer,
        responses={201: TrainerCalendarSlotSerializer, 400: {"description": "Validation error"}},
        examples=[
            OpenApiExample(
                name="Create slot (UTC)",
                description="Send ISO 8601 date-time string; end time auto-calculated.",
                value={
                    "slot_start_time": "2025-12-20T20:00:00Z"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Create slot (+02:00)",
                description="Timezone-aware example with offset.",
                value={
                    "slot_start_time": "2025-12-20T20:00:00+02:00"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Provide explicit end time",
                description="Optional end time if not 30 minutes.",
                value={
                    "slot_start_time": "2025-12-20T20:00:00Z",
                    "slot_end_time": "2025-12-20T20:30:00Z"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Admin creates for trainer",
                description="Superuser may specify trainer_profile_id to create for another trainer.",
                value={
                    "slot_start_time": "2025-12-21T14:00:00Z",
                    "trainer_profile_id": 42
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = TrainerCalendarSlotSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @extend_schema(
        tags=["Calendar"],
        summary="List my calendar slots",
        description="List all calendar slots for the authenticated trainer profile.",
        operation_id="calendar_slots_list_my",
        responses=TrainerCalendarSlotSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        profile = get_object_or_404(Profile, id=get_profile_id_from_token(request))
        slots = TrainerCalendarSlot.objects.filter(trainer=profile).select_related('trainer')
        serializer = TrainerCalendarSlotSerializer(slots, many=True)
        return Response(serializer.data)
    
class TrainerCalendarSlotDetailView(APIView):
    @extend_schema(
        tags=["Calendar"],
        summary="List trainer's calendar slots",
        description="List all calendar slots for a given trainer profile ID.",
        operation_id="calendar_slots_list_trainer",
        parameters=[
            OpenApiParameter(
                name="profile_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Trainer Profile ID",
            ),
        ],
        responses=TrainerCalendarSlotSerializer(many=True),
    )
    def get(self, request, profile_id, *args, **kwargs):
        profile = get_object_or_404(Profile, id=profile_id)
        slots = TrainerCalendarSlot.objects.filter(trainer=profile).select_related('trainer')
        serializer = TrainerCalendarSlotSerializer(slots, many=True)
        return Response(serializer.data)


class TrainerCalendarSlotDeleteView(APIView):
    @extend_schema(
        tags=["Calendar"],
        summary="Delete calendar slot",
        description="Delete an existing trainer calendar slot by ID.",
        operation_id="calendar_slots_delete",
        parameters=[
            OpenApiParameter(
                name="slot_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Calendar Slot ID",
            ),
        ],
        responses={204: {"description": "Calendar slot deleted"}, 404: {"description": "Calendar slot not found"}},
    )
    def delete(self, request, slot_id, *args, **kwargs):
        slot = get_object_or_404(TrainerCalendarSlot, id=slot_id)
        slot.delete()
        return Response(status=204)
    
    
@extend_schema_view(
    list=extend_schema(
        tags=["Trainer Records"],
        summary="List trainer records",
        description="Retrieve a list of trainer records for the authenticated trainer.",
        responses={200: TrainerRecordSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Trainer Records"],
        summary="Create a trainer record",
        description="Create a new trainer record for the authenticated trainer.",
        request=TrainerRecordSerializer,
        responses={201: TrainerRecordSerializer, 400: {"description": "Validation error"}},
    ),
    retrieve=extend_schema(
        tags=["Trainer Records"],
        summary="Retrieve a trainer record",
        description="Retrieve a specific trainer record by ID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainer Record ID",
            )
        ],
        responses={200: TrainerRecordSerializer, 404: {"description": "Not found"}},
    ),
    update=extend_schema(
        tags=["Trainer Records"],
        summary="Update a trainer record",
        description="Update an existing trainer record.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainer Record ID",
            )
        ],
        request=TrainerRecordSerializer,
        responses={200: TrainerRecordSerializer, 400: {"description": "Validation error"}, 404: {"description": "Not found"}},
    ),
    partial_update=extend_schema(
        tags=["Trainer Records"],
        summary="Partially update a trainer record",
        description="Partially update an existing trainer record.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainer Record ID",
            )
        ],
        request=TrainerRecordSerializer,
        responses={200: TrainerRecordSerializer, 400: {"description": "Validation error"}, 404: {"description": "Not found"}},
    ),
    destroy=extend_schema(
        tags=["Trainer Records"],
        summary="Delete a trainer record",
        description="Delete an existing trainer record.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Trainer Record ID",
            )
        ],
        responses={204: {"description": "Deleted"}, 404: {"description": "Not found"}},
    ),
)
class TrainerRecordView(ModelViewSet):
    queryset = TrainerRecord.objects.all()
    serializer_class = TrainerRecordSerializer
    permission_classes = [HasRole(["trainer"])]

    def get_queryset(self):
        profile_id = get_profile_id_from_token(self.request)
        return TrainerRecord.objects.filter(trainer__profile_id=profile_id)

    def perform_create(self, serializer):
        profile_id = get_profile_id_from_token(self.request)
        trainer = Profile.objects.get(id=profile_id).get_profile_data
        serializer.save(trainer=trainer)