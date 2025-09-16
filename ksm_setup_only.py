#!/usr/bin/env python3
"""
Keeper Secrets Manager - Initial Setup
Sets up KSM configuration using one-time token (run this first)
"""

import os
import sys
from pathlib import Path
from keeper_secrets_manager_core import SecretsManager
from keeper_secrets_manager_core.storage import FileKeyValueStorage

# Configuration
KSM_CONFIG_FILE = "ksm_config.json"

def setup_ksm():
    """Set up KSM using one-time token"""
    
    print("🔧 Keeper Secrets Manager - Initial Setup")
    print("=" * 45)
    print()
    
    # Check if config already exists
    if os.path.exists(KSM_CONFIG_FILE):
        print(f"⚠️  KSM config already exists: {KSM_CONFIG_FILE}")
        
        # Test the existing connection
        try:
            secrets_manager = SecretsManager(
                config=FileKeyValueStorage(KSM_CONFIG_FILE)
            )
            print("✅ Existing configuration works correctly")
            
            # Ask user what they want to do
            print()
            print("Options:")
            print("1. Keep existing configuration (recommended)")
            print("2. Replace with new one-time token")
            print("3. Exit")
            
            choice = input("Choose option (1-3): ").strip()
            
            if choice == "1":
                print("✅ Using existing KSM configuration")
                print("🎉 KSM is ready to use!")
                return True
            elif choice == "2":
                print("🔄 Will replace existing configuration...")
                # Backup and remove old config
                backup_path = f"{KSM_CONFIG_FILE}.backup.{int(os.path.getmtime(KSM_CONFIG_FILE))}"
                os.rename(KSM_CONFIG_FILE, backup_path)
                print(f"📁 Backed up old config to: {backup_path}")
                print()
            else:
                print("❌ Setup cancelled")
                return False
            
        except Exception as e:
            print(f"❌ Error with existing config: {e}")
            print("🔄 Will create a new configuration...")
            
            # Backup old config
            backup_path = f"{KSM_CONFIG_FILE}.backup.{int(os.path.getmtime(KSM_CONFIG_FILE))}"
            os.rename(KSM_CONFIG_FILE, backup_path)
            print(f"📁 Backed up old config to: {backup_path}")
            print()
    
    # Get one-time token from user
    print("📝 To set up KSM, you need a One-Time Token from Keeper:")
    print("   1. Keeper Vault → Admin Console → Secrets Manager")
    print("   2. Create/Select Application → Create One-Time Access Token")
    print("   3. Copy the token (format: REGION:TOKEN, e.g., US:abc123...)")
    print()
    
    one_time_token = input("Enter your One-Time Token: ").strip()
    
    if not one_time_token:
        print("❌ One-time token is required!")
        return False
    
    # Basic validation for Keeper token format (REGION:TOKEN)
    if ':' not in one_time_token:
        print("⚠️  Warning: Token doesn't look like a Keeper one-time token")
        print("   Expected format: [REGION]:[TOKEN] (e.g., US:abc123...)")
        proceed = input("Continue anyway? (y/N): ").strip().lower()
        if proceed != 'y':
            print("❌ Setup cancelled")
            return False
    
    try:
        print("🔗 Connecting to Keeper Secrets Manager...")
        
        # Clean up any temporary files that might interfere
        temp_files = [f for f in os.listdir('.') if f.startswith('ksm_config') and f.endswith('.tmp')]
        for temp_file in temp_files:
            os.remove(temp_file)
            print(f"🧹 Cleaned up temporary file: {temp_file}")
        
        # Initialize KSM with one-time token
        secrets_manager = SecretsManager(token=one_time_token)
        
        # Get configuration
        print("📥 Retrieving configuration from Keeper...")
        config = secrets_manager.get_config()
        
        # Save to file
        storage = FileKeyValueStorage(KSM_CONFIG_FILE)
        storage.save_config(config)
        
        # Set secure permissions
        os.chmod(KSM_CONFIG_FILE, 0o600)
        
        print(f"✅ Configuration saved to: {KSM_CONFIG_FILE}")
        print(f"🔒 File permissions set to owner-only (600)")
        
        # Test the connection
        print("🧪 Testing connection...")
        test_secrets_manager = SecretsManager(
            config=FileKeyValueStorage(KSM_CONFIG_FILE)
        )
        print("✅ Connection test successful!")
        
        print()
        print("🎉 KSM setup completed successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Create your JWT records in Keeper Vault")
        print("   2. Update app_config.json with Record UIDs")
        print("   3. Run: python improved_server_jwt_generator.py (server)")
        print("   4. Run: python improved_local_jwt_sync.py (developers)")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print()
        print("💡 Troubleshooting:")
        
        # Specific error handling
        if "already initialized with a different token" in str(e):
            print("   • There's a conflicting configuration somewhere")
            print("   • Try deleting any existing ksm_config.json files")
            print("   • Generate a new one-time token in Keeper Admin Console")
            print("   • Make sure you're using the token from the correct KSM application")
        else:
            print("   • Check that the one-time token is correct and not expired")
            print("   • Verify network connection to Keeper servers")
            print("   • Ensure the KSM application has proper permissions")
            print("   • Try generating a new one-time token")
        
        return False

def main():
    success = setup_ksm()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()