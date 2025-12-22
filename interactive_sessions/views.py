from datetime import timedelta
from django.utils import timezone
from profiles.models import Profile
from rest_framework.views import APIView
from rest_framework.response import Response
from interactive_sessions.models import InteractiveSession
from interactive_sessions.serializers import InteractiveSessionSerializer
from utils.views import get_profile_id_from_token
from .validators import InteractiveSessionValidator
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db import transaction
from trainers.models import TrainerCalendarSlot
from authenticationAndAuthorization.permissions import HasRole
from django.db import models

class SessionRequestView(APIView):
    permission_classes = [HasRole(['trainee'])]
    @extend_schema(
        tags=["Interactive Sessions"],
        summary="Request an interactive session",
        description="Trainee requests an interactive session with a trainer at a specified time slot.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "trainer_id": {"type": "integer", "description": "Profile ID of the trainer"},
                    "time_slot_id": {"type": "integer", "description": "ID of the trainer's calendar slot"},
                    "session_title": {"type": "string", "description": "Title of the session"},
                    "description": {"type": "string", "description": "Description of the session"}
                },
                "required": ["trainer_id", "time_slot_id", "session_title", "description"]
            }
        },
        responses={
            201: InteractiveSessionSerializer,
            400: {"description": "Validation error"}
        }
    )
    def post(self, request):
        trainer = request.data.get('trainer_id')
        trainee = get_profile_id_from_token(request)  # Assume this function extracts profile ID from request
        time_slot = request.data.get('time_slot_id')
        session_title = request.data.get('session_title')
        description = request.data.get('description')
        try:
            InteractiveSessionValidator.time_slot_belongs_to_trainer_and_available(time_slot, trainer)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        
        # Prevent time conflicts: same start time for any active session (requested/pending/scheduled)
        try:
            slot_obj = TrainerCalendarSlot.objects.only('slot_start_time').get(pk=time_slot)
        except TrainerCalendarSlot.DoesNotExist:
            return Response({'error': 'Selected time slot does not exist.'}, status=400)
        if timezone.now() + timedelta(hours=6) > slot_obj.slot_start_time :
            return Response({'error': 'Cannot request a session for a time slot that starts in less than 6 hours.'}, status=400)
        # Prevent multiple active sessions with the same trainer
        has_trainer_conflict = InteractiveSession.objects.filter(
            trainee__id=trainee,
            trainer__id=trainer,
            status__in=['requested', 'scheduled'],
        ).count() 
        if has_trainer_conflict > 2:
            return Response({'error': 'You already have three active sessions with this trainer. Complete or cancel it before requesting another.'}, status=400)
        has_time_conflict = InteractiveSession.objects.filter(
            trainee__id=trainee,
            status__in=['requested', 'scheduled'],
            scheduled_at__slot_start_time=slot_obj.slot_start_time,
        ).exists()
        if has_time_conflict:
            return Response({'error': 'You already have another active session at this start time.'}, status=400)

        # Prevent duplicate requests for the exact same slot
        if InteractiveSession.objects.filter(
            scheduled_at_id=time_slot,
            status__in=['requested', 'scheduled'],
            trainee__id=trainee
        ).count() > 2:
            return Response({'error': 'You already have three sessions scheduled/requested for this slot.'}, status=400)
        trainer_profile = Profile.objects.get(pk=trainer).get_profile_data
        serializer = InteractiveSessionSerializer(data={
            'trainer': trainer,
            'trainee': trainee,
            'scheduled_at': time_slot,
            'session_title': session_title,
            'description': description,
            'fees': trainer_profile.rate,
            'status': 'requested'
        }, context={'request': request})
        try:
            trainee = Profile.objects.get(pk=get_profile_id_from_token(request)).get_profile_data
        except Profile.DoesNotExist:
            return Response({'error': 'Trainee profile not found.'}, status=404)
        try:
            with transaction.atomic():
                # Atomically reserve the slot if available
                updated = TrainerCalendarSlot.objects.filter(id=time_slot, is_available=True).update(is_available=False)
                if updated == 0:
                    return Response({'error': 'Selected time slot is no longer available.'}, status=400)

                if serializer.is_valid():
                    session = serializer.save()
                    trainee.balance -= trainer_profile.rate
                    trainee.save()
                    out = InteractiveSessionSerializer(session, context={'request': request}).data
                    return Response(out, status=201)
                else:
                    # Roll back slot reservation if session creation fails
                    TrainerCalendarSlot.objects.filter(id=time_slot).update(is_available=True)
                    return Response(serializer.errors, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
    
class SessionAcceptView(APIView):
    
    permission_classes = [HasRole(['trainer'])]
    @extend_schema(
        tags=["Interactive Sessions"],
        summary="Accept an interactive session request",
        description="Trainer accepts a requested interactive session.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the interactive session"
            )
        ],
        responses={
            200: InteractiveSessionSerializer,
            404: {"description": "Session not found"}
        }
    )
    def post(self, request, session_id):
        try:
            session = InteractiveSession.objects.get(id=session_id)
        except InteractiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        if session.status != 'requested':
            return Response({'error': 'Only requested sessions can be accepted'}, status=400)
        if session.scheduled_at.slot_start_time - timezone.now() < timedelta(hours=1):
            return Response({'error': 'Cannot accept a session less than 1 hour before its start time.'}, status=400)
        with transaction.atomic():
            session.status = 'scheduled'  # Update status to pending upon acceptance
            session.save()
            serializer = InteractiveSessionSerializer(session, context={'request': request})
            return Response(serializer.data, status=200)

class SessionStartView(APIView):
    permission_classes = [HasRole(['trainer'])]
    @extend_schema(
        tags=["Interactive Sessions"],
        summary="Start an interactive session",
        description="Trainer starts a scheduled interactive session.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the interactive session"
            )
        ],
        responses={
            200: InteractiveSessionSerializer,
            404: {"description": "Session not found"},
            400: {"description": "Invalid session status for starting"}
        }
    )
    def post(self, request, session_id):
        try:
            session = InteractiveSession.objects.get(id=session_id)
        except InteractiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        if session.status != 'scheduled':
            return Response({'error': 'Only scheduled sessions can be started'}, status=400)
        if timezone.now() < session.scheduled_at.slot_start_time - timedelta(minutes=5):
            return Response({'error': 'Cannot start the session more than 5 minutes before its scheduled time.'}, status=400)
        with transaction.atomic():
            session.status = 'live'  # Update status to in_progress
            session.save()
            serializer = InteractiveSessionSerializer(session, context={'request': request})
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
class SessionCompleteView(APIView):
    def post(self, request, session_id):
        try:
            session = InteractiveSession.objects.get(id=session_id)
        except InteractiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        if session.status != 'scheduled':
            return Response({'error': 'Only scheduled sessions can be completed'}, status=400)
        with transaction.atomic():
            trainer = session.trainer.get_profile_data
            session.status = 'completed'  # Update status to completed
            session.save()
            trainer.balance += int(session.fees) * 0.92
            trainer.save()
        serializer = InteractiveSessionSerializer(session, context={'request': request})
        return Response(serializer.data, status=200)

class SessionCancelView(APIView):
    permission_classes = [HasRole(['trainee'])]
    @extend_schema(
        tags=["Interactive Sessions"],  
        summary="Cancel an interactive session",
        description="Trainee cancels a scheduled or pending interactive session.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the interactive session"
            )
        ],
        responses={
            200: InteractiveSessionSerializer,
            404: {"description": "Session not found"},
            400: {"description": "Invalid session status for cancellation"}
        }
    )
    def post(self, request, session_id):
        try:
            session = InteractiveSession.objects.get(id=session_id)
            trainer = session.trainer.get_profile_data
            trainee = session.trainee.get_profile_data
        except InteractiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        with transaction.atomic():
            if session.status not in ['scheduled', 'pending', 'requested']:
                return Response({'error': 'Only scheduled, pending, or requested sessions can be canceled'}, status=400)
            session.status = 'canceled'  # Update status to canceled
            if session.status == 'scheduled':
                trainee.balance += int(session.fees * 0.5)
                trainer.balance += int(session.fees * 0.25)
                trainee.save()
                trainer.save()
            elif session.status == 'requested' and session.scheduled_at.slot_start_time - timezone.now() > timedelta(hours=6):
                trainee.balance += int(session.fees * 0.75)
                trainee.save()
            elif session.status == 'requested':
                trainee.balance += int(session.fees)
                trainee.save()
            session.save()
            TrainerCalendarSlot.objects.filter(id=session.scheduled_at.id).update(is_available=True)
            serializer = InteractiveSessionSerializer(session, context={'request': request})
        return Response(serializer.data, status=200)  

class SessionAbortView(APIView):
    permission_classes = [HasRole(['trainer'])]
    @extend_schema(
        tags=["Interactive Sessions"],
        summary="Abort an interactive session",
        description="Trainer aborts a scheduled interactive session.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the interactive session"
            )
        ],
        responses={
            200: InteractiveSessionSerializer,
            404: {"description": "Session not found"},
            400: {"description": "Invalid session status for abortion"}
        }
    )
    def post(self, request, session_id):
        try:
            session = InteractiveSession.objects.get(id=session_id)
        except InteractiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        with transaction.atomic():
            if session.status != 'scheduled':
                return Response({'error': 'Only scheduled sessions can be aborted'}, status=400)
            session.status = 'aborted'  # Update status to aborted
            trainee = session.trainee.get_profile_data
            trainee.balance += int(session.fees)
            session.save()
            TrainerCalendarSlot.objects.filter(id=session.scheduled_at.id).update(is_available=True)
            serializer = InteractiveSessionSerializer(session, context={'request': request})
        return Response(serializer.data, status=200)

class SessionRejectView(APIView):
    permission_classes = [HasRole(['trainer'])]
    @extend_schema(
        tags=["Interactive Sessions"],
        summary="Reject an interactive session request",
        description="Trainer rejects a requested interactive session.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID of the interactive session"
            )
        ],
        responses={
            200: InteractiveSessionSerializer,
            404: {"description": "Session not found"},
            400: {"description": "Invalid session status for rejection"}
        }
    )
    def post(self, request, session_id):
        try:
            session = InteractiveSession.objects.get(id=session_id)
        except InteractiveSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)
        with transaction.atomic():
            if session.status != 'requested':
                return Response({'error': 'Only requested sessions can be rejected'}, status=400)
            session.status = 'rejected'  # Update status to rejected
            session.save()
            TrainerCalendarSlot.objects.filter(id=session.scheduled_at.id).update(is_available=True)
            serializer = InteractiveSessionSerializer(session, context={'request': request})
        return Response(serializer.data, status=200)

class SessionListView(APIView):
    permission_classes = [HasRole(['trainer', 'trainee'])]
    @extend_schema(
        tags=["Interactive Sessions"],
        summary="List interactive sessions for the user",
        description="Retrieve all interactive sessions associated with the requesting user.",
        responses={
            200: InteractiveSessionSerializer(many=True),
        }
    )
    def get(self, request):
        profile_id = get_profile_id_from_token(request)
        if Profile.objects.filter(id=profile_id, profile_type='trainer').exists():
            role = 'trainer'
        else:
            role = 'trainee'
        try:
            if role == 'trainer':
                sessions = InteractiveSession.objects.filter(
                    trainer__id=profile_id
                ).select_related('scheduled_at', 'trainer', 'trainee').order_by('-scheduled_at__slot_start_time').annotate(
                    trainee_name=models.F('trainee__trainee__name'),
                    starting_time=models.F('scheduled_at__slot_start_time')
                )
            else:
                sessions = InteractiveSession.objects.filter(
                    trainee__id=profile_id
                ).select_related('scheduled_at', 'trainer', 'trainee').order_by('-scheduled_at__slot_start_time').annotate(
                    trainer_name=models.F('trainer__trainer__name'),
                    starting_time=models.F('scheduled_at__slot_start_time')
                )
            serializer = InteractiveSessionSerializer(sessions, many=True, context={'request': request})
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)