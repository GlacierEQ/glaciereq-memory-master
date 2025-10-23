#!/usr/bin/env python3
"""
SuperMemory Provider - Real API Integration
Handles SuperMemory operations for acceleration layer
"""

import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class SuperMemoryProvider:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SUPERMEMORY_API_KEY')
        self.base_url = os.getenv('SUPERMEMORY_BASE_URL', 'https://api.supermemory.ai')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def write(self, content: str, metadata: Dict = None) -> Dict:
        """Write to SuperMemory for acceleration"""
        payload = {
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/add',
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ SuperMemory write successful: {result.get('id')}")
            return result
            
        except Exception as e:
            print(f"❌ SuperMemory write failed: {e}")
            return {'error': str(e)}
    
    async def search(self, query: str, limit: int = 10, filters: Dict = None) -> List[Dict]:
        """Fast search via SuperMemory acceleration"""
        payload = {
            'query': query,
            'limit': limit,
            'filters': filters or {}
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/search',
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            results = response.json()
            print(f"✅ SuperMemory search returned {len(results.get('results', []))} results")
            return results.get('results', [])
            
        except Exception as e:
            print(f"❌ SuperMemory search failed: {e}")
            return []
    
    async def accelerated_recall(self, query: str, neo4j_client = None) -> List[Dict]:
        """SuperMemory acceleration with Neo4j fallback"""
        # Fast retrieval via SuperMemory
        results = await self.search(query)
        
        # Mirror to Neo4j for sovereignty if client provided
        if neo4j_client and results:
            await self._sync_to_graph(results, neo4j_client)
        
        return results
    
    async def _sync_to_graph(self, memories: List[Dict], neo4j_client) -> None:
        """Sync SuperMemory results to Neo4j graph"""
        for memory in memories:
            # Create memory node in graph
            cypher = """
            MERGE (m:Memory {id: $memory_id})
            SET m.content = $content,
                m.timestamp = $timestamp,
                m.source = 'supermemory',
                m.synced_at = datetime()
            """
            
            params = {
                'memory_id': memory.get('id'),
                'content': memory.get('content', ''),
                'timestamp': memory.get('timestamp', '')
            }
            
            await neo4j_client.cypher(cypher, params)
            
        print(f"✅ Synced {len(memories)} memories to Neo4j")