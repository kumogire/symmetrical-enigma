#!/usr/bin/env python3
"""
JWT Distribution System - Setup Script
This script sets up the environment for the JWT Distribution System.
It checks for Python version, installs dependencies, creates necessary directories,
creates a .gitignore file, and helps configure the Record UID in the scripts.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    print("🔧 JWT Distribution System - Setup")
    print("=" * 40)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "keeper-secrets-manager-core>=16.6.0",
            "PyJWT>=2.4.0",
            "requests>=2.25.0"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    secrets_dir = Path("secrets")
    secrets_dir.mkdir(exist_ok=True)
    
    # Set restrictive permissions
    os.chmod(secrets_dir, 0o700)
    
    print(f"✅ Created secrets directory: {secrets_dir.absolute()}")
    return True

def create_gitignore():
    """Create .gitignore file if it doesn't exist"""
    gitignore_path = Path(".gitignore")
    
    gitignore_content = """# JWT Distribution System - Security
ksm_config.json
secrets/
*.jwt
*.token
*.backup.*
*.log
__pycache__/
.env
"""
    
    if gitignore_path.exists():
        # Check if our entries are already there
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        if "ksm_config.json" not in content:
            with open(gitignore_path, 'a') as f:
                f.write(f"\n{gitignore_content}")
            print("✅ Updated existing .gitignore with JWT security rules")
        else:
            print("✅ .gitignore already contains JWT security rules")
    else:
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore with JWT security rules")
    
    return True

def check_scripts():
    """Check if required scripts are present"""
    scripts = [
        "server_jwt_generator.py",
        "local_jwt_sync.py"
    ]
    
    missing_scripts = []
    for script in scripts:
        if not Path(script).exists():
            missing_scripts.append(script)
        else:
            print(f"✅ Found: {script}")
    
    if missing_scripts:
        print("❌ Missing scripts:")
        for script in missing_scripts:
            print(f"   - {script}")
        return False
    
    return True

def get_record_uid():
    """Help user set up the record UID"""
    print()
    print("🔑 Record UID Configuration")
    print("-" * 30)
    print("You need to update the JWT_RECORD_UID in both scripts.")
    print()
    print("Steps:")
    print("1. Create a record in Keeper Vault > 'API Development Access' folder")
    print("2. Right-click the record → 'Record Details'")
    print("3. Copy the Record UID")
    print("4. Update both scripts with this UID:")
    print("   - server_jwt_generator.py")
    print("   - local_jwt_sync.py")
    print()
    
    record_uid = input("Enter your Record UID (or press Enter to skip): ").strip()
    
    if record_uid:
        # Update the scripts
        for script_name in ["server_jwt_generator.py", "local_jwt_sync.py"]:
            script_path = Path(script_name)
            if script_path.exists():
                try:
                    with open(script_path, 'r') as f:
                        content = f.read()
                    
                    # Replace the placeholder
                    updated_content = content.replace(
                        'JWT_RECORD_UID = "YOUR_JWT_RECORD_UID"',
                        f'JWT_RECORD_UID = "{record_uid}"'
                    )
                    
                    with open(script_path, 'w') as f:
                        f.write(updated_content)
                    
                    print(f"✅ Updated {script_name} with Record UID")
                except Exception as e:
                    print(f"❌ Failed to update {script_name}: {e}")
        
        return True
    else:
        print("⚠️  Remember to update the Record UID manually later")
        return True

def show_next_steps():
    """Show what to do next"""
    print()
    print("🎉 Setup completed!")
    print()
    print("📋 Next Steps:")
    print()
    print("1. 🏗️  Server Setup (DevOps):")
    print("   python server_jwt_generator.py")
    print("   (Enter one-time token when prompted)")
    print()
    print("2. 💻 Local Setup (Engineers):")
    print("   python local_jwt_sync.py")
    print("   (Enter one-time token when prompted)")
    print()
    print("3. 🔄 Daily Usage:")
    print("   Server: python server_jwt_generator.py  # Generate new JWT")
    print("   Local:  python local_jwt_sync.py        # Sync latest JWT")
    print()
    print("📖 See README.md for detailed instructions")

def main():
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    print()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    print()
    
    # Create directories
    create_directories()
    print()
    
    # Create .gitignore
    create_gitignore()
    print()
    
    # Check scripts
    if not check_scripts():
        print()
        print("⚠️  Please ensure all script files are present before continuing")
        print("   Required files: server_jwt_generator.py, local_jwt_sync.py")
        return
    print()
    
    # Configure Record UID
    get_record_uid()
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()