# Chat API Endpoints - Correct Usage Guide

## Issue You Encountered

❌ **WRONG:** `/api/chat/conversations/1/messages/` (404 Not Found)

✅ **CORRECT:** `/api/chat/conversations/1/messages/` (NOW FIXED!)

## Problem Explanation

Previously, the chat API didn't have a nested endpoint to get messages for a specific conversation. You had to use:
- `/api/chat/messages/` - Get all messages (from all conversations you're in)
- Filter manually on the client side

This was inconvenient and inefficient.

## ✅ Solution Implemented

Added two new custom actions to `ConversationViewSet`:

1. **`/api/chat/conversations/{id}/messages/`** - Get all messages for a conversation
2. **`/api/chat/conversations/{id}/send_message/`** - Send message to a conversation

---

## Complete Chat API Endpoints

### 1. Conversations

#### List User's Conversations
```http
GET /api/chat/conversations/
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `search` (optional): Filter by participant username

**Response:**
```json
[
  {
    "id": 1,
    "participants": [2, 3],
    "messages": [],
    "created_at": "2025-11-13T10:00:00Z"
  }
]
```

#### Get Single Conversation
```http
GET /api/chat/conversations/{id}/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 1,
  "participants": [2, 3],
  "messages": [
    {
      "id": 1,
      "sender": 2,
      "sender_name": "john_doe",
      "content": "Hello!",
      "timestamp": "2025-11-13T10:05:00Z",
      "is_read": false,
      "is_deleted": false
    }
  ],
  "created_at": "2025-11-13T10:00:00Z"
}
```

#### Start New Conversation
```http
POST /api/chat/conversations/start/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "user2": 3
}
```

**Response:**
- **201 Created** - New conversation created
- **200 OK** - Conversation already exists (returns existing)

```json
{
  "id": 1,
  "participants": [2, 3],
  "messages": [],
  "created_at": "2025-11-13T10:00:00Z"
}
```

---

### 2. Messages (NEW - Nested Endpoints)

#### Get Conversation Messages (✅ NEW!)
```http
GET /api/chat/conversations/{id}/messages/?page=1&page_size=50
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 50, max: 500): Messages per page

**Response:**
```json
{
  "count": 150,
  "next": "http://api/chat/conversations/1/messages/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "conversation": 1,
      "sender": 2,
      "sender_name": "john_doe",
      "content": "Hello!",
      "attachment": null,
      "timestamp": "2025-11-13T10:05:00Z",
      "is_read": false,
      "read_at": null,
      "is_deleted": false,
      "edited_at": null
    },
    {
      "id": 2,
      "conversation": 1,
      "sender": 3,
      "sender_name": "jane_smith",
      "content": "Hi there!",
      "attachment": null,
      "timestamp": "2025-11-13T10:06:00Z",
      "is_read": true,
      "read_at": "2025-11-13T10:07:00Z",
      "is_deleted": false,
      "edited_at": null
    }
  ]
}
```

**Features:**
- ✅ Only returns messages from specified conversation
- ✅ Automatically filters out deleted messages (`is_deleted=True`)
- ✅ Ordered by timestamp (oldest first)
- ✅ Paginated (50 per page by default)
- ✅ Validates user is participant

**Errors:**
- `403 Forbidden` - You're not a participant in this conversation
- `404 Not Found` - Conversation doesn't exist

#### Send Message to Conversation (✅ NEW!)
```http
POST /api/chat/conversations/{id}/send_message/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

content: Hello! This is my message.
attachment: [optional file]
```

**Response (201 Created):**
```json
{
  "id": 3,
  "conversation": 1,
  "sender": 2,
  "sender_name": "john_doe",
  "content": "Hello! This is my message.",
  "attachment": null,
  "timestamp": "2025-11-13T11:30:00Z",
  "is_read": false,
  "read_at": null,
  "is_deleted": false,
  "edited_at": null
}
```

**Notes:**
- At least one of `content` or `attachment` must be provided
- Supports file uploads
- Auto-validates user is participant
- Returns created message immediately

**Errors:**
- `400 Bad Request` - No content or attachment provided
- `403 Forbidden` - Not a participant
- `404 Not Found` - Conversation doesn't exist

---

### 3. Messages (Global Endpoints)

These work across ALL conversations:

#### List All Messages
```http
GET /api/chat/messages/
Authorization: Bearer {access_token}
```

Returns all messages from all conversations you're in.

#### Mark Message as Read
```http
POST /api/chat/messages/{id}/mark_read/
Authorization: Bearer {access_token}
```

#### Edit Message
```http
POST /api/chat/messages/{id}/edit_message/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "Updated message content"
}
```

#### Delete Message (Soft Delete)
```http
POST /api/chat/messages/{id}/delete_message/
Authorization: Bearer {access_token}
```

---

## Complete Workflow Example

### Scenario: User wants to view conversation and messages

```bash
# 1. Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"password123"}'

# Response: {"access": "eyJhbGci...", "refresh": "..."}

# 2. List your conversations
curl -X GET http://127.0.0.1:8000/api/chat/conversations/ \
  -H "Authorization: Bearer eyJhbGci..."

# Response: [{"id": 1, "participants": [2, 3], ...}]

# 3. Get messages for conversation 1 (✅ NOW WORKS!)
curl -X GET "http://127.0.0.1:8000/api/chat/conversations/1/messages/?page=1" \
  -H "Authorization: Bearer eyJhbGci..."

# Response: Paginated messages from conversation 1

# 4. Send a message to conversation 1 (✅ NEW!)
curl -X POST http://127.0.0.1:8000/api/chat/conversations/1/send_message/ \
  -H "Authorization: Bearer eyJhbGci..." \
  -F "content=Hello! How are you?"

# Response: Created message object

# 5. Send message with attachment (✅ NEW!)
curl -X POST http://127.0.0.1:8000/api/chat/conversations/1/send_message/ \
  -H "Authorization: Bearer eyJhbGci..." \
  -F "content=Check out this file!" \
  -F "attachment=@/path/to/file.pdf"
```

---

## Why Disconnecting from WebSocket Didn't Affect Database Retrieval

**Your Issue:** "when i disconnected from the channel i still couldn't get the convo from database"

**Root Cause:** It wasn't about WebSocket disconnection. The issue was:

1. ❌ **Missing Endpoint:** `/api/chat/conversations/{id}/messages/` didn't exist
2. ❌ **Wrong URL:** You were trying to access a non-existent nested endpoint
3. ✅ **WebSocket Independent:** WebSocket and REST API are separate
   - WebSocket: Real-time messaging
   - REST API: CRUD operations, message history

**WebSocket** and **REST API** are completely independent:

```
┌─────────────────────────────────────────────────┐
│  REST API (HTTP)                                │
│  • List conversations                           │
│  • Get messages                                 │
│  • Send messages                                │
│  • Mark as read                                 │
│  • Edit/Delete messages                         │
│  Works even if WebSocket is disconnected ✅     │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  WebSocket (ws://)                              │
│  • Real-time message delivery                   │
│  • Typing indicators                            │
│  • Read receipts (live)                         │
│  • Message edits (live)                         │
│  Only works when connected ⚡                   │
└─────────────────────────────────────────────────┘
```

**They both access the same database**, but:
- REST API: Request-response (get data when you ask)
- WebSocket: Push notifications (get data when it happens)

---

## Updated API Endpoint Summary

### ✅ FIXED - Now Available

```
GET    /api/chat/conversations/{id}/messages/       # Get conversation messages (paginated)
POST   /api/chat/conversations/{id}/send_message/   # Send message to conversation
```

### Existing Endpoints

```
GET    /api/chat/conversations/                     # List user's conversations
POST   /api/chat/conversations/start/               # Start new conversation
GET    /api/chat/conversations/{id}/                # Get conversation details
PUT    /api/chat/conversations/{id}/                # Update conversation
DELETE /api/chat/conversations/{id}/                # Delete conversation

GET    /api/chat/messages/                          # List all messages
GET    /api/chat/messages/{id}/                     # Get message details
POST   /api/chat/messages/{id}/mark_read/           # Mark as read
POST   /api/chat/messages/{id}/edit_message/        # Edit message
POST   /api/chat/messages/{id}/delete_message/      # Delete message
```

### WebSocket

```
WS     /ws/chat/{conversation_id}/?token={jwt}      # Real-time messaging
```

---

## Testing the Fixed Endpoints

```bash
# Test getting messages for conversation 1
curl -X GET "http://127.0.0.1:8000/api/chat/conversations/1/messages/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should now return 200 OK with paginated messages!

# Test sending message to conversation 1
curl -X POST "http://127.0.0.1:8000/api/chat/conversations/1/send_message/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "content=Test message from API"

# Should now return 201 Created with message object!
```

---

## Summary

✅ **Fixed:** Added `/api/chat/conversations/{id}/messages/` endpoint
✅ **Fixed:** Added `/api/chat/conversations/{id}/send_message/` endpoint  
✅ **Verified:** User must be participant (automatic validation)
✅ **Paginated:** 50 messages per page (customizable)
✅ **Filtered:** Automatically excludes deleted messages
✅ **Independent:** Works whether WebSocket is connected or not

🎉 **You can now retrieve conversations and messages from the database even after disconnecting from WebSocket!**
