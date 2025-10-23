#!/usr/bin/env python3
"""
Mem0 Provider - Real API Integration
Handles Mem0 operations with graph memory support
"""

import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class Mem0Provider:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('MEM0_API_KEY')
        self.base_url = 'https://api.mem0.ai/v1'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def write(self, content: str, entity: str = None, metadata: Dict = None) -> Dict:
        """Write memory to Mem0 with graph support"""
        payload = {
            'messages': [{
                'role': 'user',
                'content': content
            }],
            'user_id': entity or 'default',
            'metadata': metadata or {}
        }
        
        # Add graph memory config
        if os.getenv('MEM0_GRAPH_PROVIDER') == 'neo4j':
            payload['config'] = {
                'graph': {
                    'provider': 'neo4j',
                    'config': {
                        'url': os.getenv('NEO4J_URI'),
                        'username': os.getenv('NEO4J_USER'),
                        'password': os.getenv('NEO4J_PASSWORD')
                    }
                }
            }
        
        try:
            response = requests.post(
                f'{self.base_url}/memories',
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Mem0 write successful: {result.get('id')}")
            return result
            
        except Exception as e:
            print(f"❌ Mem0 write failed: {e}")
            return {'error': str(e)}
    
    async def search(self, query: str, user_id: str = None, limit: int = 10, filters: Dict = None) -> List[Dict]:
        """Search memories in Mem0"""
        params = {
            'query': query,
            'user_id': user_id or 'default',
            'limit': limit
        }
        
        if filters:
            params.update(filters)
        
        try:
            response = requests.get(
                f'{self.base_url}/memories/search',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            results = response.json()
            print(f"✅ Mem0 search returned {len(results.get('memories', []))} results")
            return results.get('memories', [])
            
        except Exception as e:
            print(f"❌ Mem0 search failed: {e}")
            return []