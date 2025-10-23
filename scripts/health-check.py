#!/usr/bin/env python3
"""
Comprehensive Health Check
Validates all components of the memory master system
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, List

def check_environment() -> Dict:
    """Check environment configuration"""
    required_vars = [
        'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
        'MEM0_API_KEY', 'SUPERMEMORY_API_KEY', 'CASE_NUMBER'
    ]
    
    env_status = {}
    for var in required_vars:
        value = os.getenv(var)
        env_status[var] = {
            'set': bool(value),
            'length': len(value) if value else 0
        }
    
    return env_status

def check_services() -> Dict:
    """Check service connectivity"""
    services = {
        'neo4j': 'http://localhost:7474',
        'chromadb': 'http://localhost:8000/api/v1/heartbeat',
        'api_server': 'http://localhost:8080/health'
    }
    
    service_status = {}
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            service_status[name] = {
                'status': 'UP' if response.status_code == 200 else f'ERROR_{response.status_code}',
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            service_status[name] = {
                'status': 'DOWN',
                'error': str(e)
            }
    
    return service_status

def check_api_endpoints() -> Dict:
    """Test API endpoints"""
    endpoints = [
        ('GET', '/health'),
        ('GET', '/memory/status'),
        ('GET', '/env/status')
    ]
    
    endpoint_status = {}
    base_url = 'http://localhost:8080'
    
    for method, path in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f'{base_url}{path}', timeout=5)
            
            endpoint_status[path] = {
                'status': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        except Exception as e:
            endpoint_status[path] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    return endpoint_status

def check_external_apis() -> Dict:
    """Test external API connectivity"""
    api_status = {}
    
    # Test Mem0
    mem0_key = os.getenv('MEM0_API_KEY')
    if mem0_key:
        try:
            response = requests.get(
                'https://api.mem0.ai/v1/memories',
                headers={'Authorization': f'Bearer {mem0_key}'},
                timeout=10
            )
            api_status['mem0'] = {
                'reachable': response.status_code in [200, 401],  # 401 is ok - means API is up
                'status_code': response.status_code
            }
        except Exception as e:
            api_status['mem0'] = {
                'reachable': False,
                'error': str(e)
            }
    
    # Test SuperMemory
    supermemory_key = os.getenv('SUPERMEMORY_API_KEY')
    supermemory_url = os.getenv('SUPERMEMORY_BASE_URL', 'https://api.supermemory.ai')
    if supermemory_key:
        try:
            response = requests.get(
                f'{supermemory_url}/api/health',
                headers={'Authorization': f'Bearer {supermemory_key}'},
                timeout=10
            )
            api_status['supermemory'] = {
                'reachable': response.status_code in [200, 401],
                'status_code': response.status_code
            }
        except Exception as e:
            api_status['supermemory'] = {
                'reachable': False,
                'error': str(e)
            }
    
    return api_status

def main():
    print("🏥 GlacierEQ Memory Master - Comprehensive Health Check")
    print("======================================================")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
    
    # Environment check
    print("🔧 Environment Configuration:")
    env_status = check_environment()
    for var, status in env_status.items():
        icon = "✅" if status['set'] else "❌"
        print(f"  {icon} {var}: {'SET' if status['set'] else 'MISSING'}")
    
    # Service connectivity
    print("\n🐳 Service Connectivity:")
    service_status = check_services()
    for name, status in service_status.items():
        if status['status'] == 'UP':
            print(f"  ✅ {name}: UP ({status['response_time']:.3f}s)")
        else:
            print(f"  ❌ {name}: {status['status']}")
            if 'error' in status:
                print(f"     Error: {status['error']}")
    
    # API endpoints
    print("\n📡 API Endpoints:")
    endpoint_status = check_api_endpoints()
    for path, status in endpoint_status.items():
        if status['status'] == 200:
            print(f"  ✅ {path}: OK ({status['response_time']:.3f}s)")
        else:
            print(f"  ❌ {path}: {status['status']}")
    
    # External APIs
    print("\n🌐 External API Connectivity:")
    api_status = check_external_apis()
    for name, status in api_status.items():
        if status['reachable']:
            print(f"  ✅ {name}: REACHABLE")
        else:
            print(f"  ❌ {name}: UNREACHABLE")
            if 'error' in status:
                print(f"     Error: {status['error']}")
    
    # Overall status
    all_services_up = all(s['status'] == 'UP' for s in service_status.values())
    all_apis_ok = all(s['status'] == 200 for s in endpoint_status.values())
    external_apis_ok = all(s['reachable'] for s in api_status.values())
    
    print("\n📊 SYSTEM STATUS:")
    print(f"  Services: {'✅ ALL UP' if all_services_up else '❌ ISSUES DETECTED'}")
    print(f"  API Endpoints: {'✅ ALL OK' if all_apis_ok else '❌ ISSUES DETECTED'}")
    print(f"  External APIs: {'✅ ALL REACHABLE' if external_apis_ok else '⚠️  SOME UNREACHABLE'}")
    
    if all_services_up and all_apis_ok:
        print("\n🎉 SYSTEM HEALTHY - Ready for operation!")
        print("\n🚀 Next Steps:")
        print("   1. Run Phase 1 migration: python3 scripts/migration-helper.py")
        print("   2. Configure Sigma File Manager 2 with ui/sigma/config.json")
        print("   3. Test memory operations:")
        print("      curl -X POST http://localhost:8080/memory/write -d '{\"content\":\"test\",\"entity\":\"test\"}'")
        return 0
    else:
        print("\n⚠️  SYSTEM ISSUES DETECTED - Review errors above")
        return 1

if __name__ == '__main__':
    sys.exit(main())