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

# Configuration
CONFIG_FILE = "ksm_config.json"
SECRETS_DIR = "secrets"
JWT_FILE = "api_access.jwt"
JWT_RECORD_UID = "YOUR_JWT_RECORD_UID"  # Replace with actual record UID

def ensure_directories():
    """Create necessary directories"""
    secrets_path = Path(SECRETS_DIR)
    secrets_path.mkdir(exist_ok=True)
    return secrets_path

def remove_old_jwt():
    """Remove old JWT file if it exists"""
    
    jwt_path = Path(SECRETS_DIR) / JWT_FILE
    
    if jwt_path.exists():
        # Backup old JWT with timestamp
        backup_name = f"{JWT_FILE}.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = jwt_path.parent / backup_name
        
        jwt_path.rename(backup_path)
        print(f"🗂️  Old JWT backed up: {backup_path}")
        return True
    else:
        print(f"ℹ️  No existing JWT found at: {jwt_path}")
        return False

def retrieve_jwt_from_keeper():
    """Retrieve the latest JWT from Keeper Vault"""
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ KSM config file not found: {CONFIG_FILE}")
        print("Please set up Keeper Secrets Manager first:")
        print("1. Run the one-time token setup")
        print("2. Ensure you have access to the 'API Development Access' folder")
        return None, None
    
    try:
        # Initialize KSM
        secrets_manager = SecretsManager(
            config=FileKeyValueStorage(CONFIG_FILE)
        )
        
        print(f"📡 Connecting to Keeper Vault...")
        
        # Retrieve JWT record
        records = secrets_manager.get_secrets([JWT_RECORD_UID])
        
        if not records:
            print(f"❌ JWT record not found with UID: {JWT_RECORD_UID}")
            print("Please ensure:")
            print("1. The record UID is correct")
            print("2. You have access to the 'API Development Access' folder")
            print("3. The JWT record exists in Keeper Vault")
            return None, None
        
        jwt_record = records[0]
        print(f"📋 Found JWT record: '{jwt_record.title}'")
        
        # Extract JWT token
        jwt_token = jwt_record.password
        
        if not jwt_token:
            print(f"❌ No JWT token found in record password field")
            return None, None
        
        # Try to decode JWT to get metadata (without verification for info)
        try:
            # Decode without verification to get payload info
            payload = jwt.decode(jwt_token, options={"verify_signature": False})
            print(f"🔍 JWT Info:")
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
        
        return jwt_token, payload if 'payload' in locals() else None
        
    except Exception as e:
        print(f"❌ Error retrieving JWT from Keeper: {e}")
        return None, None

def save_jwt_locally(jwt_token):
    """Save the new JWT token locally"""
    
    jwt_path = Path(SECRETS_DIR) / JWT_FILE
    
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

def verify_jwt_access():
    """Verify the JWT can be read and used"""
    
    jwt_path = Path(SECRETS_DIR) / JWT_FILE
    
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
    print("🔄 Local JWT Sync - Keeper Secrets Manager")
    print("=" * 45)
    print()
    
    # Step 1: Setup
    print("📁 Setting up local environment...")
    secrets_path = ensure_directories()
    print(f"✅ Secrets directory: {secrets_path.absolute()}")
    print()
    
    # Step 2: Remove old JWT
    print("🗑️  Removing old JWT...")
    had_old_jwt = remove_old_jwt()
    print()
    
    # Step 3: Retrieve new JWT from Keeper
    print("☁️  Retrieving latest JWT from Keeper Vault...")
    jwt_token, payload = retrieve_jwt_from_keeper()
    
    if not jwt_token:
        print("❌ Failed to retrieve JWT from Keeper")
        sys.exit(1)
    
    print("✅ JWT retrieved successfully from Keeper")
    print()
    
    # Step 4: Save JWT locally
    print("💾 Saving JWT locally...")
    saved_path = save_jwt_locally(jwt_token)
    
    if not saved_path:
        print("❌ Failed to save JWT locally")
        sys.exit(1)
    
    print()
    
    # Step 5: Verify access
    print("🔍 Verifying JWT access...")
    access_ok = verify_jwt_access()
    print()
    
    # Summary
    print("📊 Sync Summary:")
    print(f"   {'✅' if had_old_jwt else 'ℹ️ '} Old JWT: {'Removed' if had_old_jwt else 'None found'}")
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
        print(f"   with open('{SECRETS_DIR}/{JWT_FILE}', 'r') as f:")
        print(f"       jwt_token = f.read().strip()")
        print(f"   headers = {{'Authorization': f'Bearer {{jwt_token}}'}}")
    else:
        print("❌ JWT sync completed with errors")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()