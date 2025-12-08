from authenticationAndAuthorization.permissions import HasRole
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from interactive_sessions.models import InteractiveSession
from .serializers import InteractiveSessionSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import django_filters.rest_framework as filters

class InteractiveSessionFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='status', lookup_expr='exact')
    first_participant = filters.NumberFilter(field_name='first_participant__id')
    second_participant = filters.NumberFilter(field_name='second_participant__id')
    scheduled_slot = filters.NumberFilter(field_name='scheduled_at__id')
    created_from = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = InteractiveSession
        fields = ['status', 'first_participant', 'second_participant', 'scheduled_slot', 'created_from', 'created_to']

class InteractiveSessionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        tags=["Interactive Sessions"],
        summary="List interactive sessions",
        description="Get a list of interactive sessions with optional filtering, searching, and ordering.",
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Filter by status'),
            OpenApiParameter('first_participant', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filter by first participant ID'),
            OpenApiParameter('second_participant', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filter by second participant ID'),
            OpenApiParameter('scheduled_slot', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description='Filter by scheduled slot ID'),
            OpenApiParameter('created_from', OpenApiTypes.DATETIME, OpenApiParameter.QUERY, required=False, description='Created at from (>=)'),
            OpenApiParameter('created_to', OpenApiTypes.DATETIME, OpenApiParameter.QUERY, required=False, description='Created at to (<=)'),
            OpenApiParameter('search', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Search title, description, trainer/trainee name'),
            OpenApiParameter('ordering', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description='Order by created_at, updated_at, scheduled_at'),
        ],
        responses={200: InteractiveSessionSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Interactive Sessions"],
        summary="Retrieve interactive session",
        responses={200: InteractiveSessionSerializer},
    ),
    create=extend_schema(
        tags=["Interactive Sessions"],
        summary="Create interactive session (trainer only)",
        request=InteractiveSessionSerializer,
        responses={201: InteractiveSessionSerializer, 400: {"description": "Validation error"}},
    ),
    update=extend_schema(
        tags=["Interactive Sessions"],
        summary="Update interactive session (trainer only)",
        request=InteractiveSessionSerializer,
        responses={200: InteractiveSessionSerializer, 400: {"description": "Validation error"}},
    ),
    partial_update=extend_schema(
        tags=["Interactive Sessions"],
        summary="Partially update interactive session (trainer only)",
        request=InteractiveSessionSerializer,
        responses={200: InteractiveSessionSerializer, 400: {"description": "Validation error"}},
    ),
    destroy=extend_schema(
        tags=["Interactive Sessions"],
        summary="Delete interactive session (trainer only)",
        responses={204: {"description": "Session deleted"}},
    ),
)
class InteractiveSessionView(viewsets.ModelViewSet):
    """
    ViewSet for managing interactive sessions between trainers and trainees.
    
    list: Get all interactive sessions with optional filtering, searching, and ordering.
    create: Create a new interactive session (trainer only).
    retrieve: Get details of a specific interactive session.
    update: Update an interactive session (trainer only).
    partial_update: Partially update an interactive session (trainer only).
    destroy: Delete an interactive session (trainer only).
    """
    queryset = InteractiveSession.objects.all().select_related(
        'scheduled_at',
        'scheduled_at__trainer'  # If TrainerCalendarSlot has trainer FK
    ).prefetch_related(
        'first_participant',  # ManyToMany
        'second_participant',  # ManyToMany
        'first_participant__account',
        'second_participant__account'
    ).order_by('id')
    serializer_class = InteractiveSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = InteractiveSessionPagination
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InteractiveSessionFilter
    search_fields = [
        'session_title',
        'description',
        'status',
        'first_participant__account__username',
        'second_participant__account__username',
    ]
    ordering_fields = ['created_at', 'updated_at', 'scheduled_at']
    ordering = ['-created_at']

    def get_permissions(self):
        perms = super().get_permissions()
        if self.action in {"create", "update", "partial_update", "destroy"}:
            perms.insert(0, HasRole(['trainer']))  # remove the trailing ()
        return perms

    # Methods inherit schema from extend_schema_view above.
