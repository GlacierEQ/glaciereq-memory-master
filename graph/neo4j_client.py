#!/usr/bin/env python3
"""
Neo4j Client - Graph Memory Backend
Fixed async implementation and import paths
"""

import os
from neo4j import GraphDatabase
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import asyncio

class Neo4jClient:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print(f"✅ Neo4j connected: {self.uri}")
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            self.driver = None
    
    async def cypher(self, query: str, params: Dict = None) -> Dict:
        """Execute Cypher query (async wrapper)"""
        if not self.driver:
            return {'error': 'No Neo4j connection'}
        
        try:
            # Run in thread pool to make async
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._execute_cypher, query, params)
            return result
        except Exception as e:
            print(f"❌ Cypher execution failed: {e}")
            return {'error': str(e)}
    
    def _execute_cypher(self, query: str, params: Dict = None) -> Dict:
        """Synchronous Cypher execution"""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            records = [record.data() for record in result]
            
            return {
                'records': records,
                'count': len(records),
                'query': query
            }
    
    async def create_memory_node(self, content: str, entity: str, metadata: Dict = None) -> Dict:
        """Create memory node with relationships"""
        query = """
        CREATE (m:Memory {
            id: randomUUID(),
            content: $content,
            entity: $entity,
            created_at: datetime(),
            metadata: $metadata
        })
        WITH m
        MERGE (e:Entity {name: $entity})
        CREATE (m)-[:RELATES_TO]->(e)
        RETURN m.id as memory_id, e.name as entity_name
        """
        
        params = {
            'content': content,
            'entity': entity,
            'metadata': json.dumps(metadata or {})
        }
        
        return await self.cypher(query, params)
    
    async def search_memories(self, query: str, entity: str = None, limit: int = 10) -> List[Dict]:
        """Search memories using full-text and graph traversal"""
        if entity:
            cypher = """
            MATCH (m:Memory)-[:RELATES_TO]->(e:Entity {name: $entity})
            WHERE m.content CONTAINS $query
            RETURN m, e
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            params = {'query': query, 'entity': entity, 'limit': limit}
        else:
            cypher = """
            MATCH (m:Memory)
            WHERE m.content CONTAINS $query
            OPTIONAL MATCH (m)-[:RELATES_TO]->(e:Entity)
            RETURN m, e
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            params = {'query': query, 'limit': limit}
        
        result = await self.cypher(cypher, params)
        return result.get('records', [])
    
    async def get_memory_stats(self) -> Dict:
        """Get memory graph statistics"""
        query = """
        MATCH (m:Memory)
        OPTIONAL MATCH (e:Entity)
        OPTIONAL MATCH (c:CustodyEvent)
        RETURN 
            count(DISTINCT m) as memory_count,
            count(DISTINCT e) as entity_count,
            count(DISTINCT c) as custody_events
        """
        
        result = await self.cypher(query)
        return result.get('records', [{}])[0] if result.get('records') else {}
    
    async def traverse_graph(self, start_entity: str, relationship: str, depth: int = 3) -> Dict:
        """Traverse memory graph for provenance"""
        query = f"""
        MATCH path = (start:Entity {{name: $start_entity}})
                    -[:{relationship}*1..{depth}]->(end)
        RETURN path, nodes(path) as nodes, relationships(path) as rels
        LIMIT 100
        """
        
        params = {'start_entity': start_entity}
        return await self.cypher(query, params)
    
    async def create_chain_of_custody(self, evidence_id: str, handler: str, action: str) -> Dict:
        """Create chain of custody relationship"""
        query = """
        MATCH (e:Evidence {id: $evidence_id})
        CREATE (c:CustodyEvent {
            id: randomUUID(),
            handler: $handler,
            action: $action,
            timestamp: datetime()
        })
        CREATE (e)-[:CUSTODY_EVENT]->(c)
        RETURN c.id as custody_id
        """
        
        params = {
            'evidence_id': evidence_id,
            'handler': handler,
            'action': action
        }
        
        return await self.cypher(query, params)
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

if __name__ == '__main__':
    # Test Neo4j operations
    async def test_neo4j():
        client = Neo4jClient()
        if client.driver:
            print("Testing Neo4j operations...")
            
            # Test basic query
            result = await client.cypher("RETURN 'Hello Neo4j' as message")
            print(f"Test query result: {result}")
            
            # Test memory stats
            stats = await client.get_memory_stats()
            print(f"Memory stats: {stats}")
            
            client.close()
        else:
            print("❌ Neo4j not connected - check configuration")
    
    asyncio.run(test_neo4j())