#!/usr/bin/env python3
"""
End-to-end test for user management and authentication system
Tests core functionality to verify compatibility between servers
"""
import os
import sys
import requests
import json
import time
import argparse
from urllib.parse import urljoin

def test_auth_flow(base_url="http://localhost:8000", admin_password="adminpassword"):
    """
    Test the authentication flow:
    1. Register a test user
    2. Login with test user
    3. Try accessing a protected endpoint
    4. Test admin authentication
    5. Test admin can access user list
    
    Args:
        base_url: Base URL of the API server
        admin_password: Password for the admin user
    """
    print(f"Testing authentication flow against {base_url}")
    
    # Generate unique test user
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test{int(time.time())}@example.com",
        "password": "TestPassword123!"
    }
    
    # Step 1: Register test user
    print(f"\n1. Registering test user: {test_user['username']}")
    register_url = urljoin(base_url, "/v1/auth/register")
    register_response = requests.post(register_url, json=test_user)
    
    if register_response.status_code != 200 and register_response.status_code != 201:
        print(f"❌ User registration failed with status {register_response.status_code}")
        print(register_response.text)
        return False
    else:
        print(f"✅ User registered successfully: {register_response.status_code}")
        try:
            user_data = register_response.json()
            print(f"   User ID: {user_data.get('id')}")
            print(f"   Username: {user_data.get('username')}")
            print(f"   Email: {user_data.get('email')}")
        except:
            print("   Could not parse user data from response")
    
    # Step 2: Login with test user
    print(f"\n2. Logging in as test user: {test_user['username']}")
    token_url = urljoin(base_url, "/v1/auth/token")
    login_response = requests.post(
        token_url,
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ User login failed with status {login_response.status_code}")
        print(login_response.text)
        return False
    else:
        print(f"✅ User login successful")
        try:
            token_data = login_response.json()
            user_token = token_data.get("access_token")
            print(f"   Token type: {token_data.get('token_type')}")
            print(f"   Token: {user_token[:15]}...")
        except:
            print("   Could not parse token data from response")
            return False
    
    # Step 3: Try accessing user profile with token
    print(f"\n3. Accessing user profile with token")
    me_url = urljoin(base_url, "/v1/auth/me")
    me_response = requests.get(
        me_url,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    if me_response.status_code != 200:
        print(f"❌ User profile access failed with status {me_response.status_code}")
        print(me_response.text)
        return False
    else:
        print(f"✅ User profile access successful")
        try:
            user_profile = me_response.json()
            print(f"   Username: {user_profile.get('username')}")
            print(f"   Email: {user_profile.get('email')}")
            print(f"   Admin: {user_profile.get('is_admin')}")
            print(f"   MFA Enabled: {user_profile.get('mfa_enabled')}")
        except:
            print("   Could not parse profile data from response")
    
    # Step 4: Login as admin
    print(f"\n4. Logging in as admin user")
    admin_login_response = requests.post(
        token_url,
        data={
            "username": "admin",
            "password": admin_password
        }
    )
    
    if admin_login_response.status_code != 200:
        print(f"❌ Admin login failed with status {admin_login_response.status_code}")
        print(admin_login_response.text)
        return False
    else:
        print(f"✅ Admin login successful")
        try:
            admin_token_data = admin_login_response.json()
            admin_token = admin_token_data.get("access_token")
            print(f"   Token: {admin_token[:15]}...")
        except:
            print("   Could not parse admin token data from response")
            return False
    
    # Step 5: Try accessing admin endpoint
    print(f"\n5. Accessing admin users list")
    users_url = urljoin(base_url, "/v1/admin/users")
    
    try:
        users_response = requests.get(
            users_url,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if users_response.status_code == 200:
            print(f"✅ Admin users list access successful")
            users = users_response.json()
            print(f"   Found {len(users)} users")
            return True
        else:
            print(f"❌ Admin users list access failed with status {users_response.status_code}")
            print(users_response.text)
            
            # Try a different approach if this one fails
            print(f"\nTrying alternative admin endpoint...")
            alt_users_url = urljoin(base_url, "/v1/admin/users/")
            alt_response = requests.get(
                alt_users_url,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if alt_response.status_code == 200:
                print(f"✅ Alternative admin endpoint access successful")
                return True
            else:
                print(f"❌ Alternative admin endpoint access failed with status {alt_response.status_code}")
                print(alt_response.text)
                return False
    except Exception as e:
        print(f"❌ Error accessing admin endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test authentication flow")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API server")
    parser.add_argument("--password", default="adminpassword", help="Admin password")
    args = parser.parse_args()
    
    success = test_auth_flow(args.url, args.password)
    if success:
        print("\n🎉 Authentication flow test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Authentication flow test failed")
        sys.exit(1)
