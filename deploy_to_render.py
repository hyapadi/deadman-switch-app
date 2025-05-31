#!/usr/bin/env python3
"""
Deployment script for Render.com using the API
"""
import os
import requests
import json
import time
from typing import Dict, Any

# Configuration
RENDER_API_BASE = "https://api.render.com/v1"
GITHUB_REPO = "https://github.com/hyapadi/deadman-switch-app"

def get_api_key():
    """Get API key from environment or prompt user"""
    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        print("Please set RENDER_API_KEY environment variable")
        print("You can get your API key from: https://dashboard.render.com/u/settings#api-keys")
        return None
    return api_key

def make_request(method: str, endpoint: str, api_key: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Make API request to Render"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    url = f"{RENDER_API_BASE}{endpoint}"
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, json=data)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    if response.status_code not in [200, 201]:
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()

def create_postgres_database(api_key: str) -> str:
    """Create PostgreSQL database"""
    print("Creating PostgreSQL database...")
    
    data = {
        "name": "deadman-switch-db",
        "databaseName": "deadman_switch",
        "user": "deadman_switch_user",
        "plan": "free",  # Use free tier
        "region": "oregon"
    }
    
    result = make_request("POST", "/postgres", api_key, data)
    if result:
        print(f"✅ Database created: {result['id']}")
        return result['id']
    return None

def create_redis_instance(api_key: str) -> str:
    """Create Redis instance"""
    print("Creating Redis instance...")
    
    data = {
        "name": "deadman-switch-redis",
        "plan": "free",  # Use free tier
        "region": "oregon"
    }
    
    result = make_request("POST", "/redis", api_key, data)
    if result:
        print(f"✅ Redis created: {result['id']}")
        return result['id']
    return None

def create_web_service(api_key: str, db_id: str, redis_id: str) -> str:
    """Create web service"""
    print("Creating web service...")
    
    data = {
        "type": "web_service",
        "name": "deadman-switch",
        "repo": GITHUB_REPO,
        "branch": "main",
        "buildCommand": "pip install uv && uv sync && uv run alembic upgrade head && uv run python create_admin.py",
        "startCommand": "uv run gunicorn deadman_switch.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT",
        "plan": "free",  # Use free tier
        "region": "oregon",
        "runtime": "python3",
        "envVars": [
            {
                "key": "ENVIRONMENT",
                "value": "production"
            },
            {
                "key": "HOST",
                "value": "0.0.0.0"
            },
            {
                "key": "ACCESS_TOKEN_EXPIRE_MINUTES",
                "value": "30"
            }
        ]
    }
    
    result = make_request("POST", "/services", api_key, data)
    if result:
        print(f"✅ Web service created: {result['id']}")
        return result['id']
    return None

def wait_for_deployment(api_key: str, service_id: str):
    """Wait for deployment to complete"""
    print("Waiting for deployment to complete...")
    
    while True:
        result = make_request("GET", f"/services/{service_id}", api_key)
        if result:
            status = result.get('serviceDetails', {}).get('deployStatus')
            print(f"Deployment status: {status}")
            
            if status == "live":
                print("✅ Deployment completed successfully!")
                print(f"🌐 Your app is live at: {result['serviceDetails']['url']}")
                break
            elif status in ["build_failed", "deploy_failed"]:
                print("❌ Deployment failed!")
                break
        
        time.sleep(30)  # Wait 30 seconds before checking again

def main():
    """Main deployment function"""
    print("🚀 Starting Render deployment...")
    
    api_key = get_api_key()
    if not api_key:
        return
    
    # Test API connection
    print("Testing API connection...")
    result = make_request("GET", "/services", api_key)
    if not result:
        print("❌ Failed to connect to Render API")
        return
    
    print("✅ Connected to Render API")
    
    # Create services
    db_id = create_postgres_database(api_key)
    if not db_id:
        print("❌ Failed to create database")
        return
    
    redis_id = create_redis_instance(api_key)
    if not redis_id:
        print("❌ Failed to create Redis instance")
        return
    
    service_id = create_web_service(api_key, db_id, redis_id)
    if not service_id:
        print("❌ Failed to create web service")
        return
    
    # Wait for deployment
    wait_for_deployment(api_key, service_id)
    
    print("\n🎉 Deployment complete!")
    print("\n📋 Next steps:")
    print("1. Visit your app URL")
    print("2. Login with admin/admin123")
    print("3. Change the admin password")
    print("4. Start creating deadman switches!")

if __name__ == "__main__":
    main()
