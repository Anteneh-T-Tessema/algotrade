# User Management API Documentation

This document describes the User Management API with two-factor authentication (2FA) implemented in the secure API servers.

## Authentication Endpoints

### 1. Register a New User

**Endpoint:** `POST /v1/auth/register`

**Description:** Creates a new user account in the system.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (201 Created):**
```json
{
  "id": "user_uuid",
  "username": "newuser",
  "email": "user@example.com",
  "is_active": true,
  "is_admin": false,
  "mfa_enabled": false,
  "created_at": "2023-05-01T12:34:56.789Z",
  "updated_at": "2023-05-01T12:34:56.789Z"
}
```

### 2. Login (Obtain Token)

**Endpoint:** `POST /v1/auth/token`

**Description:** Authenticates a user and issues an access token. If MFA is enabled for the user, the MFA code must be provided.

**Request Body (Form Data):**
```
username: newuser
password: SecurePassword123!
mfa_code: 123456  (required only if MFA is enabled)
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "MFA code required"
}
```

### 3. Setup MFA

**Endpoint:** `POST /v1/auth/mfa/setup`

**Description:** Generates a new MFA secret for a user and returns the provisioning URI for QR code generation.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_uri": "otpauth://totp/SecureAPI:newuser?secret=JBSWY3DPEHPK3PXP&issuer=SecureAPI"
}
```

### 4. Enable MFA

**Endpoint:** `POST /v1/auth/mfa/enable`

**Description:** Enables MFA for a user after verifying the provided MFA code.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "mfa_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "enabled": true
}
```

### 5. Disable MFA

**Endpoint:** `POST /v1/auth/mfa/disable`

**Description:** Disables MFA for a user after verifying the provided MFA code.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "mfa_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "enabled": false
}
```

## Admin Endpoints

### 1. List All Users

**Endpoint:** `GET /v1/admin/users`

**Description:** Returns a list of all users in the system. Requires admin privileges.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": "user_uuid1",
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true,
    "is_admin": true,
    "mfa_enabled": true,
    "created_at": "2023-05-01T12:34:56.789Z",
    "updated_at": "2023-05-01T12:34:56.789Z"
  },
  {
    "id": "user_uuid2",
    "username": "newuser",
    "email": "user@example.com",
    "is_active": true,
    "is_admin": false,
    "mfa_enabled": false,
    "created_at": "2023-05-01T12:45:56.789Z",
    "updated_at": "2023-05-01T12:45:56.789Z"
  }
]
```

### 2. Get User by Username

**Endpoint:** `GET /v1/admin/users/{username}`

**Description:** Returns details for a specific user. Requires admin privileges.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "user_uuid2",
  "username": "newuser",
  "email": "user@example.com",
  "is_active": true,
  "is_admin": false,
  "mfa_enabled": false,
  "created_at": "2023-05-01T12:45:56.789Z",
  "updated_at": "2023-05-01T12:45:56.789Z"
}
```

### 3. Update User

**Endpoint:** `PUT /v1/admin/users/{username}`

**Description:** Updates a user's information. Requires admin privileges.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "is_active": false,
  "is_admin": false
}
```

**Response (200 OK):**
```json
{
  "id": "user_uuid2",
  "username": "newuser",
  "email": "user@example.com",
  "is_active": false,
  "is_admin": false,
  "mfa_enabled": false,
  "created_at": "2023-05-01T12:45:56.789Z",
  "updated_at": "2023-05-02T09:12:34.567Z"
}
```

### 4. Delete User

**Endpoint:** `DELETE /v1/admin/users/{username}`

**Description:** Deletes a user from the system. Requires admin privileges.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "deleted": true,
  "username": "newuser"
}
```

## Error Responses

All API endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Username must be at least 3 characters long"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 409 Conflict
```json
{
  "detail": "Username already exists"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Authentication Flow

1. **Registration:** Users register with username, email, and password
2. **Login:** Users authenticate with username and password to get an access token
3. **MFA Setup (Optional):** Users can set up MFA by getting a secret and scanning a QR code in an authenticator app
4. **MFA Enable:** Users verify the MFA setup by providing a valid MFA code
5. **Login with MFA:** When MFA is enabled, users must provide an MFA code during login
6. **API Access:** Use the access token in the Authorization header for all API requests

## Security Considerations

- All passwords are hashed using bcrypt
- Access tokens are JWT tokens with a short expiration time (30 minutes)
- MFA uses TOTP (Time-based One-Time Password) algorithm according to RFC 6238
- All sensitive operations (login, password change, MFA setup/enable/disable) are logged for auditing
- Admin endpoints are restricted to users with admin privileges
- Rate limiting is applied to all authentication endpoints to prevent brute force attacks

## Example Usage (Python)

```python
import requests
import pyotp
import qrcode
from urllib.parse import urljoin
from io import BytesIO

BASE_URL = "http://localhost:8000"

# Register a new user
def register_user(username, email, password):
    response = requests.post(
        urljoin(BASE_URL, "/v1/auth/register"),
        json={"username": username, "email": email, "password": password}
    )
    return response.json()

# Login and get access token
def login(username, password, mfa_code=None):
    data = {"username": username, "password": password}
    if mfa_code:
        data["mfa_code"] = mfa_code
    
    response = requests.post(
        urljoin(BASE_URL, "/v1/auth/token"),
        data=data
    )
    return response.json()

# Setup MFA and display QR code
def setup_mfa(access_token):
    response = requests.post(
        urljoin(BASE_URL, "/v1/auth/mfa/setup"),
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    mfa_data = response.json()
    
    # Generate and display QR code
    qr = qrcode.QRCode()
    qr.add_data(mfa_data["provisioning_uri"])
    qr.make()
    
    qr_img = qr.make_image()
    qr_img.show()
    
    return mfa_data["secret"]

# Enable MFA
def enable_mfa(access_token, mfa_secret):
    # Generate a valid TOTP code from the secret
    totp = pyotp.TOTP(mfa_secret)
    mfa_code = totp.now()
    
    response = requests.post(
        urljoin(BASE_URL, "/v1/auth/mfa/enable"),
        headers={"Authorization": f"Bearer {access_token}"},
        json={"mfa_code": mfa_code}
    )
    
    return response.json()

# Example usage
if __name__ == "__main__":
    # Register a new user
    user = register_user("testuser", "test@example.com", "SecurePassword123!")
    print(f"Registered user: {user['username']}")
    
    # Login to get access token
    auth = login("testuser", "SecurePassword123!")
    access_token = auth["access_token"]
    print(f"Logged in, token: {access_token[:10]}...")
    
    # Setup MFA
    mfa_secret = setup_mfa(access_token)
    print(f"MFA secret: {mfa_secret}")
    
    # Enable MFA (scan the QR code in an authenticator app first)
    result = enable_mfa(access_token, mfa_secret)
    print(f"MFA enabled: {result['enabled']}")
    
    # Login again with MFA
    auth = login("testuser", "SecurePassword123!", pyotp.TOTP(mfa_secret).now())
    access_token = auth["access_token"]
    print(f"Logged in with MFA, token: {access_token[:10]}...")
```
