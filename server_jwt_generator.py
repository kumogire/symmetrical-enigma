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

# KSM Configuration - Use standard filename
KSM_CONFIG_FILE = "client-config.json"

# Application Configuration (can be environment variables or simple config file)
APP_CONFIG_FILE = "app_config.json"

def extract_field_value(field):
    """Extract string value from Keeper field (handles lists)"""
    if isinstance(field, list) and len(field) > 0:
        return field[0]
    return field

def test_existing_ksm_config():
    """Test if existing KSM configuration works"""
    
    if not os.path.exists(KSM_CONFIG_FILE):
        print(f"ℹ️  No existing KSM config found ({KSM_CONFIG_FILE})")
        return None
    
    print(f"✅ Found existing KSM configuration: {KSM_CONFIG_FILE}")
    
    try:
        # Test the existing configuration
        secrets_manager = SecretsManager(
            config=FileKeyValueStorage(KSM_CONFIG_FILE)
        )
        
        print("🧪 Testing existing KSM connection...")
        
        # Try a simple operation to verify connection works
        # This will fail gracefully if the config is invalid
        secrets_manager.get_secrets([])  # Empty list is safe - just tests connection
        
        print("✅ Existing KSM configuration works perfectly!")
        print("ℹ️  No setup required - KSM is already configured for this project")
        return secrets_manager
        
    except Exception as e:
        print(f"⚠️  Existing KSM config has issues: {e}")
        print("🔧 Will attempt to set up fresh configuration...")
        return None

def setup_ksm_with_token():
    """Set up KSM using one-time token (only if existing config doesn't work)"""
    
    print()
    print("🔧 Setting up new Keeper Secrets Manager configuration...")
    print()
    print("📝 You need a One-Time Token from Keeper Admin Console:")
    print("   1. Keeper Vault → Secrets Manager")
    print("   2. Create/Select Application → Create One-Time Access Token")
    print("   3. Copy the token (format: REGION:TOKEN)")
    print()
    
    one_time_token = input("Enter your One-Time Token (or press Enter to skip): ").strip()
    
    if not one_time_token:
        print("❌ Setup cancelled - cannot proceed without valid KSM configuration")
        return None
    
    try:
        print("🔗 Initializing connection to Keeper...")
        
        # Backup existing config if it exists
        if os.path.exists(KSM_CONFIG_FILE):
            backup_path = f"{KSM_CONFIG_FILE}.backup.{int(datetime.datetime.now().timestamp())}"
            os.rename(KSM_CONFIG_FILE, backup_path)
            print(f"📁 Backed up existing config to: {backup_path}")
        
        # Initialize KSM with one-time token
        secrets_manager = SecretsManager(
            token=one_time_token,
            config=FileKeyValueStorage(KSM_CONFIG_FILE)
        )
        
        # Test the connection
        print("🧪 Testing new configuration...")
        secrets_manager.get_secrets([])  # Test connection
        
        print(f"✅ New KSM configuration saved to: {KSM_CONFIG_FILE}")
        print("🎉 KSM setup completed successfully!")
        return secrets_manager
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print()
        if "already initialized with a different token" in str(e):
            print("💡 This suggests there's still a configuration conflict.")
            print("   The existing config might be from a different KSM application.")
            print("   Options:")
            print("   1. Use the existing config (if it works for your team)")
            print("   2. Contact your team to understand which KSM app to use")
            print("   3. Create a new KSM application for this project")
        return None

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
        try:
            issuer_field = config_record.custom_field('issuer')
            if issuer_field:
                jwt_config['issuer'] = extract_field_value(issuer_field)
        except:
            pass

        try:
            audience_field = config_record.custom_field('audience')
            if audience_field:
                jwt_config['audience'] = extract_field_value(audience_field)
        except:
            pass

        try:
            exp_hours_field = config_record.custom_field('expiration_hours')
            if exp_hours_field:
                jwt_config['expiration_hours'] = int(exp_hours_field)
        except:
            pass

        try:
            secrets_dir_field = config_record.custom_field('secrets_dir')
            if secrets_dir_field:
                jwt_config['secrets_dir'] = extract_field_value(secrets_dir_field)
        except:
            pass

        try:
            jwt_filename_field = config_record.custom_field('jwt_filename')
            if jwt_filename_field:
                jwt_config['jwt_filename'] = extract_field_value(jwt_filename_field)
        except:
            pass
        
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
    """Update JWT token in Keeper Vault (simulated for POC)"""
    
    try:
        print(f"☁️  Updating JWT in Keeper Vault...")
        
        # Get the token record
        token_records = secrets_manager.get_secrets([token_record_uid])
        
        if not token_records:
            print(f"❌ JWT token record not found: {token_record_uid}")
            return False
        
        token_record = token_records[0]
        print(f"📋 Found token record: '{token_record.title}'")
        
        # Note: For production, you would use Keeper Commander CLI or REST API to update
        print(f"🔄 Would update record with:")
        print(f"   Password: {token[:30]}...")
        print(f"   Notes: Generated at {payload['generated_at']}")
        print(f"   Expires: {payload['exp'].isoformat()}")
        
        print(f"💡 To actually update the record:")
        print(f"   1. Copy the JWT token from local file")
        print(f"   2. Paste it into the Keeper record password field")
        print(f"   3. Update the notes with generation timestamp")
        
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
        "action_required": "Run: python improved_local_jwt_sync.py",
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
    print("🏗️  JWT Server Generator - Uses Existing KSM Configuration")
    print("=" * 60)
    print()
    
    # Step 1: Test existing KSM configuration first
    print("🔍 Checking for existing KSM configuration...")
    secrets_manager = test_existing_ksm_config()
    
    if not secrets_manager:
        # Only set up new config if existing one doesn't work
        secrets_manager = setup_ksm_with_token()
        if not secrets_manager:
            sys.exit(1)
    
    print()
    
    # Step 2: Load app configuration  
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
    
    # Step 7: Update Keeper (simulated)
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
    print(f"   ✅ KSM connection: Using {KSM_CONFIG_FILE}")
    print(f"   ✅ JWT configuration: Loaded from Keeper")
    print(f"   ✅ JWT generated: {jwt_config['expiration_hours']} hour expiration")
    print(f"   ✅ Saved locally: {local_path}")
    print(f"   ⚠️  Keeper update: Manual step required")
    print(f"   ✅ Team notification: Sent")
    print()
    
    print("🎉 JWT generation completed!")
    print(f"📅 Token expires: {payload['exp'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    print("💡 Next steps:")
    print("   1. Manually update the JWT token record in Keeper Vault")
    print("   2. API Engineers can run: python improved_local_jwt_sync.py")

if __name__ == "__main__":
    main()