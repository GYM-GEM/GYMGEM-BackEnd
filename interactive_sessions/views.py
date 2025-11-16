from authenticationAndAuthorization.permissions import HasRole
from interactive_sessions.models import InteractiveSession
from interactive_sessions.serializers import InteractiveSessionSerializer
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from .validators import InteractiveSessionValidator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
# Create your views here.

class InteractiveSessionView(ViewSet):
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'trainer', 'trainee']
    search_fields = ['title', 'description', 'trainer__name', 'trainee__name']
    ordering_fields = ['created_at', 'updated_at', 'start_time']
    ordering = ['-created_at']  # default ordering


    @action(methods=['post'], detail=False, permission_classes=[HasRole(['trainer', 'trainee'])],url_name='create-session', url_path='create')
    def post(self, request):
        serializer = InteractiveSessionSerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.save()
            return Response(InteractiveSessionSerializer(session).data, status=201)
        return Response(serializer.errors, status=400)
    
    @action(methods=['delete'], detail=True,url_name='delete-session', url_path='delete')
    def delete(self, request, pk):
        try:
            session = InteractiveSession.objects.get(pk=pk)
        except InteractiveSession.DoesNotExist:
            return Response({"error": "Interactive session not found."}, status=404)
        serializer = InteractiveSessionSerializer()
        serializer.delete(session)
        return Response(status=204)
    
    @action(methods=['get'], detail=True,permission_classes=[HasRole(['trainer', 'trainee'])], url_name='get-session', url_path='detail')
    def get(self, request, pk):
        try:
            if self.request.user.is_superuser:
                pass
            else:
                InteractiveSessionValidator.validate_participant_belongs_to_session(request.data.get('first_participant'),request.data.get('second_participant'), request.user)
        except ValueError as e: 
            return Response({"error": str(e)}, status=400)
        try:
            session = InteractiveSession.objects.get(pk=pk)
        except InteractiveSession.DoesNotExist:
            return Response({"error": "Interactive session not found."}, status=404)
        
        serializer = InteractiveSessionSerializer(session)
        return Response(serializer.data, status=200)
    
    @action(methods=['put'], detail=True, url_name='update-session', url_path='update')
    def put(self, request, pk):
        try:
            if self.request.user.is_superuser:
                pass
            else:
                InteractiveSessionValidator.validate_participant_belongs_to_session(request.data.get('first_participant'),request.data.get('second_participant'), request.user)
        except ValueError as e: 
            return Response({"error": str(e)}, status=400)
        try:
            session = InteractiveSession.objects.get(pk=pk)
        except InteractiveSession.DoesNotExist:
            return Response({"error": "Interactive session not found."}, status=404)
        
        serializer = InteractiveSessionSerializer(session, data=request.data)
        if serializer.is_valid():
            updated_session = serializer.save()
            return Response(InteractiveSessionSerializer(updated_session).data, status=200)
        return Response(serializer.errors, status=400)
    
    @action(methods=['get'], detail=False, permission_classes=[HasRole(['trainer', 'trainee'])], url_name='list-sessions', url_path='list')
    def list(self, request):
        try:
            user_participants = request.user.get_all_participant_profiles()
            sessions = InteractiveSession.objects.filter(participants__in=user_participants).distinct()
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = InteractiveSessionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = InteractiveSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=200)
    


    @action(methods=['get'], detail=False, url_name='list-all-sessions', url_path='list-all')
    def list_all_sessions(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Only superadmins can access all sessions."}, status=403)

        sessions = InteractiveSession.objects.all()
        sessions = self.filter_queryset(sessions)
        page = self.paginate_queryset(sessions)

        if page is not None:
            serializer = InteractiveSessionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = InteractiveSessionSerializer(sessions, many=True)

        return Response(serializer.data, status=200)