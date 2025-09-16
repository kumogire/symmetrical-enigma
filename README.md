# symmetrical-enigma (Keeper Secrets Manager based JWT distribution system)

A secure JWT token distribution system for API Engineers using Keeper Secrets Manager for centralized credential management.
**Application configuration stored in Keeper Vault** for complete centralized secret management.

## 🎯 System Overview

The idea of this application is to make JWT token creation and distrubtion easier and more secure to manage.

**Zero hardcoded configuration** - Everything managed in Keeper Vault:
- ✅ **JWT signing keys** stored in Keeper
- ✅ **JWT configuration** (expiration, issuer, etc.) stored in Keeper  
- ✅ **JWT tokens** distributed through Keeper
- ✅ **Only Record UIDs** in application config (safe to commit)

## 📋 Architecture

```
┌─────────────────┐    ┌──────────────────────────┐    ┌─────────────────┐
│   Server        │    │      Keeper Vault        │    │   Local Dev     │
│                 │    │                          │    │                 │
│ 1. Load config  ├───►│ JWT Config Record        │◄───┤ 1. Load config  │
│ 2. Generate JWT │    │ • JWT signing secret     │    │ 2. Retrieve JWT │
│ 3. Upload JWT   ├───►│ • Expiration, issuer     │    │ 3. Save locally │
│                 │    │ • Directory settings     │    │                 │
│                 │    │                          │    │                 │
│                 │    │ JWT Token Record         │    │                 │
│                 │    │ • Current JWT token      │    │                 │
└─────────────────┘    └──────────────────────────┘    └─────────────────┘
```

## 🚀 Quick Setup

### Prerequisites
- Python 3.7+
- Keeper Vault account with Secrets Manager enabled
- Access to "API Development Access" folder

### Install Dependencies
```bash
pip install keeper-secrets-manager-core PyJWT
```

## 🔧 Keeper Vault Setup

### 1. Create KSM Application
1. **Keeper Vault** → **Admin Console** → **Secrets Manager**
2. **Create Application** → **General Purpose**
3. **Application Name**: `JWT Distribution System`
4. **Generate One-Time Token** (save this!)

### 2. Create Shared Folder
1. Create folder: **`API Development Access`**
2. **Share with**: API Engineers team
3. **Permissions**: Read for engineers, Write for server

### 3. Create Keeper Records

#### A. JWT Configuration Record
1. **Add Record** in "API Development Access" folder
2. **Title**: `JWT Configuration`
3. **Password**: `your-super-secret-jwt-signing-key-256-bits` (JWT secret)
4. **Custom Fields** (click "Add Field"):
   - `issuer`: `your-api-server`
   - `audience`: `your-api-engineers`
   - `expiration_hours`: `24`
   - `secrets_dir`: `secrets`
   - `jwt_filename`: `api_access.jwt`
5. **Save** and **copy Record UID**

#### B. JWT Token Record  
1. **Add Record** in "API Development Access" folder
2. **Title**: `JWT Token - Current`
3. **Password**: (empty - will be populated by server)
4. **Save** and **copy Record UID**

## 💻 Application Setup

### 1. One-Time KSM Setup (Choose One Method)

#### Method A: Standalone Setup (Recommended)
```bash
python ksm_setup_only.py
# Enter one-time token when prompted
```

#### Method B: Setup During First Run
The improved scripts will automatically prompt for one-time token setup if `ksm_config.json` doesn't exist.

### 2. Configuration File Method

Create `app_config.json`:
```json
{
  "jwt_token_record_uid": "abc123-your-token-record-uid",
  "jwt_config_record_uid": "def456-your-config-record-uid"
}
```

### 3. Environment Variables Method (Alternative)
```bash
export JWT_TOKEN_RECORD_UID="abc123-your-token-record-uid"
export JWT_CONFIG_RECORD_UID="def456-your-config-record-uid"
```

### 4. Test the Setup

#### Server Test:
```bash
python server_jwt_generator.py
# Should connect automatically using existing ksm_config.json
```

#### Local Developer Test:
```bash
python local_jwt_sync.py  
# Should connect automatically using existing ksm_config.json
```

## 🔄 Daily Workflow

### Server Side (DevOps/Admin)

#### Generate New JWT Token
```bash
python server_jwt_generator.py
```

**What happens:**
1. ✅ Loads JWT config from Keeper (signing key, expiration, etc.)
2. ✅ Generates JWT using Keeper-stored configuration
3. ✅ Saves to local `/secrets/api_access.jwt`
4. ✅ Updates JWT token record in Keeper Vault
5. ✅ Logs notification for team

### Local Side (API Engineers)

#### Sync Latest JWT Token  
```bash
python local_jwt_sync.py
```

**What happens:**
1. ✅ Loads JWT config from Keeper (file paths, etc.)
2. ✅ Backs up old JWT (if exists)
3. ✅ Retrieves latest JWT from Keeper
4. ✅ Saves to configured local path
5. ✅ Verifies token validity and expiration

## 📁 File Structure

```
project/
├── ksm_setup_only.py                   # One-time KSM setup (optional)
├── server_jwt_generator.py             # Server-side JWT generation
├── local_jwt_sync.py                   # Local JWT synchronization
├── app_config.json                     # Application config (Record UIDs)
├── ksm_config.json                     # KSM config (auto-generated)
├── secrets/                            # Local secrets directory
│   ├── api_access.jwt                  # Current JWT token
│   ├── api_access.jwt.backup.*         # JWT backups
│   └── jwt_notifications.log           # Notification log
└── README.md                           # This file
```

## 🔧 Configuration Benefits

### What's Safe to Commit:
- ✅ `app_config.json` - Only contains Record UIDs
- ✅ Python scripts - No secrets embedded
- ✅ `requirements.txt` - Just dependencies

### What's Never Committed:
- ❌ `ksm_config.json` - Contains encryption keys
- ❌ `secrets/` directory - Contains JWT tokens
- ❌ JWT signing secrets - Stored only in Keeper

## 💻 Using JWT in Your Code

### Python Example
```python
import json

# Load config to get file paths
with open('app_config.json', 'r') as f:
    config = json.load(f)

# Read JWT from configured location (defaults: secrets/api_access.jwt)
with open('secrets/api_access.jwt', 'r') as f:
    jwt_token = f.read().strip()

# Use in API requests
import requests
headers = {'Authorization': f'Bearer {jwt_token}'}
response = requests.get('https://api.example.com/data', headers=headers)
```

### Environment Variable Usage
```bash
export JWT_TOKEN=$(cat secrets/api_access.jwt)
curl -H "Authorization: Bearer $JWT_TOKEN" https://api.example.com/data
```

## 🔒 Security Features

### Centralized Secret Management:
- ✅ **JWT signing keys** never leave Keeper Vault
- ✅ **All configuration** stored in Keeper  
- ✅ **Token rotation** managed centrally
- ✅ **Access control** through Keeper permissions

### Application Security:
- ✅ **No hardcoded secrets** anywhere in code
- ✅ **Configuration-driven** paths and settings
- ✅ **Secure file permissions** (600)
- ✅ **Automatic backups** before token updates

### Audit & Monitoring:
- ✅ **Full audit trail** through Keeper Vault logs
- ✅ **Access tracking** for all secret retrievals
- ✅ **Team notifications** for token updates

## ⚠️ .gitignore Requirements

```gitignore
# Critical - Never commit these
ksm_config.json
secrets/
*.jwt
*.token
*.backup.*
*.log
```

## 🛠️ Troubleshooting

### Configuration Issues
- **"KSM config file not found"**: 
  - **Solution 1**: Run `python ksm_setup_only.py` first
  - **Solution 2**: The improved scripts will prompt for one-time token automatically
  - **Solution 3**: Generate new one-time token if existing one expired
- **"Record not found"**: Check Record UIDs in `app_config.json`
- **"Missing configuration"**: Update Record UIDs (remove "YOUR_" prefixes)
- **"Token already used"**: Generate a new one-time token in Keeper Admin Console

### JWT Issues  
- **"Token expired"**: Run server script to generate new token
- **"Invalid token"**: Check JWT signing secret in Keeper config record
- **"Permission denied"**: Verify Keeper folder access permissions

### Debug Mode
Add to scripts for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📅 Production Deployment

### Automated Server (Cron)
```bash
# Daily JWT generation
0 9 * * * cd /path/to/jwt-system && python server_jwt_generator.py
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Sync JWT Token
  env:
    JWT_TOKEN_RECORD_UID: ${{ secrets.JWT_TOKEN_RECORD_UID }}
    JWT_CONFIG_RECORD_UID: ${{ secrets.JWT_CONFIG_RECORD_UID }}
  run: |
    python local_jwt_sync.py
    export JWT_TOKEN=$(cat secrets/api_access.jwt)
```

## 🎉 Benefits Summary

### For API Engineers:
- ✅ **One command sync** - `python local_jwt_sync.py`
- ✅ **Always current tokens** - automatic rotation
- ✅ **No secret management** - everything in Keeper
- ✅ **Configurable paths** - customize to your workflow

### For DevOps:
- ✅ **Centralized control** - all settings in Keeper Vault
- ✅ **Easy rotation** - update config record to change all settings
- ✅ **Audit compliance** - full tracking through Keeper
- ✅ **Team permissions** - fine-grained access control

### For Security:
- ✅ **Zero trust secrets** - nothing hardcoded anywhere
- ✅ **Keeper vault protection** - enterprise-grade encryption
- ✅ **Access logging** - who accessed what and when
- ✅ **Easy revocation** - remove access via Keeper permissions

**Ready to start?** 

1. Create your Keeper records
2. Update `app_config.json` with Record UIDs  
3. Run `python local_jwt_sync.py` to get your first JWT!