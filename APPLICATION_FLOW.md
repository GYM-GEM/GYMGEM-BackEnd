# GymGem Application - Complete Flow Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Authentication & Authorization Flow](#authentication--authorization-flow)
3. [Account Management Flow](#account-management-flow)
4. [Profile System Flow](#profile-system-flow)
5. [Real-time Chat System Flow](#real-time-chat-system-flow)
6. [Course Management Flow](#course-management-flow)
7. [Background Tasks Flow](#background-tasks-flow)
8. [Error Handling & Security](#error-handling--security)

---

## Architecture Overview

### Technology Stack
```
Backend Framework: Django 5.2.7 + Django REST Framework
Authentication: JWT (SimpleJWT) with token blacklisting
Real-time: Django Channels 4.3.1 + WebSockets
Message Broker: Redis (Channel Layer + Celery)
Task Queue: Celery with Celery Beat
Database: PostgreSQL (gymgem_db)
API Documentation: drf-spectacular (OpenAPI 3.0)
```

### Application Structure
```
GymGem-BackEnd/
├── accounts/          # User account management
├── authenticationAndAuthorization/  # JWT auth & permissions
├── profiles/          # Multi-type profiles (Gym, Trainer, Store, Trainee)
├── chat/             # Real-time messaging system
├── courses/          # Course management (trainers & trainees)
├── trainers/         # Trainer-specific functionality
├── trainees/         # Trainee-specific functionality
├── gyms/             # Gym management
├── stores/           # Store management
└── utils/            # Shared utilities
```

---

## Authentication & Authorization Flow

### 1. User Registration
```
Client Request → POST /api/accounts/
│
├─ Request Body:
│  {
│    "username": "john_doe",
│    "email": "john@example.com",
│    "password": "secure_password",
│    "confirmPassword": "secure_password",
│    "firstName": "John",
│    "lastName": "Doe"
│  }
│
├─ Backend Process:
│  1. Validate password match
│  2. Hash password using Django's make_password()
│  3. Create Account record
│  4. Return account ID
│
└─ Response:
   {
     "id": 1
   }
```

### 2. User Login
```
Client Request → POST /api/auth/login/
│
├─ Request Body:
│  {
│    "username": "john_doe",  # OR "email": "john@example.com"
│    "password": "secure_password"
│  }
│
├─ Backend Process:
│  1. Resolve username from email if email provided
│  2. Validate credentials against Django user model
│  3. Check for multiple accounts with same email
│  4. Generate JWT tokens (access + refresh)
│  5. Fetch account and associated profiles
│  6. Manage token blacklisting (limit to 5 active sessions)
│
└─ Response:
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "account": {
       "id": 1,
       "username": "john_doe",
       "email": "john@example.com",
       "profile_types": ["trainer", "trainee"]
     }
   }
```

**Token Specifications:**
- **Access Token**: Valid for 60 minutes
- **Refresh Token**: Valid for 2 days
- **Algorithm**: HS256
- **Storage**: Client stores both tokens (typically in localStorage or secure cookies)

### 3. Token Refresh
```
Client Request → POST /api/auth/refresh/
│
├─ Headers:
│  {
│    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
│  }
│
├─ Backend Process:
│  1. Validate refresh token
│  2. Check if token is blacklisted
│  3. Generate new access token
│
└─ Response:
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
   }
```

### 4. Logout
```
Client Request → POST /api/auth/logout/
│
├─ Headers:
│  {
│    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc...",
│    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
│  }
│
├─ Backend Process:
│  1. Validate access token (IsAuthenticated)
│  2. Blacklist refresh token
│  3. Prevent future use of this token
│
└─ Response:
   Status: 205 Reset Content
```

---

## Account Management Flow

### 1. List All Accounts
```
GET /api/accounts/
│
├─ Permission: AllowAny
│
├─ Backend Process:
│  1. Query all Account objects
│  2. Serialize account data
│  3. Return account list
│
└─ Response:
   [
     {
       "id": 1,
       "username": "john_doe",
       "email": "john@example.com",
       "firstName": "John",
       "lastName": "Doe",
       "createdAt": "2025-11-01T10:00:00Z",
       "updatedAt": "2025-11-01T10:00:00Z"
     }
   ]
```

### 2. Get Account Details
```
GET /api/accounts/{account_id}/
│
├─ Backend Process:
│  1. Fetch Account by ID
│  2. Retrieve associated profiles
│  3. Return detailed account data
│
└─ Response:
   {
     "id": 1,
     "username": "john_doe",
     "email": "john@example.com",
     "firstName": "John",
     "lastName": "Doe",
     "profiles": [
       {"profile_type": "trainer"},
       {"profile_type": "trainee"}
     ]
   }
```

### 3. Update Account
```
PUT /api/accounts/{account_id}/
│
├─ Request Body:
│  {
│    "username": "john_updated",
│    "email": "john.new@example.com",
│    "firstName": "John",
│    "lastName": "Updated"
│  }
│
├─ Backend Process:
│  1. Validate account exists
│  2. Update account fields
│  3. Save changes
│
└─ Response:
   {
     "message": "Account updated successfully"
   }
```

### 4. Delete Account
```
DELETE /api/accounts/{account_id}/
│
├─ Backend Process:
│  1. Validate account exists
│  2. Delete account (cascade deletes profiles, messages, etc.)
│
└─ Response:
   {
     "message": "Account deleted successfully"
   }
```

---

## Profile System Flow

### Profile Types
- **Gym**: Gym facility owner/manager
- **Trainer**: Fitness trainer who creates courses
- **Store**: Equipment/supplement store
- **Trainee**: User taking courses

### Profile Creation
```
Each account can have MULTIPLE profile types
│
├─ Database Constraint:
│  - Unique constraint on (account_id, profile_type)
│  - One account can be both trainer AND trainee
│  - Cannot duplicate same profile type per account
│
└─ Model:
   Profile {
     account: ForeignKey(Account)
     profile_type: CharField(choices=['gym','trainer','store','trainee'])
   }
```

---

## Real-time Chat System Flow

### Architecture
```
Client (WebSocket) ←→ Django Channels ←→ Redis Channel Layer ←→ Multiple Clients
│                           │
│                           ├─ HTTP REST API (CRUD operations)
│                           └─ WebSocket Consumer (Real-time messaging)
```

### 1. Start Conversation (REST API)
```
POST /api/chat/conversations/start/
│
├─ Request:
│  {
│    "user2": 5
│  }
│
├─ Backend Process:
│  1. Validate user2 exists
│  2. Prevent self-conversation
│  3. Check if conversation already exists
│  4. Create new conversation or return existing
│  5. Add both users as participants
│
└─ Response:
   Status: 200 (existing) or 201 (new)
   {
     "id": 1,
     "participants": [1, 5],
     "created_at": "2025-11-09T12:00:00Z"
   }
```

### 2. List User Conversations (REST API)
```
GET /api/chat/conversations/?search=john
│
├─ Headers:
│  Authorization: Bearer {access_token}
│
├─ Backend Process:
│  1. Filter conversations by authenticated user
│  2. Optional: Filter by participant username (search parameter)
│  3. Return conversations with participants
│
└─ Response:
   [
     {
       "id": 1,
       "participants": [
         {"id": 1, "username": "john_doe"},
         {"id": 5, "username": "jane_smith"}
       ],
       "created_at": "2025-11-09T12:00:00Z"
     }
   ]
```

### 3. Get Conversation Messages (REST API)
```
GET /api/chat/conversations/{id}/messages/?page=1
│
├─ Headers:
│  Authorization: Bearer {access_token}
│
├─ Backend Process:
│  1. Validate user is conversation participant
│  2. Retrieve messages with pagination (50 per page)
│  3. Filter out deleted messages (is_deleted=True)
│  4. Order by timestamp (oldest first)
│
└─ Response:
   {
     "count": 150,
     "next": "http://api/chat/conversations/1/messages/?page=2",
     "previous": null,
     "results": [
       {
         "id": 1,
         "sender": "john_doe",
         "content": "Hello!",
         "attachment": null,
         "timestamp": "2025-11-09T12:05:00Z",
         "is_read": true,
         "read_at": "2025-11-09T12:06:00Z",
         "is_deleted": false,
         "edited_at": null
       }
     ]
   }
```

### 4. Send Message (REST API)
```
POST /api/chat/conversations/{id}/send_message/
│
├─ Request (multipart/form-data):
│  {
│    "content": "Hello!",
│    "attachment": <file>  # Optional
│  }
│
├─ Backend Process:
│  1. Validate user is participant
│  2. Validate content or attachment exists
│  3. Create Message record
│  4. Handle file upload if attachment provided
│  5. Return message data
│
└─ Response:
   {
     "id": 10,
     "sender": "john_doe",
     "content": "Hello!",
     "attachment": "/media/chat_attachments/file.pdf",
     "timestamp": "2025-11-09T12:10:00Z"
   }
```

### 5. WebSocket Real-time Messaging

#### Connection Flow
```
1. Client Authentication
   ↓
   WebSocket URL: ws://127.0.0.1:8000/ws/chat/{conversation_id}/?token={jwt_access_token}
   Note: Server MUST be running with Daphne (ASGI), NOT with 'runserver'!
   ↓
2. JWTAuthMiddleware
   ├─ Extract token from query parameter
   ├─ Validate token using SimpleJWT
   ├─ Set scope['user'] to authenticated user
   └─ Pass to ChatConsumer
   ↓
3. ChatConsumer.connect()
   ├─ Check if user is authenticated (reject if AnonymousUser)
   ├─ Validate conversation exists
   ├─ Verify user is participant in conversation
   ├─ Add channel to Redis group: 'chat_{conversation_id}'
   └─ Accept connection
   ↓
4. Connection Established ✓
```

#### Rejection Scenarios
```
Close Code 4001: Authentication Failure (no token or invalid token)
Close Code 4003: Permission Denied (not a conversation participant)
Close Code 4004: Conversation Not Found
Close Code 4000: Unexpected Error
```

#### Send Message via WebSocket
```
Client → WebSocket
│
├─ Message Format:
│  {
│    "type": "message",  # Default for chat messages
│    "content": "Hello from WebSocket!"
│  }
│
├─ Consumer Process:
│  1. Validate JSON format
│  2. Validate content exists and is string
│  3. Validate content not empty/whitespace
│  4. Limit content length (max 5000 chars)
│  5. Create Message in database
│  6. Broadcast to all participants via Redis
│
└─ Broadcast to All Participants:
   channel_layer.group_send('chat_1', {
     "type": "chat_message",
     "message_id": 15,
     "sender": "john_doe",
     "content": "Hello from WebSocket!",
     "timestamp": "2025-11-09T12:15:00Z"
   })
```

#### Read Receipt Flow
```
Client → WebSocket
│
├─ Message Format:
│  {
│    "type": "read",
│    "message_id": 15
│  }
│
├─ Consumer Process:
│  1. Validate message_id provided
│  2. Fetch message from database
│  3. Verify message belongs to this conversation
│  4. Update is_read=True and read_at=now()
│  5. Broadcast read receipt to all participants
│
└─ Broadcast:
   {
     "type": "read_receipt",
     "message_id": 15,
     "read_by": "jane_smith",
     "read_at": "2025-11-09T12:16:00Z"
   }
```

#### Typing Indicator Flow
```
Client → WebSocket
│
├─ Message Format:
│  {
│    "type": "typing",
│    "is_typing": true
│  }
│
├─ Consumer Process:
│  1. No database operation (ephemeral)
│  2. Broadcast to OTHER participants only
│
└─ Broadcast:
   {
     "type": "typing_indicator",
     "user": "john_doe",
     "is_typing": true
   }
```

#### Edit Message Flow
```
Client → WebSocket
│
├─ Message Format:
│  {
│    "type": "edit",
│    "message_id": 15,
│    "new_content": "Updated message content"
│  }
│
├─ Consumer Process:
│  1. Validate message_id and new_content
│  2. Fetch message from database
│  3. Verify sender is current user
│  4. Verify message not deleted
│  5. Update content and set edited_at=now()
│  6. Broadcast edit to all participants
│
└─ Broadcast:
   {
     "type": "message_edited",
     "message_id": 15,
     "new_content": "Updated message content",
     "edited_by": "john_doe",
     "edited_at": "2025-11-09T12:20:00Z"
   }
```

#### Delete Message Flow
```
Client → WebSocket
│
├─ Message Format:
│  {
│    "type": "delete",
│    "message_id": 15
│  }
│
├─ Consumer Process:
│  1. Validate message_id
│  2. Fetch message from database
│  3. Verify sender is current user
│  4. Set is_deleted=True and edited_at=now()
│  5. Soft delete (keep in database)
│  6. Broadcast deletion to all participants
│
└─ Broadcast:
   {
     "type": "message_deleted",
     "message_id": 15,
     "deleted_by": "john_doe",
     "deleted_at": "2025-11-09T12:25:00Z"
   }
```

#### Disconnection Flow
```
WebSocket Close
│
├─ Consumer Process:
│  1. Remove channel from Redis group
│  2. Clean up resources
│  3. Connection terminated
│
└─ No broadcast (silent disconnect)
```

### 6. Message Lifecycle

```
Message States:
│
├─ Created
│  ├─ is_read: False
│  ├─ read_at: NULL
│  ├─ is_deleted: False
│  └─ edited_at: NULL
│
├─ Read
│  ├─ is_read: True
│  ├─ read_at: 2025-11-09T12:16:00Z
│  ├─ is_deleted: False
│  └─ edited_at: NULL
│
├─ Edited
│  ├─ is_read: True
│  ├─ read_at: 2025-11-09T12:16:00Z
│  ├─ is_deleted: False
│  └─ edited_at: 2025-11-09T12:20:00Z
│
└─ Deleted (Soft)
   ├─ is_read: True
   ├─ read_at: 2025-11-09T12:16:00Z
   ├─ is_deleted: True
   └─ edited_at: 2025-11-09T12:25:00Z
```

---

## Course Management Flow

### 1. Create Course (Trainer Only)
```
POST /api/courses/create/
│
├─ Headers:
│  Authorization: Bearer {access_token}
│
├─ Request:
│  {
│    "title": "Beginner Yoga",
│    "description": "Learn the basics of yoga",
│    "trainer_profile": 1,
│    "price": 49.99
│  }
│
├─ Backend Process:
│  1. Verify user has 'trainer' role
│  2. Validate trainer_profile belongs to user
│  3. Create Course record
│
└─ Response:
   Status: 201
   {
     "id": 1,
     "title": "Beginner Yoga",
     "description": "Learn the basics of yoga",
     "trainer_profile": 1,
     "price": 49.99
   }
```

### 2. Browse Courses (Trainee)
```
GET /api/courses/for-trainees/
│
├─ Headers:
│  Authorization: Bearer {access_token}
│
├─ Backend Process:
│  1. Verify user is authenticated
│  2. Return all available courses
│
└─ Response:
   [
     {
       "id": 1,
       "title": "Beginner Yoga",
       "trainer": "John Trainer",
       "price": 49.99
     }
   ]
```

### 3. Update Course (Trainer Only)
```
PUT /api/courses/{id}/update/
│
├─ Permissions:
│  - User must have 'trainer' role
│  - Course must belong to authenticated trainer
│
├─ Backend Process:
│  1. Validate trainer owns course
│  2. Update course fields
│
└─ Response:
   Status: 200
   {updated course data}
```

### 4. Delete Course (Trainer Only)
```
DELETE /api/courses/{id}/delete/
│
├─ Permissions:
│  - User must have 'trainer' role
│  - Course must belong to authenticated trainer
│
├─ Backend Process:
│  1. Validate trainer owns course
│  2. Delete course and related data
│
└─ Response:
   Status: 204 No Content
```

---

## Background Tasks Flow

### Celery Configuration
```
Broker: Redis (redis://127.0.0.1:6379/0)
Result Backend: Redis
Task Serializer: JSON
Accept Content: ['json']
Timezone: UTC
```

### Periodic Task: Delete Old Messages
```
Task: chat.cron.delete_old_messages
Schedule: Configured via Celery Beat
│
├─ Execution:
│  1. Calculate threshold: now() - 7 days
│  2. Query deleted messages older than threshold
│  3. Permanently delete from database
│
└─ Purpose:
   Clean up soft-deleted messages after 7 days
   to free up database storage
```

### Starting Background Services

#### Celery Worker
```bash
celery -A GymGem worker --loglevel=info
```
- Processes async tasks
- Handles message deletion tasks

#### Celery Beat (Scheduler)
```bash
celery -A GymGem beat --loglevel=info
```
- Schedules periodic tasks
- Triggers delete_old_messages task

---

## Error Handling & Security

### JWT Authentication Errors
```
401 Unauthorized:
├─ Invalid token
├─ Expired token
├─ Blacklisted token
└─ Missing token

Solution: Refresh token or re-login
```

### WebSocket Connection Errors
```
4001: Authentication Failure
├─ Missing token in query parameter
└─ Invalid JWT token

4003: Permission Denied
├─ User not participant in conversation
└─ User not authenticated

4004: Not Found
└─ Conversation does not exist

4000: Unexpected Error
└─ Server-side error during connection
```

### Rate Limiting & Security
```
Pagination:
├─ Messages: 50 per page (max 500)
├─ Prevents database overload
└─ Optimizes client performance

Message Validation:
├─ Max length: 5000 characters
├─ No empty/whitespace-only messages
└─ Content must be string type

Token Management:
├─ Max 5 active sessions per user
├─ Older tokens auto-blacklisted
└─ Refresh token rotation
```

### CORS & API Access
```
Allowed Origins: Configured in settings.py
API Schema: /api/schema/ (OpenAPI 3.0)
Swagger UI: /api/schema/swagger-ui/
ReDoc: /api/schema/redoc/
```

---

## Complete Request/Response Cycles

### Scenario 1: New User Onboarding
```
1. Register Account
   POST /api/accounts/
   ↓
2. Login
   POST /api/auth/login/
   ↓ Receive JWT tokens
3. Create Profile(s)
   (Profiles created via admin or separate endpoint)
   ↓
4. User Ready to Use Application
```

### Scenario 2: Real-time Chat Session
```
1. User Logs In
   POST /api/auth/login/
   ↓ Receive access token
   
2. List Conversations
   GET /api/chat/conversations/
   ↓
   
3. Select/Start Conversation
   POST /api/chat/conversations/start/
   ↓ Get conversation_id
   
4. Connect WebSocket
   ws://domain/ws/chat/{conversation_id}/?token={access_token}
   ↓ Connection accepted
   
5. Real-time Messaging
   ├─ Send: {"type": "message", "content": "Hi!"}
   ├─ Receive: broadcast to all participants
   ├─ Typing: {"type": "typing", "is_typing": true}
   ├─ Read: {"type": "read", "message_id": 10}
   ├─ Edit: {"type": "edit", "message_id": 10, "new_content": "Updated"}
   └─ Delete: {"type": "delete", "message_id": 10}
   
6. Disconnect
   WebSocket closes, channel removed from group
```

### Scenario 3: Trainer Creates and Manages Course
```
1. Login as Trainer
   POST /api/auth/login/
   ↓
   
2. Create Course
   POST /api/courses/create/
   ↓
   
3. View Course
   GET /api/courses/{id}/detail/
   ↓
   
4. Update Course
   PUT /api/courses/{id}/update/
   ↓
   
5. Delete Course
   DELETE /api/courses/{id}/delete/
```

### Scenario 4: Token Expiration Handling
```
1. Access Token Expires (60 min)
   API Request → 401 Unauthorized
   ↓
   
2. Client Refreshes Token
   POST /api/auth/refresh/
   Headers: {"refresh": "refresh_token"}
   ↓ Receive new access token
   
3. Retry Original Request
   Include new access token
   ↓
   
4. If Refresh Token Expired (2 days)
   POST /api/auth/login/
   ↓ Full re-authentication required
```

---

## API Endpoints Summary

### Authentication & Authorization
```
POST   /api/auth/login/          Login with credentials
POST   /api/auth/refresh/        Refresh access token
POST   /api/auth/logout/         Logout and blacklist token
```

### Account Management
```
GET    /api/accounts/            List all accounts
POST   /api/accounts/            Create new account
GET    /api/accounts/{id}/       Get account details
PUT    /api/accounts/{id}/       Update account
PATCH  /api/accounts/{id}/       Partial update
DELETE /api/accounts/{id}/       Delete account
```

### Chat System (REST)
```
GET    /api/chat/conversations/                    List user's conversations
POST   /api/chat/conversations/start/              Start new conversation
GET    /api/chat/conversations/{id}/               Get conversation details
GET    /api/chat/conversations/{id}/messages/      Get conversation messages (paginated)
POST   /api/chat/conversations/{id}/send_message/  Send message with optional attachment
PUT    /api/chat/conversations/{id}/               Update conversation
DELETE /api/chat/conversations/{id}/               Delete conversation
```

### Chat System (WebSocket)
```
WS     /ws/chat/{conversation_id}/?token={jwt}     Real-time messaging connection
```

### Courses
```
GET    /api/courses/for-trainees/   Browse available courses
POST   /api/courses/create/         Create course (trainer)
GET    /api/courses/{id}/detail/    Get course details
PUT    /api/courses/{id}/update/    Update course (trainer)
DELETE /api/courses/{id}/delete/    Delete course (trainer)
```

### API Documentation
```
GET    /api/schema/                 OpenAPI schema (YAML/JSON)
GET    /api/schema/swagger-ui/      Swagger UI interface
GET    /api/schema/redoc/           ReDoc interface
```

---

## Running the Application

### Start Django Development Server
```bash
python manage.py runserver
```

### Start Redis Server
```bash
# Option 1: Automated script
bash install_redis.sh

# Option 2: Manual
sudo apt install redis-server
sudo systemctl start redis-server
```

### Start Celery Worker
```bash
celery -A GymGem worker --loglevel=info
```

### Start Celery Beat Scheduler
```bash
celery -A GymGem beat --loglevel=info
```

### Run Migrations
```bash
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

---

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Chat Tests Only
```bash
python manage.py test chat
```

### Test Results
```
18 tests passing in chat app:
- Connection authentication tests
- Message sending/receiving tests
- Read receipt tests
- Typing indicator tests
- Edit/delete message tests
- Pagination tests
- Search/filter tests
- Error handling tests
```

---

## Environment Variables

Required in `.env` file:
```bash
# Database
DB_NAME=gymgem_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Celery (uses REDIS_URL)
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

---

## Conclusion

This application implements a complete gym/fitness platform with:
- ✅ Secure JWT authentication
- ✅ Multi-role profile system
- ✅ Real-time chat with WebSockets
- ✅ Course management for trainers/trainees
- ✅ Background task processing
- ✅ Comprehensive API documentation
- ✅ Production-ready architecture

All flows are tested, documented, and ready for deployment.
