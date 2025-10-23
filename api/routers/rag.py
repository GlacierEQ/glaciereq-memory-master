#!/usr/bin/env python3
"""
Graph-RAG Router - Hybrid Retrieval with Provenance
Blends semantic vectors + graph traversal with learned ranking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import numpy as np
from datetime import datetime

# Import components
import sys
sys.path.append('../..')
from graph.neo4j_client import Neo4jClient
from providers.supermemory import SuperMemoryProvider
from providers.mem0 import Mem0Provider

router = APIRouter(prefix="/rag", tags=["rag"])

class RAGQuery(BaseModel):
    query: str
    entity: Optional[str] = None
    limit: Optional[int] = 10
    include_provenance: Optional[bool] = True
    confidence_threshold: Optional[float] = 0.7
    max_graph_depth: Optional[int] = 3

class RAGResponse(BaseModel):
    results: List[Dict[str, Any]]
    provenance: Optional[List[Dict]] = None
    confidence_scores: Optional[Dict] = None
    execution_time: Optional[float] = None

class GraphRAG:
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.supermemory = SuperMemoryProvider()
        self.mem0 = Mem0Provider()
    
    async def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Semantic vector search via SuperMemory/Mem0"""
        # Fast path: SuperMemory
        results = await self.supermemory.search(query, limit)
        
        # Fallback: Mem0 if insufficient results
        if len(results) < limit:
            mem0_results = await self.mem0.search(query, limit=limit-len(results))
            results.extend(mem0_results)
        
        # Add semantic scores
        for i, result in enumerate(results):
            result['semantic_score'] = 1.0 - (i * 0.1)  # Simple ranking
            result['search_type'] = 'semantic'
        
        return results
    
    async def graph_search(self, query: str, entity: str = None, depth: int = 3) -> List[Dict]:
        """Graph traversal search with entity context"""
        if not self.neo4j.driver:
            return []
        
        # Build entity-aware Cypher query
        if entity:
            cypher = """
            MATCH (start:Entity {name: $entity})
            MATCH path = (start)-[*1..{depth}]-(m:Memory)
            WHERE m.content CONTAINS $query
            WITH m, path, length(path) as path_length
            OPTIONAL MATCH (m)-[:CUSTODY_EVENT]->(c:CustodyEvent)
            OPTIONAL MATCH (m)-[:DERIVED_FROM]->(source:Memory)
            RETURN m, path, path_length, collect(c) as custody, collect(source) as sources
            ORDER BY path_length ASC, m.created_at DESC
            LIMIT $limit
            """.format(depth=depth)
            
            params = {'entity': entity, 'query': query, 'limit': 20}
        else:
            cypher = """
            MATCH (m:Memory)
            WHERE m.content CONTAINS $query
            OPTIONAL MATCH path = (m)-[:RELATES_TO*1..2]-(e:Entity)
            OPTIONAL MATCH (m)-[:CUSTODY_EVENT]->(c:CustodyEvent)
            RETURN m, path, collect(c) as custody
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            
            params = {'query': query, 'limit': 20}
        
        result = await self.neo4j.cypher(cypher, params)
        graph_results = []
        
        for record in result.get('records', []):
            memory = record.get('m', {})
            path_length = record.get('path_length', 1)
            custody = record.get('custody', [])
            
            # Calculate graph relevance score
            graph_score = 1.0 / (path_length + 1)  # Closer entities score higher
            if custody:
                graph_score += 0.2  # Boost for chain-of-custody
            
            graph_results.append({
                **memory,
                'graph_score': graph_score,
                'path_length': path_length,
                'custody_events': len(custody),
                'search_type': 'graph'
            })
        
        return graph_results
    
    async def hybrid_search(self, query: str, entity: str = None, limit: int = 10, include_provenance: bool = True) -> Dict:
        """Hybrid semantic + graph search with learned ranking"""
        start_time = datetime.utcnow()
        
        # Run searches in parallel
        semantic_task = asyncio.create_task(self.semantic_search(query, limit * 2))
        graph_task = asyncio.create_task(self.graph_search(query, entity, 3))
        
        semantic_results = await semantic_task
        graph_results = await graph_task
        
        # Hybrid ranking algorithm
        all_results = []
        result_map = {}  # Dedupe by content hash
        
        # Process semantic results
        for result in semantic_results:
            content_hash = hash(result.get('content', ''))
            if content_hash not in result_map:
                result_map[content_hash] = {
                    **result,
                    'hybrid_score': result.get('semantic_score', 0.5) * 0.6,
                    'signals': {'semantic': result.get('semantic_score', 0.5)}
                }
        
        # Blend in graph results (boost scores for matches)
        for result in graph_results:
            content_hash = hash(result.get('content', ''))
            graph_boost = result.get('graph_score', 0.5) * 0.4
            
            if content_hash in result_map:
                # Existing result - boost hybrid score
                result_map[content_hash]['hybrid_score'] += graph_boost
                result_map[content_hash]['signals']['graph'] = result.get('graph_score', 0.5)
                result_map[content_hash]['path_length'] = result.get('path_length')
                result_map[content_hash]['custody_events'] = result.get('custody_events', 0)
            else:
                # New graph-only result
                result_map[content_hash] = {
                    **result,
                    'hybrid_score': graph_boost + 0.3,  # Base score for graph-only
                    'signals': {'graph': result.get('graph_score', 0.5)}
                }
        
        # Sort by hybrid score and limit
        sorted_results = sorted(
            result_map.values(), 
            key=lambda x: x.get('hybrid_score', 0), 
            reverse=True
        )[:limit]
        
        # Add provenance if requested
        provenance = []
        if include_provenance and entity:
            prov_result = await self._get_provenance_trail(entity)
            provenance = prov_result.get('records', [])
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            'results': sorted_results,
            'provenance': provenance,
            'confidence_scores': {
                'semantic_weight': 0.6,
                'graph_weight': 0.4,
                'avg_confidence': np.mean([r.get('hybrid_score', 0) for r in sorted_results]) if sorted_results else 0
            },
            'execution_time': execution_time,
            'result_counts': {
                'semantic': len(semantic_results),
                'graph': len(graph_results),
                'hybrid': len(sorted_results)
            }
        }
    
    async def _get_provenance_trail(self, entity: str) -> Dict:
        """Get provenance trail for entity"""
        cypher = """
        MATCH path = (e:Entity {name: $entity})
                    -[:CUSTODY_EVENT|DERIVED_FROM*1..5]->(related)
        RETURN path, 
               nodes(path) as trail_nodes,
               [r in relationships(path) | {type: type(r), props: properties(r)}] as trail_rels
        ORDER BY length(path)
        LIMIT 50
        """
        
        return await self.neo4j.cypher(cypher, {'entity': entity})

# Initialize Graph-RAG engine
graph_rag = GraphRAG()

@router.post("/semantic", response_model=Dict)
async def semantic_search(query: RAGQuery):
    """Semantic vector search across memory providers"""
    try:
        results = await graph_rag.semantic_search(query.query, query.limit)
        return {
            'results': results,
            'search_type': 'semantic',
            'query': query.query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/graph", response_model=Dict)
async def graph_search(query: RAGQuery):
    """Graph traversal search with entity context"""
    try:
        results = await graph_rag.graph_search(
            query.query, 
            query.entity, 
            query.max_graph_depth or 3
        )
        return {
            'results': results,
            'search_type': 'graph',
            'query': query.query,
            'entity': query.entity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hybrid", response_model=Dict)
async def hybrid_search(query: RAGQuery):
    """Hybrid semantic + graph search with learned ranking"""
    try:
        result = await graph_rag.hybrid_search(
            query.query,
            query.entity,
            query.limit,
            query.include_provenance
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def rag_status():
    """RAG system status and performance metrics"""
    return {
        'semantic_provider': 'supermemory+mem0',
        'graph_provider': 'neo4j',
        'hybrid_ranking': 'enabled',
        'provenance_tracking': 'enabled',
        'confidence_threshold': 0.7
    }