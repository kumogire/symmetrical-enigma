#!/usr/bin/env python3
"""
Local JWT Sync - Keeper Secrets Manager
Retrieves the latest JWT token from Keeper Vault for local development
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

# Application Configuration
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
        
        # Extract configuration with defaults
        jwt_config = {
            "secrets_dir": "secrets",
            "jwt_filename": "api_access.jwt"
        }
        
        # Override with custom fields if they exist
        for field in config_record.fields:
            field_label = field.get('label', '').lower()
            field_value = field.get('value', [{}])[0].get('value', '')
            
            if field_label == 'secrets_dir' and field_value:
                jwt_config['secrets_dir'] = field_value
            elif field_label == 'jwt_filename' and field_value:
                jwt_config['jwt_filename'] = field_value
        
        print(f"🔧 JWT Configuration:")
        print(f"   Secrets dir: {jwt_config['secrets_dir']}")
        print(f"   JWT filename: {jwt_config['jwt_filename']}")
        
        return jwt_config
        
    except Exception as e:
        print(f"❌ Error loading JWT config: {e}")
        # Return defaults on error
        return {
            "secrets_dir": "secrets",
            "jwt_filename": "api_access.jwt"
        }

def ensure_directories(secrets_dir):
    """Create necessary directories"""
    secrets_path = Path(secrets_dir)
    secrets_path.mkdir(exist_ok=True)
    return secrets_path

def remove_old_jwt(jwt_config):
    """Remove old JWT file if it exists"""
    
    secrets_dir = jwt_config['secrets_dir']
    jwt_filename = jwt_config['jwt_filename']
    jwt_path = Path(secrets_dir) / jwt_filename
    
    if jwt_path.exists():
        # Backup old JWT with timestamp
        backup_name = f"{jwt_filename}.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = jwt_path.parent / backup_name
        
        jwt_path.rename(backup_path)
        print(f"🗂️  Old JWT backed up: {backup_path}")
        return True
    else:
        print(f"ℹ️  No existing JWT found at: {jwt_path}")
        return False

def retrieve_jwt_from_keeper(secrets_manager, token_record_uid):
    """Retrieve the latest JWT from Keeper Vault"""
    
    try:
        print(f"📡 Retrieving JWT from Keeper Vault...")
        
        # Retrieve JWT record
        token_records = secrets_manager.get_secrets([token_record_uid])
        
        if not token_records:
            print(f"❌ JWT token record not found: {token_record_uid}")
            return None, None
        
        jwt_record = token_records[0]
        print(f"📋 Found JWT record: '{jwt_record.title}'")
        
        # Extract JWT token
        jwt_token = jwt_record.password
        
        if not jwt_token:
            print(f"❌ No JWT token found in record password field")
            return None, None
        
        # Try to decode JWT to get metadata (without verification for info)
        payload = None
        try:
            # Decode without verification to get payload info
            payload = jwt.decode(jwt_token, options={"verify_signature": False})
            print(f"🔍 JWT Token Info:")
            print(f"   Issuer: {payload.get('iss', 'Unknown')}")
            print(f"   Audience: {payload.get('aud', 'Unknown')}")
            print(f"   Generated: {payload.get('generated_at', 'Unknown')}")
            
            # Check expiration
            exp_timestamp = payload.get('exp')
            if exp_timestamp:
                exp_datetime = datetime.datetime.fromtimestamp(exp_timestamp)
                now = datetime.datetime.utcnow()
                
                if exp_datetime > now:
                    time_left = exp_datetime - now
                    print(f"   Expires: {exp_datetime.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    print(f"   Time left: {time_left}")
                    print(f"   ✅ Token is valid")
                else:
                    print(f"   Expires: {exp_datetime.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    print(f"   ❌ Token has expired!")
                    print(f"   Please contact the team to generate a new token")
            
        except jwt.InvalidTokenError as e:
            print(f"⚠️  Could not decode JWT for info: {e}")
            print(f"   Token will be saved anyway")
        
        # Get additional metadata from record
        notes = getattr(jwt_record, 'notes', '')
        if notes:
            print(f"📝 Notes: {notes}")
        
        return jwt_token, payload
        
    except Exception as e:
        print(f"❌ Error retrieving JWT from Keeper: {e}")
        return None, None

def save_jwt_locally(jwt_token, jwt_config):
    """Save the new JWT token locally"""
    
    secrets_dir = jwt_config['secrets_dir']
    jwt_filename = jwt_config['jwt_filename']
    jwt_path = Path(secrets_dir) / jwt_filename
    
    try:
        with open(jwt_path, 'w') as f:
            f.write(jwt_token)
        
        # Set restrictive permissions (owner only)
        os.chmod(jwt_path, 0o600)
        
        print(f"💾 JWT saved locally: {jwt_path.absolute()}")
        print(f"🔒 File permissions set to owner-only (600)")
        
        return jwt_path
        
    except Exception as e:
        print(f"❌ Error saving JWT locally: {e}")
        return None

def verify_jwt_access(jwt_config):
    """Verify the JWT can be read and used"""
    
    secrets_dir = jwt_config['secrets_dir']
    jwt_filename = jwt_config['jwt_filename']
    jwt_path = Path(secrets_dir) / jwt_filename
    
    if not jwt_path.exists():
        print(f"❌ JWT file not found: {jwt_path}")
        return False
    
    try:
        with open(jwt_path, 'r') as f:
            token = f.read().strip()
        
        if len(token) > 0:
            print(f"✅ JWT file readable: {len(token)} characters")
            print(f"🔗 Token preview: {token[:30]}...")
            return True
        else:
            print(f"❌ JWT file is empty")
            return False
            
    except Exception as e:
        print(f"❌ Error reading JWT file: {e}")
        return False

def main():
    print("🔄 Local JWT Sync - Keeper Configuration")
    print("=" * 45)
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
        print("❌ Failed to load JWT configuration")
        sys.exit(1)
    
    print()
    
    # Step 4: Setup directories
    print("📁 Setting up local environment...")
    secrets_path = ensure_directories(jwt_config['secrets_dir'])
    print(f"✅ Secrets directory: {secrets_path.absolute()}")
    print()
    
    # Step 5: Remove old JWT
    print("🗑️  Managing old JWT...")
    had_old_jwt = remove_old_jwt(jwt_config)
    print()
    
    # Step 6: Retrieve new JWT from Keeper
    print("☁️  Retrieving latest JWT from Keeper Vault...")
    jwt_token, payload = retrieve_jwt_from_keeper(
        secrets_manager, 
        app_config['jwt_token_record_uid']
    )
    
    if not jwt_token:
        print("❌ Failed to retrieve JWT from Keeper")
        sys.exit(1)
    
    print("✅ JWT retrieved successfully from Keeper")
    print()
    
    # Step 7: Save JWT locally
    print("💾 Saving JWT locally...")
    saved_path = save_jwt_locally(jwt_token, jwt_config)
    
    if not saved_path:
        print("❌ Failed to save JWT locally")
        sys.exit(1)
    
    print()
    
    # Step 8: Verify access
    print("🔍 Verifying JWT access...")
    access_ok = verify_jwt_access(jwt_config)
    print()
    
    # Summary
    print("📊 Sync Summary:")
    print(f"   {'✅' if had_old_jwt else 'ℹ️ '} Old JWT: {'Backed up' if had_old_jwt else 'None found'}")
    print(f"   ✅ Configuration: Loaded from Keeper")
    print(f"   ✅ New JWT: Retrieved from Keeper")
    print(f"   ✅ Local save: {saved_path}")
    print(f"   {'✅' if access_ok else '❌'} Verification: {'Passed' if access_ok else 'Failed'}")
    
    if payload:
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            exp_datetime = datetime.datetime.fromtimestamp(exp_timestamp)
            print(f"   📅 Expires: {exp_datetime.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    print()
    
    if access_ok:
        print("🎉 JWT sync completed successfully!")
        print("💡 Your local JWT is now up to date and ready for API development.")
        print()
        print("🔧 Usage in your code:")
        secrets_dir = jwt_config['secrets_dir']
        jwt_filename = jwt_config['jwt_filename']
        print(f"   with open('{secrets_dir}/{jwt_filename}', 'r') as f:")
        print(f"       jwt_token = f.read().strip()")
        print(f"   headers = {{'Authorization': f'Bearer {{jwt_token}}'}}")
    else:
        print("❌ JWT sync completed with errors")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()