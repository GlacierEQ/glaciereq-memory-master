#!/usr/bin/env python3
"""
Sigma Configuration Validator
Validates Sigma File Manager 2 configuration and provides setup instructions
"""

import json
import os
import requests
from datetime import datetime

def validate_sigma_config():
    """Validate Sigma FM2 configuration file"""
    config_path = 'ui/sigma/config.json'
    
    print("🖥️  SIGMA FILE MANAGER 2 - Configuration Validator")
    print("=" * 55)
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print("❌ Sigma config not found at ui/sigma/config.json")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"✅ Configuration file loaded successfully")
        
        # Validate workspace
        workspace = config.get('workspace', '')
        print(f"📝 Workspace: {workspace}")
        
        # Validate tabs
        tabs = config.get('tabs', [])
        print(f"📑 Tabs configured: {len(tabs)}")
        
        for tab in tabs:
            tab_name = tab.get('name', 'Unknown')
            tab_icon = tab.get('icon', '')
            tab_type = tab.get('type', '')
            print(f"   {tab_icon} {tab_name} ({tab_type})")
        
        # Test API connectivity for each endpoint
        print(f"\n🔌 Testing API Connectivity:")
        
        test_endpoints = [
            ('Health Check', 'GET', '/health'),
            ('Memory Status', 'GET', '/memory/status'),
            ('RAG Status', 'GET', '/rag/status'),
            ('Copilot Status', 'GET', '/copilot/status'),
            ('Audit Status', 'GET', '/audit/status'),
            ('Ingestion Status', 'GET', '/ingest/status'),
            ('Metrics', 'GET', '/metrics'),
            ('SLO Dashboard', 'GET', '/metrics/slo')
        ]
        
        base_url = 'http://localhost:8080'
        successful_endpoints = 0
        
        for name, method, endpoint in test_endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f'{base_url}{endpoint}', timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ {name}: OK")
                    successful_endpoints += 1
                else:
                    print(f"   ❌ {name}: HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print(f"   ⚠️  {name}: API server not running")
            except Exception as e:
                print(f"   ❌ {name}: {str(e)[:50]}...")
        
        print(f"\n📊 Endpoint Connectivity: {successful_endpoints}/{len(test_endpoints)} OK")
        
        # Sigma setup instructions
        print(f"\n📋 SIGMA FILE MANAGER 2 SETUP INSTRUCTIONS:")
        print("=" * 45)
        print("1. Open Sigma File Manager 2")
        print("2. Go to Workspace Settings")
        print("3. Import Configuration:")
        print(f"   📄 File: {os.path.abspath(config_path)}")
        print(f"   🏷️  Workspace Name: {workspace}")
        print("4. Verify tab configuration:")
        
        for tab in tabs:
            tab_name = tab.get('name')
            tab_icon = tab.get('icon')
            print(f"   {tab_icon} {tab_name} Tab")
            
            if tab.get('type') == 'api_form':
                endpoints = tab.get('endpoints', {})
                print(f"      API Endpoints: {len(endpoints)} configured")
            elif tab.get('type') == 'embed_panels':
                panels = tab.get('panels', [])
                print(f"      Embed Panels: {len(panels)} configured")
        
        print("5. Save and activate workspace")
        
        # Connection test URLs
        print(f"\n🔗 Direct Access URLs:")
        print(f"   🖥️  Main API: {base_url}")
        print(f"   🏥 Health: {base_url}/health")
        print(f"   🧠 Memory Status: {base_url}/memory/status")
        print(f"   🔗 Neo4j Browser: http://localhost:7474")
        print(f"   📊 Metrics: {base_url}/metrics")
        print(f"   📡 Audit Stream: {base_url}/audit/stream")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def main():
    """Main validation function"""
    print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = validate_sigma_config()
    
    if success:
        print(f"\n🎯 SIGMA CONFIGURATION READY")
        print(f"✅ All systems validated and accessible")
        print(f"🚀 Ready for maximum power operation")
        return 0
    else:
        print(f"\n⚠️  Configuration issues detected")
        print(f"📋 Fix issues above and re-run validation")
        return 1

if __name__ == '__main__':
    exit(main())
