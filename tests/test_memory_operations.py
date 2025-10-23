#!/usr/bin/env python3
"""
Memory Operations Tests
End-to-end testing for write/search/forget operations
"""

import pytest
import asyncio
import json
from datetime import datetime

# Import components for testing
import sys
import os
sys.path.append('..')

class TestMemoryOperations:
    
    @pytest.fixture
    def sample_memory_data(self):
        return {
            'content': 'Test memory for automated testing - Case 1FDV-23-0001009',
            'entity': 'test_entity_automated',
            'classification': 'general',
            'metadata': {
                'test': True,
                'created_by': 'automated_test',
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    @pytest.mark.asyncio
    async def test_memory_write_search_forget_flow(self, sample_memory_data):
        """Test complete memory lifecycle"""
        try:
            from core.memory_orchestrator.aggregator_mcp import MemoryAggregator
            aggregator = MemoryAggregator()
            
            # Test write
            write_result = await aggregator.write_memory(
                sample_memory_data['content'],
                sample_memory_data['entity'],
                sample_memory_data['classification'],
                sample_memory_data['metadata']
            )
            
            assert write_result['success'] == True
            print(f"✅ Memory write successful: {sample_memory_data['entity']}")
            
            # Test search
            search_results = await aggregator.search_memory(
                'automated testing',
                sample_memory_data['entity'],
                limit=5
            )
            
            assert len(search_results) > 0
            print(f"✅ Memory search successful: {len(search_results)} results")
            
            # Test forget (if memory has ID)
            if write_result.get('providers', {}).get('mem0', {}).get('id'):
                memory_id = write_result['providers']['mem0']['id']
                forget_result = await aggregator.forget_memory(
                    memory_id,
                    'automated_test_cleanup'
                )
                
                assert forget_result['forgotten'] == True
                print(f"✅ Memory forget successful: {memory_id}")
            
        except Exception as e:
            pytest.fail(f"Memory operations test failed: {e}")
    
    @pytest.mark.asyncio 
    async def test_neo4j_connectivity(self):
        """Test Neo4j graph database connectivity"""
        try:
            from graph.neo4j_client import Neo4jClient
            client = Neo4jClient()
            
            if not client.driver:
                pytest.skip("Neo4j not available - skipping graph tests")
            
            # Test basic query
            result = await client.cypher("RETURN 'test' as message")
            assert 'records' in result
            assert len(result['records']) == 1
            assert result['records'][0]['message'] == 'test'
            
            print("✅ Neo4j connectivity test passed")
            
            # Test memory stats
            stats = await client.get_memory_stats()
            assert 'memory_count' in stats or stats == {}
            
            print("✅ Neo4j memory stats test passed")
            
            client.close()
            
        except Exception as e:
            pytest.fail(f"Neo4j connectivity test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_policy_engine(self):
        """Test policy engine functionality"""
        try:
            from core.memory_orchestrator.policy_engine import PolicyEngine
            engine = PolicyEngine()
            
            # Test TTL checking
            test_memory = {
                'classification': 'general',
                'timestamp': '2024-01-01T00:00:00Z'  # Old timestamp
            }
            
            expired = engine.check_ttl_expired(test_memory)
            print(f"✅ TTL check test: {expired}")
            
            # Test tombstone creation
            tombstone = engine.create_tombstone('test_123', 'automated_test')
            assert 'original_id' in tombstone
            assert tombstone['original_id'] == 'test_123'
            
            print("✅ Policy engine tests passed")
            
        except Exception as e:
            pytest.fail(f"Policy engine test failed: {e}")

if __name__ == '__main__':
    # Run tests directly
    pytest.main([__file__, '-v'])