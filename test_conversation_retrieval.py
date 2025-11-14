#!/usr/bin/env python
"""
Test script to debug conversation retrieval issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GymGem.settings')
django.setup()

from chat.models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 70)
print("CONVERSATION RETRIEVAL DIAGNOSTIC")
print("=" * 70)

# Get john_doe user (ID: 2 from your token)
try:
    user = User.objects.get(username='john_doe')
    print(f"\n✓ User found: {user.username} (ID: {user.id})")
except User.DoesNotExist:
    print("\n❌ User 'john_doe' not found!")
    print("\nAvailable users:")
    for u in User.objects.all():
        print(f"  - {u.username} (ID: {u.id})")
    exit(1)

# Check all conversations in database
print("\n" + "-" * 70)
print("ALL CONVERSATIONS IN DATABASE")
print("-" * 70)

all_conversations = Conversation.objects.all()
print(f"\nTotal conversations: {all_conversations.count()}")

if all_conversations.count() == 0:
    print("\n❌ No conversations found in database!")
    print("\nTo create a conversation:")
    print("  1. Login to get token: POST /api/auth/login/")
    print("  2. Start conversation: POST /api/chat/conversations/start/")
    print("     Body: {\"user2\": <other_user_id>}")
else:
    for conv in all_conversations:
        participants = conv.participants.all()
        participant_names = [p.username for p in participants]
        print(f"\nConversation ID: {conv.id}")
        print(f"  Created: {conv.created_at}")
        print(f"  Participants: {', '.join(participant_names)}")
        print(f"  Participant IDs: {[p.id for p in participants]}")
        print(f"  Message count: {conv.messages.count()}")
        
        # Check if john_doe is a participant
        is_participant = conv.participants.filter(id=user.id).exists()
        print(f"  john_doe is participant: {'✓ YES' if is_participant else '❌ NO'}")

# Check conversations where john_doe is a participant
print("\n" + "-" * 70)
print("CONVERSATIONS FOR john_doe (via QuerySet)")
print("-" * 70)

user_conversations = Conversation.objects.filter(participants=user)
print(f"\nConversations where john_doe is participant: {user_conversations.count()}")

if user_conversations.count() == 0:
    print("\n❌ john_doe is not a participant in any conversation!")
    print("\nPossible causes:")
    print("  1. No conversations created yet")
    print("  2. john_doe not added as participant")
    print("  3. Database sync issue")
else:
    for conv in user_conversations:
        participants = conv.participants.all()
        participant_names = [p.username for p in participants]
        print(f"\nConversation ID: {conv.id}")
        print(f"  Other participants: {', '.join([p for p in participant_names if p != 'john_doe'])}")
        print(f"  Messages: {conv.messages.count()}")

# Check specific conversation ID 1 (from your WebSocket URL)
print("\n" + "-" * 70)
print("CONVERSATION ID 1 (from WebSocket URL)")
print("-" * 70)

try:
    conv1 = Conversation.objects.get(id=1)
    print(f"\n✓ Conversation 1 exists!")
    print(f"  Created: {conv1.created_at}")
    
    participants = conv1.participants.all()
    print(f"  Participants ({participants.count()}):")
    for p in participants:
        print(f"    - {p.username} (ID: {p.id})")
    
    # Check if john_doe is participant
    is_participant = conv1.participants.filter(id=user.id).exists()
    print(f"\n  john_doe is participant: {'✓ YES' if is_participant else '❌ NO'}")
    
    if not is_participant:
        print("\n  ⚠️ This is why WebSocket connection fails with code 4003!")
        print("  Solution: Add john_doe to conversation 1:")
        print(f"    conv = Conversation.objects.get(id=1)")
        print(f"    conv.participants.add(User.objects.get(id={user.id}))")
    
    # Check messages
    messages = conv1.messages.all()
    print(f"\n  Messages: {messages.count()}")
    if messages.count() > 0:
        print(f"  Latest message:")
        latest = messages.last()
        print(f"    From: {latest.sender.username}")
        print(f"    Content: {latest.content[:50]}...")
        print(f"    Time: {latest.timestamp}")
        
except Conversation.DoesNotExist:
    print("\n❌ Conversation 1 does not exist!")
    print("\n  This is why WebSocket connection fails with code 4004!")
    print("  Solution: Create conversation first via REST API")

# Summary and recommendations
print("\n" + "=" * 70)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 70)

if user_conversations.count() == 0:
    print("\n❌ Problem: john_doe has no conversations")
    print("\n📝 Solution:")
    print("  1. Create conversation via REST API:")
    print("     POST /api/chat/conversations/start/")
    print("     Headers: Authorization: Bearer <token>")
    print("     Body: {\"user2\": <other_user_id>}")
    print("\n  2. Or add john_doe to existing conversation manually:")
    print("     python manage.py shell")
    print("     >>> from chat.models import Conversation")
    print("     >>> from django.contrib.auth import get_user_model")
    print("     >>> User = get_user_model()")
    print(f"     >>> conv = Conversation.objects.get(id=1)")
    print(f"     >>> user = User.objects.get(username='john_doe')")
    print(f"     >>> conv.participants.add(user)")
else:
    print(f"\n✅ john_doe has {user_conversations.count()} conversation(s)")
    print(f"\n📝 To retrieve via API:")
    print(f"  GET /api/chat/conversations/")
    print(f"  Headers: Authorization: Bearer <token>")
    print(f"\n📝 To get specific conversation:")
    print(f"  GET /api/chat/conversations/{{id}}/")
    print(f"  Headers: Authorization: Bearer <token>")

print("\n" + "=" * 70)
