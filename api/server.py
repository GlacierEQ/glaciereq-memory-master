#!/usr/bin/env python3
"""
GlacierEQ Memory Master API Server
Unified REST API for Sigma frontend and external integrations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
from typing import Dict, List, Optional

# Import core components
sys.path.append('..')
from core.memory_orchestrator.aggregator_mcp import MemoryAggregator
from graph.neo4j_client import Neo4jClient

app = FastAPI(title="GlacierEQ Memory Master API")

# CORS for Sigma frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
memory_aggregator = MemoryAggregator()
neo4j_client = Neo4jClient()

# Pydantic models
class MemoryWrite(BaseModel):
    content: str
    entity: str
    classification: Optional[str] = 'general'
    metadata: Optional[Dict] = None

class MemorySearch(BaseModel):
    query: str
    entity: Optional[str] = None
    limit: Optional[int] = 10
    filters: Optional[Dict] = None

class MemoryForget(BaseModel):
    memory_id: str
    reason: str

class CypherQuery(BaseModel):
    query: str
    params: Optional[Dict] = None

# Health endpoints
@app.get("/health")
async def health():
    """System health check"""
    neo4j_status = "connected" if neo4j_client.driver else "disconnected"
    
    return {
        "status": "ok",
        "services": {
            "neo4j": neo4j_status,
            "mem0": "configured" if os.getenv('MEM0_API_KEY') else "missing_key",
            "supermemory": "configured" if os.getenv('SUPERMEMORY_API_KEY') else "missing_key"
        },
        "case_number": "1FDV-23-0001009"
    }

@app.get("/memory/status")
async def memory_status():
    """Memory system status"""
    stats = await neo4j_client.get_memory_stats() if neo4j_client.driver else {}
    
    return {
        "graph_stats": stats,
        "providers": {
            "mem0": {"enabled": bool(os.getenv('MEM0_API_KEY'))},
            "supermemory": {"enabled": bool(os.getenv('SUPERMEMORY_API_KEY'))},
            "neo4j": {"enabled": bool(neo4j_client.driver)}
        }
    }

# Memory operations
@app.post("/memory/write")
async def write_memory(request: MemoryWrite):
    """Write memory to all providers"""
    try:
        result = await memory_aggregator.write_memory(
            request.content,
            request.entity,
            request.classification,
            request.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search")
async def search_memory(request: MemorySearch):
    """Search memories across all providers"""
    try:
        results = await memory_aggregator.search_memory(
            request.query,
            request.entity,
            request.limit,
            request.filters
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/forget")
async def forget_memory(request: MemoryForget):
    """Forget memory with tombstone policy"""
    try:
        result = await memory_aggregator.forget_memory(
            request.memory_id,
            request.reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Graph operations
@app.post("/graph/cypher")
async def run_cypher(request: CypherQuery):
    """Execute Cypher query"""
    try:
        result = await neo4j_client.cypher(request.query, request.params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/graph/traverse")
async def traverse_graph(start_entity: str, relationship: str, depth: int = 3):
    """Traverse memory graph"""
    try:
        result = await neo4j_client.traverse_graph(start_entity, relationship, depth)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Environment and ops
@app.get("/env/status")
async def env_status():
    """Environment configuration status"""
    required_vars = [
        'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
        'MEM0_API_KEY', 'SUPERMEMORY_API_KEY'
    ]
    
    status = {}
    for var in required_vars:
        status[var] = "set" if os.getenv(var) else "missing"
    
    return {
        "environment": status,
        "case_number": os.getenv('CASE_NUMBER', '1FDV-23-0001009'),
        "forensic_logging": os.getenv('FORENSIC_LOGGING', 'true')
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)