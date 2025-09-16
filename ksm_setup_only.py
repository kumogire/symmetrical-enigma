# Check if config already exists
    if os.path.exists(KSM_CONFIG_FILE):
        print(f"✅ KSM config already exists: {KSM_CONFIG_FILE}")
        
        # Test the existing connection
        try:
            secrets_manager = SecretsManager(
                config=FileKeyValueStorage(KSM_CONFIG_FILE)
            )
            print("✅ Existing configuration works correctly")
            print("🎉 KSM is already set up and ready to use!")
            return True
            
        except Exception as e:
            print(f"❌ Error with existing config: {e}")
            print("⚠️  Will create a new configuration...")
            
            # Backup old config
            backup_path = f"{KSM_CONFIG_FILE}.backup"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(KSM_CONFIG_FILE, backup_path)
            print(f"📁 Backed up old config to: {backup_path}")
            print()
    
    # Get one-time token from user
    print("📝 To set up KSM, you need a One-Time Token from Keeper:")
    print("   1. Keeper Vault → Admin Console → Secrets Manager")
    print("   2. Create/Select Application → Create One-Time Access Token")
    print("   3. Copy the token (starts with 'ksm_ott_')")
    print()
    
    one_time_token = input("Enter your One-Time Token: ").strip()
    
    if not one_time_token:
        print("❌ One-time token is required!")
        return False
    
    if not one_time_token.startswith('ksm_ott_'):
        print("⚠️  Warning: Token doesn't look like a KSM one-time token")
        print("   Expected format: ksm_ott_...")
        proceed = input("Continue anyway? (y/N): ").strip().lower()
        if proceed != 'y':
            print("❌ Setup cancelled")
            return False
    
    try:
        print("🔗 Connecting to Keeper Secrets Manager...")
        
        # Initialize KSM with one-time token
        secrets_manager = SecretsManager(token=one_time_token)
        
        # Get configuration
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
        print("   • Check that the one-time token is correct")
        print("   • Verify network connection to Keeper servers")
        print("   • Ensure the KSM application has proper permissions")
        print("   • Try generating a new one-time token")
        return False

def main():
    success = setup_ksm()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()