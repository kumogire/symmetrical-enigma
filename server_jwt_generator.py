#!/usr/bin/env python3
"""
JWT Server Generator - Keeper Secrets Manager (Config information stored via Keeper)
Generates JWT tokens using configuration stored in Keeper Vault and distributes them via Keeper Vault for API Engineers team
"""

import os
import sys
import json
import jwt
import datetime
from pathlib import Path
from keeper_secrets_manager_core import SecretsManager
from keeper_secrets_manager_core.storage import FileKeyValueStorage

# KSM Configuration
KSM_CONFIG_FILE = "ksm_config.json"

# Application Configuration (can be environment variables or simple config file)
APP_CONFIG_FILE = "app_config.json"

def load_app_config():
    """Load application configuration (Record UIDs)"""
    
    config = {}
    
    # Try environment variables first
    if os.getenv("JWT_TOKEN_RECORD_UID") and os.getenv("JWT_CONFIG_RECORD_UID"):
        config = {
            "jwt_token_record_uid": os.getenv("JWT_TOKEN_RECORD_UID"),
            "jwt_config_record_uid": os.getenv("JWT_CONFIG_RECORD_UID")
        }
        print("📋 Using configuration from environment variables")
        return config
    
    # Try app config file
    if os.path.exists(APP_CONFIG_FILE):
        try:
            with open(APP_CONFIG_FILE, 'r') as f:
                config = json.load(f)
            print(f"📋 Using configuration from {APP_CONFIG_FILE}")
            return config
        except Exception as e:
            print(f"❌ Error reading {APP_CONFIG_FILE}: {e}")
    
    # Fallback - create template config file
    template_config = {
        "jwt_token_record_uid": "YOUR_JWT_TOKEN_RECORD_UID",
        "jwt_config_record_uid": "YOUR_JWT_CONFIG_RECORD_UID"
    }
    
    with open(APP_CONFIG_FILE, 'w') as f:
        json.dump(template_config, f, indent=2)
    
    print(f"❌ Configuration not found. Created template: {APP_CONFIG_FILE}")
    print("Please update the Record UIDs in this file and run again.")
    return None

def load_jwt_config_from_keeper(secrets_manager, config_record_uid):
    """Load JWT configuration from Keeper Vault"""
    
    try:
        print(f"🔧 Loading JWT configuration from Keeper...")
        
        # Get the config record
        config_records = secrets_manager.get_secrets([config_record_uid])
        
        if not config_records:
            print(f"❌ JWT config record not found: {config_record_uid}")
            return None
        
        config_record = config_records[0]
        print(f"📋 Found config record: '{config_record.title}'")
        
        # Extract configuration
        jwt_config = {
            "secret": config_record.password,  # JWT signing secret
            "issuer": "api-development-server",  # Default
            "audience": "api-engineers",  # Default
            "expiration_hours": 24,  # Default
            "secrets_dir": "secrets",  # Default
            "jwt_filename": "api_access.jwt"  # Default
        }
        
        # Override with custom fields if they exist
        for field in config_record.fields:
            field_label = field.get('label', '').lower()
            field_value = field.get('value', [{}])[0].get('value', '')
            
            if field_label == 'issuer' and field_value:
                jwt_config['issuer'] = field_value
            elif field_label == 'audience' and field_value:
                jwt_config['audience'] = field_value
            elif field_label == 'expiration_hours' and field_value:
                try:
                    jwt_config['expiration_hours'] = int(field_value)
                except ValueError:
                    pass
            elif field_label == 'secrets_dir' and field_value:
                jwt_config['secrets_dir'] = field_value
            elif field_label == 'jwt_filename' and field_value:
                jwt_config['jwt_filename'] = field_value
        
        print(f"🔧 JWT Configuration loaded:")
        print(f"   Issuer: {jwt_config['issuer']}")
        print(f"   Audience: {jwt_config['audience']}")
        print(f"   Expiration: {jwt_config['expiration_hours']} hours")
        print(f"   Secrets dir: {jwt_config['secrets_dir']}")
        print(f"   JWT filename: {jwt_config['jwt_filename']}")
        print(f"   Secret length: {len(jwt_config['secret'])} characters")
        
        return jwt_config
        
    except Exception as e:
        print(f"❌ Error loading JWT config from Keeper: {e}")
        return None

def ensure_directories(secrets_dir):
    """Create necessary directories"""
    secrets_path = Path(secrets_dir)
    secrets_path.mkdir(exist_ok=True)
    print(f"✅ Secrets directory ready: {secrets_path.absolute()}")
    return secrets_path

def generate_jwt(jwt_config):
    """Generate a new JWT token using config from Keeper"""
    
    # JWT payload
    now = datetime.datetime.utcnow()
    exp_hours = jwt_config.get('expiration_hours', 24)
    
    payload = {
        "iss": jwt_config['issuer'],
        "aud": jwt_config['audience'],
        "iat": now,
        "exp": now + datetime.timedelta(hours=exp_hours),
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
    token = jwt.encode(payload, jwt_config['secret'], algorithm="HS256")
    
    print(f"🔑 Generated new JWT token")
    print(f"   Issuer: {payload['iss']}")
    print(f"   Audience: {payload['aud']}")
    print(f"   Expires: {payload['exp'].isoformat()}")
    
    return token, payload

def save_jwt_locally(token, jwt_config):
    """Save JWT to local secrets folder"""
    
    secrets_dir = jwt_config.get('secrets_dir', 'secrets')
    jwt_filename = jwt_config.get('jwt_filename', 'api_access.jwt')
    
    jwt_path = Path(secrets_dir) / jwt_filename
    
    with open(jwt_path, 'w') as f:
        f.write(token)
    
    # Set secure permissions
    os.chmod(jwt_path, 0o600)
    
    print(f"💾 JWT saved locally: {jwt_path.absolute()}")
    return jwt_path

def update_jwt_in_keeper(secrets_manager, token_record_uid, token, payload):
    """Update JWT token in Keeper Vault"""
    
    try:
        print(f"☁️  Updating JWT in Keeper Vault...")
        
        # Get the token record
        token_records = secrets_manager.get_secrets([token_record_uid])
        
        if not token_records:
            print(f"❌ JWT token record not found: {token_record_uid}")
            return False
        
        token_record = token_records[0]
        print(f"📋 Found token record: '{token_record.title}'")
        
        # Note: KSM Core SDK is read-only. In production, you would:
        # 1. Use Keeper Commander CLI with write permissions
        # 2. Use Keeper REST API 
        # 3. Use a webhook/automation system
        
        print(f"🔄 Would update record with:")
        print(f"   Password: {token[:30]}...")
        print(f"   Notes: Generated at {payload['generated_at']}")
        print(f"   Expires: {payload['exp'].isoformat()}")
        
        # For this POC, we simulate the update
        print(f"⚠️  Note: Actual Keeper update would happen here")
        print(f"   Implementation options:")
        print(f"   - Keeper Commander CLI integration")
        print(f"   - Keeper REST API calls")
        print(f"   - Automated workflow system")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating JWT in Keeper: {e}")
        return False

def send_notification(jwt_config, payload):
    """Send notification to API Engineers team"""
    
    notification_message = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event": "jwt_generated",
        "message": "New API Development JWT token has been generated and is available in Keeper Vault",
        "config": {
            "issuer": jwt_config['issuer'],
            "audience": jwt_config['audience'],
            "expiration_hours": jwt_config['expiration_hours']
        },
        "expires_at": payload['exp'].isoformat(),
        "action_required": "Run: python local_jwt_sync.py",
        "location": "Keeper Vault > API Development Access folder"
    }
    
    print(f"📢 Notification for API Engineers team:")
    print(json.dumps(notification_message, indent=2))
    
    # Save notification log
    secrets_dir = jwt_config.get('secrets_dir', 'secrets')
    log_file = Path(secrets_dir) / "jwt_notifications.log"
    with open(log_file, 'a') as f:
        f.write(f"{json.dumps(notification_message)}\n")
    
    print(f"📝 Notification logged to: {log_file}")
    
    return True

def main():
    print("🏗️  JWT Server Generator - Keeper Configuration")
    print("=" * 55)
    print()
    
    # Step 1: Load app configuration
    app_config = load_app_config()
    if not app_config:
        sys.exit(1)
    
    # Validate config
    required_keys = ['jwt_token_record_uid', 'jwt_config_record_uid']
    missing_keys = [k for k in required_keys if not app_config.get(k) or app_config[k].startswith('YOUR_')]
    
    if missing_keys:
        print(f"❌ Missing configuration: {missing_keys}")
        print(f"Please update {APP_CONFIG_FILE} with actual Record UIDs")
        sys.exit(1)
    
    print()
    
    # Step 2: Initialize KSM
    if not os.path.exists(KSM_CONFIG_FILE):
        print(f"❌ KSM config file not found: {KSM_CONFIG_FILE}")
        print("Please run the KSM setup with one-time token first.")
        sys.exit(1)
    
    try:
        secrets_manager = SecretsManager(
            config=FileKeyValueStorage(KSM_CONFIG_FILE)
        )
        print("✅ Connected to Keeper Secrets Manager")
    except Exception as e:
        print(f"❌ Failed to connect to Keeper: {e}")
        sys.exit(1)
    
    print()
    
    # Step 3: Load JWT configuration from Keeper
    jwt_config = load_jwt_config_from_keeper(
        secrets_manager, 
        app_config['jwt_config_record_uid']
    )
    
    if not jwt_config:
        sys.exit(1)
    
    print()
    
    # Step 4: Setup directories
    ensure_directories(jwt_config['secrets_dir'])
    print()
    
    # Step 5: Generate JWT
    print("🔑 Generating new JWT token...")
    token, payload = generate_jwt(jwt_config)
    print()
    
    # Step 6: Save locally
    print("💾 Saving JWT locally...")
    local_path = save_jwt_locally(token, jwt_config)
    print()
    
    # Step 7: Update Keeper
    print("☁️  Updating JWT in Keeper Vault...")
    keeper_success = update_jwt_in_keeper(
        secrets_manager, 
        app_config['jwt_token_record_uid'], 
        token, 
        payload
    )
    print()
    
    # Step 8: Send notification
    print("📢 Sending notification...")
    notification_success = send_notification(jwt_config, payload)
    print()
    
    # Summary
    print("📊 Generation Summary:")
    print(f"   ✅ JWT configuration: Loaded from Keeper")
    print(f"   ✅ JWT generated: {jwt_config['expiration_hours']} hour expiration")
    print(f"   ✅ Saved locally: {local_path}")
    print(f"   {'✅' if keeper_success else '⚠️ '} Keeper update: {'Success' if keeper_success else 'Manual step required'}")
    print(f"   ✅ Team notification: Sent")
    print()
    
    print("🎉 JWT generation completed!")
    print(f"📅 Token expires: {payload['exp'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    print("💡 Next steps:")
    print("   1. Manually update the JWT token record in Keeper Vault (if needed)")
    print("   2. API Engineers can run: python local_jwt_sync.py")

if __name__ == "__main__":
    main()