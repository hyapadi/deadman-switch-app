#!/usr/bin/env python3
"""
Simple deployment script for Render.com - Web service only with SQLite
"""
import requests
import json

def deploy_simple(api_key):
    """Deploy just the web service using SQLite"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test connection
    response = requests.get("https://api.render.com/v1/services", headers=headers)
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("✅ Connected to Render API")
    
    # Get owner ID
    owners_response = requests.get("https://api.render.com/v1/owners", headers=headers)
    if owners_response.status_code != 200:
        print(f"❌ Failed to get owner ID: {owners_response.status_code}")
        return False
    
    owners = owners_response.json()
    owner_id = owners[0]['owner']['id']
    print(f"✅ Owner ID: {owner_id}")
    
    # Create web service with SQLite (no external database needed)
    print("Creating web service with SQLite...")
    service_data = {
        "type": "web_service",
        "name": "deadman-switch",
        "ownerId": owner_id,
        "serviceDetails": {
            "repo": "https://github.com/hyapadi/deadman-switch-app",
            "branch": "main",
            "buildCommand": "pip install uv && uv sync && uv run alembic upgrade head && uv run python create_admin.py",
            "startCommand": "uv run gunicorn deadman_switch.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT",
            "plan": "free",
            "region": "oregon",
            "runtime": "python3",
            "envVars": [
                {"key": "ENVIRONMENT", "value": "production"},
                {"key": "HOST", "value": "0.0.0.0"},
                {"key": "ACCESS_TOKEN_EXPIRE_MINUTES", "value": "30"},
                {"key": "DATABASE_URL", "value": "sqlite:///./deadman_switch.db"}
            ]
        }
    }
    
    service_response = requests.post("https://api.render.com/v1/services", headers=headers, json=service_data)
    if service_response.status_code not in [200, 201]:
        print(f"❌ Service creation failed: {service_response.status_code}")
        print(f"Response: {service_response.text}")
        return False
    
    service_result = service_response.json()
    print(f"✅ Web service created: {service_result['id']}")
    print(f"🌐 Service URL: {service_result.get('serviceDetails', {}).get('url', 'URL will be available after deployment')}")
    
    print("\n🎉 Deployment initiated successfully!")
    print("\n📋 Service Details:")
    print(f"- Service ID: {service_result['id']}")
    print(f"- Name: deadman-switch")
    print(f"- Database: SQLite (local file)")
    print(f"- Plan: Free tier")
    
    print("\n📋 Next steps:")
    print("1. Monitor deployment in Render dashboard")
    print("2. Wait for build to complete (~5-10 minutes)")
    print("3. Visit your app URL when ready")
    print("4. Login with admin/admin123")
    
    return True

if __name__ == "__main__":
    print("🚀 Simple Render Deployment Script")
    print("=" * 50)
    
    api_key = input("Enter your Render API key: ").strip()
    if not api_key:
        print("❌ API key is required")
        exit(1)
    
    success = deploy_simple(api_key)
    if success:
        print("\n✅ Deployment script completed successfully!")
    else:
        print("\n❌ Deployment failed. Check the errors above.")
