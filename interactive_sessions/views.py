from authenticationAndAuthorization.permissions import HasRole
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from interactive_sessions.models import InteractiveSession
from .serializers import InteractiveSessionSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
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
    queryset = InteractiveSession.objects.all().order_by('id')
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

    @swagger_auto_schema(
        operation_description="Get a list of interactive sessions",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('first_participant', openapi.IN_QUERY, description="Filter by first participant ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('second_participant', openapi.IN_QUERY, description="Filter by second participant ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in title, description, trainer name, trainee name", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by: created_at, updated_at, start_time (prefix with '-' for descending)", type=openapi.TYPE_STRING),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new interactive session (trainer only)"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a specific interactive session"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an interactive session (trainer only)"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update an interactive session (trainer only)"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an interactive session (trainer only)"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
