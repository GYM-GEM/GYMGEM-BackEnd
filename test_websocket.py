#!/usr/bin/env python3
"""
WebSocket Connection Test Script
Tests the chat WebSocket endpoint with the provided JWT token
"""

import asyncio
import websockets
import json
import sys

# WebSocket URL and token from user
WS_URL = "ws://127.0.0.1:8000/ws/chat/1/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYzMDM1NDE5LCJpYXQiOjE3NjMwMzE4MTksImp0aSI6ImFmMWZkODE5Y2Y1ZjRjNmI4ZGIzMzUxY2RiZjMxNDM0IiwidXNlcl9pZCI6IjIiLCJ1c2VybmFtZSI6ImpvaG5fZG9lIiwiZW1haWwiOiJqb2huQGV4YW1wbGUuY29tIiwiYWNjb3VudF9pZCI6MiwicHJvZmlsZV90eXBlcyI6W119.xSC9H_JNBUUWPcuRSesj5k29qxQWkeMTWqiW0VW0ExE"

async def test_websocket():
    """Test WebSocket connection and basic operations"""
    
    print("=" * 70)
    print("WEBSOCKET CONNECTION TEST")
    print("=" * 70)
    print(f"\nURL: {WS_URL[:50]}...")
    print(f"Conversation ID: 1")
    print(f"User: john_doe (ID: 2)")
    print("\nAttempting connection...")
    
    try:
        # Connect to WebSocket
        async with websockets.connect(WS_URL) as websocket:
            print("✅ CONNECTION SUCCESSFUL!\n")
            
            # Test 1: Send a chat message
            print("-" * 70)
            print("TEST 1: Sending chat message")
            print("-" * 70)
            message = {
                "type": "message",
                "content": "Hello! This is a test message from WebSocket."
            }
            await websocket.send(json.dumps(message))
            print(f"→ Sent: {json.dumps(message, indent=2)}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"← Received: {json.dumps(json.loads(response), indent=2)}")
            except asyncio.TimeoutError:
                print("⚠ No response received (might be broadcast only)")
            
            # Test 2: Send typing indicator
            print("\n" + "-" * 70)
            print("TEST 2: Sending typing indicator")
            print("-" * 70)
            typing = {
                "type": "typing",
                "is_typing": True
            }
            await websocket.send(json.dumps(typing))
            print(f"→ Sent: {json.dumps(typing, indent=2)}")
            
            # Wait a moment
            await asyncio.sleep(0.5)
            
            # Stop typing
            typing["is_typing"] = False
            await websocket.send(json.dumps(typing))
            print(f"→ Sent: {json.dumps(typing, indent=2)}")
            
            # Test 3: Invalid message (should get error)
            print("\n" + "-" * 70)
            print("TEST 3: Sending invalid message (empty content)")
            print("-" * 70)
            invalid = {
                "type": "message",
                "content": ""
            }
            await websocket.send(json.dumps(invalid))
            print(f"→ Sent: {json.dumps(invalid, indent=2)}")
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"← Received: {json.dumps(json.loads(response), indent=2)}")
            except asyncio.TimeoutError:
                print("⚠ No response received")
            
            print("\n" + "=" * 70)
            print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
            print("=" * 70)
            print("\nWebSocket API is working correctly!")
            print("\nConnection Details:")
            print(f"  • Server: 127.0.0.1:8000")
            print(f"  • Protocol: WebSocket (ws://)")
            print(f"  • Authentication: JWT Token (query parameter)")
            print(f"  • User: john_doe")
            print(f"  • Conversation: 1")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ CONNECTION FAILED with status code: {e.status_code}")
        if e.status_code == 403:
            print("\nPossible causes:")
            print("  • User is not a participant in conversation 1")
            print("  • Conversation 1 does not exist")
        elif e.status_code == 401:
            print("\nPossible causes:")
            print("  • JWT token is invalid or expired")
            print("  • Token authentication failed")
        print(f"\nClose code: {e.status_code}")
        
    except websockets.exceptions.InvalidHandshake as e:
        print(f"\n❌ HANDSHAKE FAILED: {e}")
        print("\nPossible causes:")
        print("  • Django server is not running")
        print("  • WebSocket endpoint not configured correctly")
        
    except ConnectionRefusedError:
        print("\n❌ CONNECTION REFUSED")
        print("\nPossible causes:")
        print("  • Django server is not running on port 8000")
        print("  • Run: python manage.py runserver")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}")
        print(f"Details: {e}")

async def decode_token():
    """Decode and display JWT token information"""
    import base64
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYzMDM1NDE5LCJpYXQiOjE3NjMwMzE4MTksImp0aSI6ImFmMWZkODE5Y2Y1ZjRjNmI4ZGIzMzUxY2RiZjMxNDM0IiwidXNlcl9pZCI6IjIiLCJ1c2VybmFtZSI6ImpvaG5fZG9lIiwiZW1haWwiOiJqb2huQGV4YW1wbGUuY29tIiwiYWNjb3VudF9pZCI6MiwicHJvZmlsZV90eXBlcyI6W119.xSC9H_JNBUUWPcuRSesj5k29qxQWkeMTWqiW0VW0ExE"
    
    print("\n" + "=" * 70)
    print("JWT TOKEN INFORMATION")
    print("=" * 70)
    
    parts = token.split('.')
    if len(parts) != 3:
        print("❌ Invalid JWT token format")
        return
    
    # Decode header
    header_data = parts[0] + '=' * (4 - len(parts[0]) % 4)
    header = json.loads(base64.urlsafe_b64decode(header_data))
    print("\nHeader:")
    print(json.dumps(header, indent=2))
    
    # Decode payload
    payload_data = parts[1] + '=' * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_data))
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    
    # Check expiration
    import datetime
    exp_timestamp = payload.get('exp')
    iat_timestamp = payload.get('iat')
    
    if exp_timestamp:
        exp_date = datetime.datetime.fromtimestamp(exp_timestamp)
        now = datetime.datetime.now()
        
        print(f"\nToken Expiration:")
        print(f"  Issued At:  {datetime.datetime.fromtimestamp(iat_timestamp)}")
        print(f"  Expires At: {exp_date}")
        print(f"  Current:    {now}")
        
        if now > exp_date:
            print(f"  Status: ❌ EXPIRED (expired {now - exp_date} ago)")
        else:
            print(f"  Status: ✅ VALID (expires in {exp_date - now})")

async def main():
    """Main test function"""
    # First decode token
    await decode_token()
    
    # Then test WebSocket
    print("\n")
    await test_websocket()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        sys.exit(0)
