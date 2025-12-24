from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from utils.views import get_profile_id_from_token
from profiles.models import Profile
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class MessagePagination(PageNumberPagination):
    """
    Pagination class for messages.
    Returns 50 messages per page to optimize performance for long conversations.
    """
    page_size = 50
    page_size_query_param = 'page_size'  # Allow client to override: ?page_size=100
    max_page_size = 500  # Maximum allowed page size to prevent abuse

@extend_schema_view(
    list=extend_schema(
        tags=['Chat'],
        summary="List user's conversations",
        description="Retrieve all conversations where the authenticated user is a participant. Supports filtering by participant username.",
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search conversations by participant username (case-insensitive partial match)',
                required=False,
                examples=[
                    OpenApiExample(
                        'Search by username',
                        value='john',
                        description='Find conversations with users whose username contains "john"'
                    )
                ]
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Chat'],
        summary="Get conversation details",
        description="Retrieve details of a specific conversation. User must be a participant.",
    ),
    create=extend_schema(
        tags=['Chat'],
        summary="Create conversation (use start action instead)",
        description="This endpoint is available but 'start' action is recommended for creating conversations.",
    ),
    update=extend_schema(
        tags=['Chat'],
        summary="Update conversation",
        description="Update conversation details. User must be a participant.",
    ),
    partial_update=extend_schema(
        tags=['Chat'],
        summary="Partially update conversation",
        description="Partially update conversation details. User must be a participant.",
    ),
    destroy=extend_schema(
        tags=['Chat'],
        summary="Delete conversation",
        description="Delete a conversation. User must be a participant.",
    ),
)
class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def _get_current_profile(self):
        profile_id = get_profile_id_from_token(self.request)
        if not profile_id:
            raise ValidationError('current_profile is missing in token')
        return get_object_or_404(Profile, id=profile_id)

    def get_queryset(self):
        """
        Filter conversations to only show those where the user is a participant.
        Supports optional search parameter to filter by participant username.
        """
        profile = self._get_current_profile()
        queryset = Conversation.objects.filter(
            participants=profile
        ).prefetch_related(
            'messages',  # Fetch all messages in one query
            'messages__sender',  # Fetch senders in one query
            'participants'  # Fetch participants in one query
        )
        # Optional search by participant username
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(participants__account__username__icontains=search) & 
                ~Q(participants__account__username=profile.account.username if profile.account else None)
            ).distinct()
        return queryset

    @extend_schema(
        tags=['Chat'],
        summary="Start a new conversation",
        description="Start a new conversation with another user. Returns existing conversation if one already exists between the two users.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'user2': {
                        'type': 'integer',
                        'description': 'ID of the user to start conversation with',
                        'example': 5
                    }
                },
                'required': ['user2']
            }
        },
        responses={
            200: ConversationSerializer,
            201: ConversationSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Start Conversation Request',
                value={'user2': 5},
                request_only=True,
            ),
            OpenApiExample(
                'Success Response',
                value={
                    'id': 1,
                    'participants': [1, 5],
                    'created_at': '2025-11-09T12:00:00Z'
                },
                response_only=True,
                status_codes=['200', '201'],
            ),
            OpenApiExample(
                'User Not Found Error',
                value={'error': 'User with ID 999 does not exist'},
                response_only=True,
                status_codes=['404'],
            ),
        ],
    )
    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        Start a new conversation with another user.
        """
        current_profile = self._get_current_profile()
        user2_id = request.data.get('user2')
        if not user2_id:
            return Response(
                {'error': 'user2 is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if int(user2_id) == current_profile.id:
            return Response(
                {'error': 'Cannot start a conversation with yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user2_profile = Profile.objects.filter(id=user2_id).first()
        if not user2_profile:
            return Response(
                {'error': f'User with ID {user2_id} does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        # Check for existing conversation
        existing_conversation = Conversation.objects.filter(
            participants__id=current_profile.id
        ).filter(
            participants__id=user2_id
        ).first()
        if existing_conversation:
            serializer = ConversationSerializer(existing_conversation, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(current_profile, user2_profile)
        conversation.save()
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
     

    @extend_schema(
        tags=['Chat'],
        summary="Get conversation messages",
        description="Retrieve all messages for a specific conversation with pagination. User must be a participant.",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number (default: 1)',
                required=False,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of messages per page (default: 50, max: 500)',
                required=False,
            ),
        ],
        responses={
            200: MessageSerializer(many=True),
            403: {'description': 'Not a participant in this conversation'},
            404: {'description': 'Conversation not found'},
        },
    )
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages for a specific conversation.
        Returns paginated results ordered by timestamp.
        """
        # Get the conversation
        conversation = self.get_object()
        current_profile = self._get_current_profile()
        
        # Verify user is a participant
        if not conversation.participants.filter(id=current_profile.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get messages for this conversation, exclude deleted messages
        messages = Message.objects.filter(
            conversation=conversation,
            is_deleted=False
        ).order_by('timestamp')
        
        # Apply pagination
        paginator = MessagePagination()
        paginated_messages = paginator.paginate_queryset(messages, request)
        
        # Serialize and return
        serializer = MessageSerializer(paginated_messages, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=['Chat'],
        summary="Send message to conversation",
        description="Send a new message to a specific conversation. Supports text content and file attachments. User must be a participant.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'content': {
                        'type': 'string',
                        'description': 'Message text content',
                        'example': 'Hello! How are you?'
                    },
                    'attachment': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Optional file attachment'
                    }
                }
            }
        },
        responses={
            201: MessageSerializer,
            400: {'description': 'Bad request - content or attachment required'},
            403: {'description': 'Not a participant in this conversation'},
            404: {'description': 'Conversation not found'},
        },
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def send_message(self, request, pk=None):
        """
        Send a message to a specific conversation.
        At least one of content or attachment must be provided.
        """
        # Get the conversation
        conversation = self.get_object()
        current_profile = self._get_current_profile()
        
        # Verify user is a participant
        if not conversation.participants.filter(id=current_profile.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get content and attachment
        content = request.data.get('content', '').strip()
        attachment = request.FILES.get('attachment')
        
        # Validate that at least one exists
        if not content and not attachment:
            return Response(
                {'error': 'Either content or attachment must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=current_profile,
            content=content,
            attachment=attachment
        )
        
        # Serialize and return
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



@extend_schema_view(
    list=extend_schema(
        tags=['Chat'],
        summary="List messages",
        description="Retrieve all messages from conversations where the authenticated user is a participant.",
    ),
    retrieve=extend_schema(
        tags=['Chat'],
        summary="Get message details",
        description="Retrieve details of a specific message. User must be a participant in the conversation.",
    ),
    create=extend_schema(
        tags=['Chat'],
        summary="Send a message",
        description="Send a new message in a conversation. User must be a participant. Supports file attachments.",
    ),
    update=extend_schema(
        tags=['Chat'],
        summary="Update message",
        description="Update a message. User must be the sender.",
    ),
    partial_update=extend_schema(
        tags=['Chat'],
        summary="Partially update message",
        description="Partially update a message. User must be the sender.",
    ),
    destroy=extend_schema(
        tags=['Chat'],
        summary="Delete message",
        description="Delete a message. User must be the sender.",
    ),
)
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    pagination_class = MessagePagination  # Enable pagination

    def _get_current_profile(self):
        profile_id = get_profile_id_from_token(self.request)
        if not profile_id:
            raise ValidationError('current_profile is missing in token')
        return get_object_or_404(Profile, id=profile_id)

    def get_queryset(self):
        """
        Filter messages to only show those in conversations where the user is a participant.
        """
        profile = self._get_current_profile()
        user_conversations = Conversation.objects.filter(
            participants=profile
        ).values_list('id', flat=True)  # Only get IDs
    
        return Message.objects.filter(
            conversation_id__in=user_conversations
        ).select_related(
            'sender',
            'conversation'
        ).prefetch_related(
            'conversation__participants'
        )

    @extend_schema(
        tags=['Chat'],
        summary="Mark message as read",
        description="Mark a specific message as read. Updates the is_read flag and read_at timestamp.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'example': 'message marked as read'
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={'status': 'message marked as read'},
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        current_profile = self._get_current_profile()
        # Only allow marking as read if participant
        if not msg.conversation.participants.filter(id=current_profile.id).exists():
            return Response({'error': 'You are not a participant in this conversation'}, status=status.HTTP_403_FORBIDDEN)
        msg.is_read = True
        msg.read_at = now()
        msg.save()
        return Response({'status': 'message marked as read'}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Chat'],
        summary="Edit message",
        description="Edit the content of a message. Only the sender can edit their own messages. Cannot edit deleted messages.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'content': {
                        'type': 'string',
                        'description': 'New message content',
                        'example': 'This is the updated message content'
                    }
                },
                'required': ['content']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'example': 'message edited successfully'
                    },
                    'edited_at': {
                        'type': 'string',
                        'format': 'date-time'
                    }
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'You can only edit your own messages'}
                }
            }
        }
    )
    @action(detail=True, methods=['patch'])
    def edit(self, request, pk=None):
        """Edit a message (only by sender)"""
        msg = self.get_object()
        current_profile = self._get_current_profile()
        
        # Check if user is the sender
        if msg.sender != current_profile:
            return Response(
                {'error': 'You can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if message is deleted
        if msg.is_deleted:
            return Response(
                {'error': 'Cannot edit a deleted message'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get new content
        new_content = request.data.get('content')
        if not new_content or not new_content.strip():
            return Response(
                {'error': 'Content is required and cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update message
        msg.content = new_content.strip()
        msg.edited_at = now()
        msg.save()
        
        return Response({
            'status': 'message edited successfully',
            'edited_at': msg.edited_at
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Chat'],
        summary="Delete message",
        description="Soft-delete a message. Only the sender can delete their own messages. Message content is cleared and marked as deleted.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'example': 'message deleted successfully'
                    }
                }
            },
            403: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'You can only delete your own messages'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Message is already deleted'}
                }
            }
        }
    )
    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """Soft-delete a message (only by sender)"""
        msg = self.get_object()
        current_profile = self._get_current_profile()
        
        # Check if user is the sender
        if msg.sender != current_profile:
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already deleted
        if msg.is_deleted:
            return Response(
                {'error': 'Message is already deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete
        msg.is_deleted = True
        msg.content = ""  # Clear content for privacy
        msg.save()
        
        return Response({
            'status': 'message deleted successfully'
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Chat'],
        summary="Get unread messages count",
        description="Retrieve the count of unread messages in a conversation. Excludes messages sent by the requesting user.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'unread_count': {
                        'type': 'integer',
                        'example': 3
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={'unread_count': 3},
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=['get'])
    def get_unread_messages_count(self, request, pk=None):
        conversation = self.get_object()
        current_profile = self._get_current_profile()
        # Use aggregate for count - single query
        from django.db.models import Count
        
        unread_count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=current_profile).aggregate(
            count=Count('id')
        )['count'] or 0
        
        return Response({'unread_count': unread_count})
