# symmetrical-enigma

A secure JWT token distribution system for API Engineers using Keeper Secrets Manager for centralized credential management.

## 🎯 System Overview

This system provides secure JWT token distribution for the API Engineering team:

- **Server Side**: Generates JWT tokens and distributes them via Keeper Vault
- **Local Side**: Engineers sync the latest JWT tokens from Keeper to their local environment
- **Zero Hardcoded Secrets**: All tokens managed centrally in Keeper Vault

## 📋 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Server        │    │   Keeper Vault   │    │   Local Dev     │
│                 │    │                  │    │                 │
│ 1. Generate JWT ├───►│ 2. Store JWT     │◄───┤ 3. Retrieve JWT │
│ 2. Save locally │    │ 3. Notify team   │    │ 4. Save locally │
│ 3. Upload JWT   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Setup

### Prerequisites
- Python 3.7+
- Keeper Vault account with Secrets Manager enabled
- Access to "API Development Access" folder in Keeper

### Install Dependencies
```bash
pip install keeper-secrets-manager-core PyJWT
```

## 🔧 Initial Setup

### 1. Keeper Vault Setup

#### A. Create KSM Application
1. **Keeper Vault** → **Admin Console** → **Secrets Manager**
2. **Create Application** → **General Purpose**
3. **Application Name**: `JWT Distribution System`
4. **Generate One-Time Token** (save this!)

#### B. Create API Development Access Folder
1. In Keeper Vault, create a **Shared Folder**: `API Development Access`
2. **Share with**: API Engineers team
3. **Permissions**: Read access for engineers, Write access for server

#### C. Create JWT Record
1. **Add Record** in the "API Development Access" folder
2. **Record Type**: Login
3. **Title**: `API Development JWT`
4. **Password**: (will be populated by server script)
5. **Save** and **copy the Record UID**

### 2. Server Setup

#### A. Configure Server Script
1. Copy `server_jwt_generator.py` to your server
2. Update configuration:
   ```python
   JWT_RECORD_UID = "your-actual-record-uid-here"
   JWT_SECRET = "your-secure-jwt-signing-key"  # Store this in Keeper too!
   ```

#### B. Setup KSM on Server
```bash
# Run the server script first time
python server_jwt_generator.py

# Enter your one-time token when prompted
# This creates ksm_config.json
```

### 3. Local Developer Setup

#### A. Configure Local Script
1. Copy `local_jwt_sync.py` to each developer machine
2. Update the Record UID:
   ```python
   JWT_RECORD_UID = "your-actual-record-uid-here"
   ```

#### B. Setup KSM Locally
```bash
# Each developer runs this once
python local_jwt_sync.py

# Enter your one-time token when prompted
# This creates ksm_config.json locally
```

## 🔄 Daily Workflow

### Server Side (DevOps/Admin)

#### Generate New JWT Token
```bash
python server_jwt_generator.py
```

**What happens:**
1. ✅ Generates new 24-hour JWT token
2. ✅ Saves to local `/secrets/api_access.jwt`
3. ✅ Updates Keeper Vault record
4. ✅ Logs notification for team
5. ✅ Shows token expiration time

### Local Side (API Engineers)

#### Sync Latest JWT Token
```bash
python local_jwt_sync.py
```

**What happens:**
1. ✅ Backs up old JWT (if exists)
2. ✅ Retrieves latest JWT from Keeper
3. ✅ Saves to local `/secrets/api_access.jwt`
4. ✅ Verifies token validity and expiration
5. ✅ Sets secure file permissions (600)

## 📁 File Structure

```
project/
├── server_jwt_generator.py     # Server-side JWT generation
├── local_jwt_sync.py          # Local JWT synchronization
├── ksm_config.json           # KSM configuration (auto-generated)
├── secrets/                  # Local secrets directory
│   ├── api_access.jwt       # Current JWT token
│   ├── api_access.jwt.backup.* # JWT backups
│   └── jwt_notifications.log # Notification log
└── README.md                # This file
```

## 💻 Using JWT in Your Code

### Python Example
```python
# Read JWT from local file
with open('secrets/api_access.jwt', 'r') as f:
    jwt_token = f.read().strip()

# Use in API requests
import requests
headers = {'Authorization': f'Bearer {jwt_token}'}
response = requests.get('https://api.example.com/data', headers=headers)
```

### Node.js Example
```javascript
const fs = require('fs');
const jwt_token = fs.readFileSync('secrets/api_access.jwt', 'utf8').trim();

const headers = {
    'Authorization': `Bearer ${jwt_token}`
};
```

### Curl Example
```bash
JWT_TOKEN=$(cat secrets/api_access.jwt)
curl -H "Authorization: Bearer $JWT_TOKEN" https://api.example.com/data
```

## 🔒 Security Features

- ✅ **No hardcoded secrets** in application code
- ✅ **Centralized token management** via Keeper Vault
- ✅ **Automatic token rotation** (24-hour expiration)
- ✅ **Secure file permissions** (600 - owner only)
- ✅ **Token backup** before replacement
- ✅ **Expiration validation** on retrieval
- ✅ **Audit trail** through Keeper Vault logs

## ⚠️ Important Security Notes

1. **Never commit** `ksm_config.json` or `secrets/` to version control
2. **Add to .gitignore**:
   ```
   ksm_config.json
   secrets/
   *.jwt
   *.backup.*
   ```
3. **Rotate JWT signing key** regularly
4. **Monitor token usage** through Keeper Vault audit logs
5. **Revoke access** by removing users from Keeper folder

## 🛠️ Troubleshooting

### Common Issues

#### "Record not found"
- Verify Record UID is correct
- Check access permissions to "API Development Access" folder
- Ensure KSM application has proper access

#### "Token expired"
- Run server script to generate new token
- Check server script is running on schedule

#### "Permission denied" on secrets file
- Check file permissions: `ls -la secrets/`
- Re-run local script to fix permissions

#### "KSM config not found"
- Run setup with one-time token
- Regenerate one-time token if expired

### Debug Mode
Add debug output to scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📅 Recommended Schedule

### Automated Server Tasks
- **Daily**: Generate new JWT (cron job)
- **Weekly**: Rotate JWT signing key
- **Monthly**: Review access permissions

### Developer Tasks
- **Daily**: Sync JWT before starting development
- **As needed**: Check token expiration with `local_jwt_sync.py`

## 🔄 Production Deployment

### Server Automation
```bash
# Add to crontab for daily token generation
0 9 * * * /usr/bin/python3 /path/to/server_jwt_generator.py
```

### CI/CD Integration
```yaml
# Example GitHub Actions step
- name: Sync JWT Token
  run: |
    python local_jwt_sync.py
    export JWT_TOKEN=$(cat secrets/api_access.jwt)
```

## 📞 Support

### For Issues:
1. Check this README troubleshooting section
2. Verify Keeper Vault access and permissions
3. Contact DevOps team for server-side issues
4. Contact API Engineers team lead for access issues

### Emergency Access:
If JWT system is down, temporary access can be provided through:
1. Direct Keeper Vault access to JWT record
2. Manual JWT generation using backup methods
3. Contact system administrator

---

## 🎉 Benefits for API Engineers

- ✅ **Always current tokens** - automatically rotated
- ✅ **No manual token management** - one command sync
- ✅ **Secure by default** - no tokens in code or repos
- ✅ **Team visibility** - shared access through Keeper
- ✅ **Audit trail** - all access logged in Keeper Vault

**Ready to start?** Run `python local_jwt_sync.py` to get your first JWT token!
