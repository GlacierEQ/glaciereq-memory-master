#!/usr/bin/env python3
"""
Memory Aggregator MCP Server
Unified memory operations across Mem0, SuperMemory, Neo4j
"""

import asyncio
import json
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import providers
sys.path.append('../..')
from providers.mem0 import Mem0Provider
from providers.supermemory import SuperMemoryProvider
from graph.neo4j_client import Neo4jClient

class MemoryAggregator:
    def __init__(self):
        self.mem0 = Mem0Provider()
        self.supermemory = SuperMemoryProvider()
        self.neo4j = Neo4jClient()
        self.policies = self._load_policies()
    
    def _load_policies(self) -> Dict:
        """Load memory policies from config"""
        try:
            with open('policies/memory.yaml', 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except:
            return {
                'ttl_days': {'privileged': None, 'general': 365},
                'tombstone': True,
                'redaction': True
            }
    
    async def write_memory(self, content: str, entity: str, classification: str = 'general', metadata: Dict = None) -> Dict:
        """Write memory to all providers with sovereignty mirroring"""
        timestamp = datetime.utcnow().isoformat()
        full_metadata = {
            'entity': entity,
            'classification': classification,
            'timestamp': timestamp,
            'case_number': '1FDV-23-0001009',
            **(metadata or {})
        }
        
        results = {}
        
        # Primary: Write to Mem0 (system of record)
        mem0_result = await self.mem0.write(content, entity, full_metadata)
        results['mem0'] = mem0_result
        
        # Acceleration: Mirror to SuperMemory
        supermemory_result = await self.supermemory.write(content, full_metadata)
        results['supermemory'] = supermemory_result
        
        # Sovereignty: Create graph node
        neo4j_result = await self.neo4j.create_memory_node(content, entity, full_metadata)
        results['neo4j'] = neo4j_result
        
        return {
            'success': True,
            'providers': results,
            'metadata': full_metadata
        }
    
    async def search_memory(self, query: str, entity: str = None, limit: int = 10, filters: Dict = None) -> List[Dict]:
        """Search across all providers with acceleration priority"""
        results = []
        
        # Fast path: SuperMemory acceleration
        supermemory_results = await self.supermemory.search(query, limit, filters)
        if supermemory_results:
            results.extend([{**r, 'source': 'supermemory'} for r in supermemory_results])
        
        # Fallback: Mem0 comprehensive search
        if len(results) < limit:
            mem0_results = await self.mem0.search(query, entity, limit - len(results), filters)
            results.extend([{**r, 'source': 'mem0'} for r in mem0_results])
        
        return results

# MCP Server Implementation (stdio)
async def handle_mcp_request(request: Dict) -> Dict:
    """Handle MCP requests"""
    aggregator = MemoryAggregator()
    method = request.get('method')
    params = request.get('params', {})
    
    try:
        if method == 'write_memory':
            return await aggregator.write_memory(
                params.get('content'),
                params.get('entity'),
                params.get('classification', 'general'),
                params.get('metadata')
            )
        elif method == 'search_memory':
            return await aggregator.search_memory(
                params.get('query'),
                params.get('entity'),
                params.get('limit', 10),
                params.get('filters')
            )
        else:
            return {'error': f'Unknown method: {method}'}
            
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    # MCP stdio server
    while True:
        try:
            line = input()
            request = json.loads(line)
            response = asyncio.run(handle_mcp_request(request))
            print(json.dumps(response))
            sys.stdout.flush()
        except EOFError:
            break
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.stdout.flush()