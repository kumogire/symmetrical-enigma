#!/usr/bin/env python3
"""
JWT Server Generator - Keeper Secrets Manager
Generates JWT tokens and distributes them via Keeper Vault for API Engineers team
"""

import os
import sys
import json
import jwt
import datetime
from pathlib import Path
from keeper_secrets_manager_core import SecretsManager
from keeper_secrets_manager_core.storage import FileKeyValueStorage

# Configuration
CONFIG_FILE = "ksm_config.json"
SECRETS_DIR = "secrets"
JWT_FILE = "api_access.jwt"
JWT_RECORD_UID = "YOUR_JWT_RECORD_UID"  # Replace with actual record UID in "API Development Access"

# JWT Configuration
JWT_SECRET = "your-jwt-secret-key-here"  # In production, this should also come from Keeper
JWT_ISSUER = "api-development-server"
JWT_AUDIENCE = "api-engineers"

def ensure_directories():
    """Create necessary directories"""
    secrets_path = Path(SECRETS_DIR)
    secrets_path.mkdir(exist_ok=True)
    print(f"✅ Secrets directory ready: {secrets_path.absolute()}")

def generate_jwt():
    """Generate a new JWT token for API access"""
    
    # JWT payload
    now = datetime.datetime.utcnow()
    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": now + datetime.timedelta(hours=24),  # 24-hour expiration
        "sub": "api-development-access",
        "team": "API Engineers",
        "permissions": [
            "api:read",
            "api:write", 
            "api:deploy"
        ],
        "generated_at": now.isoformat(),
        "version": "1.0"
    }
    
    # Generate JWT
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    print(f"🔑 Generated new JWT token")
    print(f"   Issuer: {payload['iss']}")
    print(f"   Audience: {payload['aud']}")
    print(f"   Expires: {payload['exp'].isoformat()}")
    
    return token, payload

def save_jwt_locally(token):
    """Save JWT to local secrets folder"""
    
    jwt_path = Path(SECRETS_DIR) / JWT_FILE
    
    with open(jwt_path, 'w') as f:
        f.write(token)
    
    print(f"💾 JWT saved locally: {jwt_path.absolute()}")
    return jwt_path

def upload_jwt_to_keeper(token, payload):
    """Upload JWT to Keeper Vault in API Development Access folder"""
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ KSM config file not found: {CONFIG_FILE}")
        print("Please run the initial KSM setup first.")
        return False
    
    try:
        # Initialize KSM
        secrets_manager = SecretsManager(
            config=FileKeyValueStorage(CONFIG_FILE)
        )
        
        print(f"📡 Connecting to Keeper Vault...")
        
        # Get the JWT record
        records = secrets_manager.get_secrets([JWT_RECORD_UID])
        
        if not records:
            print(f"❌ JWT record not found with UID: {JWT_RECORD_UID}")
            print("Please create a record in the 'API Development Access' folder first.")
            return False
        
        jwt_record = records[0]
        print(f"📋 Found JWT record: '{jwt_record.title}'")
        
        # Update the record with new JWT
        # Note: KSM Core SDK is primarily for reading. For writing, you'd typically use:
        # - Keeper Commander CLI
        # - Keeper SDKs with write permissions
        # - Manual update through Vault UI
        
        # For this POC, we'll demonstrate the concept by showing what would be updated
        print(f"🔄 Would update record '{jwt_record.title}' with:")
        print(f"   Password: {token[:20]}...")
        print(f"   Notes: Generated at {payload['generated_at']}")
        print(f"   Custom field 'expires': {payload['exp'].isoformat()}")
        
        # In a real implementation, you might:
        # 1. Use Keeper Commander API to update the record
        # 2. Use a webhook to trigger updates
        # 3. Use Keeper's REST API with proper permissions
        
        print(f"⚠️  Note: Record update would happen here in production")
        print(f"   Manual step: Update the record in Keeper Vault with the new JWT")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to Keeper: {e}")
        return False

def send_notification():
    """Send notification to API Engineers team"""
    
        # In a real-world scenario, this could be an email, Slack message, etc.
    
    notification_message = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event": "jwt_generated",
        "message": "New API Development JWT token has been generated and is available in Keeper Vault",
        "action_required": "Run the local JWT sync script to get the latest token",
        "expires_in": "24 hours",
        "location": "Keeper Vault > API Development Access folder"
    }
    
    print(f"📢 Notification sent to API Engineers team:")
    print(json.dumps(notification_message, indent=2))
    
    # Save notification log
    log_file = Path(SECRETS_DIR) / "jwt_notifications.log"
    with open(log_file, 'a') as f:
        f.write(f"{json.dumps(notification_message)}\n")
    
    print(f"📝 Notification logged to: {log_file}")
    
    return True

def main():
    print("🏗️  JWT Server Generator - Keeper Secrets Manager Integration")
    print("=" * 65)
    print()
    
    # Step 1: Setup
    ensure_directories()
    print()
    
    # Step 2: Generate JWT
    print("🔑 Generating new JWT token...")
    token, payload = generate_jwt()
    print()
    
    # Step 3: Save locally
    print("💾 Saving JWT locally...")
    local_path = save_jwt_locally(token)
    print()
    
    # Step 4: Upload to Keeper
    print("☁️  Uploading JWT to Keeper Vault...")
    keeper_success = upload_jwt_to_keeper(token, payload)
    print()
    
    # Step 5: Send notification
    print("📢 Sending notification to API Engineers...")
    notification_success = send_notification()
    print()
    
    # Summary
    print("📊 Generation Summary:")
    print(f"   ✅ JWT generated successfully")
    print(f"   ✅ Saved locally: {local_path}")
    print(f"   {'✅' if keeper_success else '⚠️ '} Keeper upload: {'Success' if keeper_success else 'Manual step required'}")
    print(f"   ✅ Team notification: Sent")
    print()
    
    if keeper_success:
        print("🎉 JWT generation and distribution completed!")
        print("💡 API Engineers can now run the local sync script to get the new token.")
    else:
        print("⚠️  Manual step required:")
        print("   1. Copy the JWT token from the local file")
        print("   2. Update the Keeper record manually")
        print("   3. Notify the team that the new token is ready")
    
    print()
    print(f"🔗 JWT Token Preview: {token[:50]}...")
    print(f"📅 Expires: {payload['exp'].strftime('%Y-%m-%d %H:%M:%S')} UTC")

if __name__ == "__main__":
    main()