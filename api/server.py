#!/usr/bin/env python3
"""
GlacierEQ Memory Master API Server
Unified REST API with Graph-RAG, Copilots, Audit, Ingestion, and Self-Healing Ops
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import os
import sys
import time
import asyncio
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

# Import core components
sys.path.append('..')
from core.memory_orchestrator.aggregator_mcp import MemoryAggregator
from graph.neo4j_client import Neo4jClient
from observers.metrics import metrics, LatencyTimer
from api.routers.audit import log_memory_operation

# Import all routers
from api.routers.rag import router as rag_router
from api.routers.copilot import router as copilot_router  
from api.routers.audit import router as audit_router
from api.routers.ingest import router as ingest_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    print("🚀 Starting GlacierEQ Memory Master API Server")
    print("===============================================")
    
    # Set start time for uptime calculation
    app.state.start_time = time.time()
    
    # Initialize components
    print("⚙️ Initializing core components...")
    memory_aggregator = MemoryAggregator()
    neo4j_client = Neo4jClient()
    
    # Start background metrics collection
    print("📊 Starting metrics collection...")
    metrics_task = asyncio.create_task(_metrics_collector())
    
    print("✅ All systems initialized")
    print(f"🎯 API Server ready: http://localhost:8080")
    print(f"🔗 Neo4j Browser: http://localhost:7474")
    print(f"📊 Metrics: http://localhost:8080/metrics")
    print(f"📡 Audit Stream: http://localhost:8080/audit/stream")
    
    yield
    
    print("🛑 Shutting down GlacierEQ Memory Master")
    metrics_task.cancel()

# Create FastAPI app with lifespan
app = FastAPI(
    title="GlacierEQ Memory Master API",
    description="Sovereign Memory Architecture with Graph-RAG, Copilots, and Federal Compliance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for Sigma frontend and external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for embedded UI (if exists)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include all routers with metrics
app.include_router(rag_router)
app.include_router(copilot_router)
app.include_router(audit_router)
app.include_router(ingest_router)

# Initialize global components
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

# Middleware for automatic metrics collection
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for all API requests"""
    start_time = time.time()
    
    # Increment request counter
    metrics.increment_counter('api_requests_total')
    
    try:
        response = await call_next(request)
        
        # Record successful request latency
        latency_ms = (time.time() - start_time) * 1000
        endpoint = request.url.path.replace('/', '_').strip('_') or 'root'
        metrics.record_latency(f'api_latency_{endpoint}', latency_ms)
        
        return response
        
    except Exception as e:
        # Record error
        metrics.increment_counter('api_errors_total')
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_latency('api_error_latency', latency_ms)
        raise

# Core API endpoints
@app.get("/")
async def root():
    """API root with system overview"""
    return {
        "service": "GlacierEQ Memory Master API",
        "version": "1.0.0",
        "status": "operational",
        "case_support": "1FDV-23-0001009",
        "capabilities": [
            "memory_operations", "graph_rag", "domain_copilots", 
            "audit_compliance", "multi_modal_ingestion", "self_healing_ops"
        ],
        "endpoints": {
            "memory": "/memory/{write,search,forget}",
            "graph_rag": "/rag/{semantic,graph,hybrid}",
            "copilots": "/copilot/{legal,ops,research}",
            "audit": "/audit/{stream,trail,attest}",
            "ingestion": "/ingest/{item,bulk,document}",
            "metrics": "/metrics",
            "health": "/health"
        },
        "sigma_config": "ui/sigma/config.json"
    }

@app.get("/health")
async def health():
    """Comprehensive system health with SLO status"""
    neo4j_status = "connected" if neo4j_client.driver else "disconnected"
    
    # Check service connectivity
    services = {
        "neo4j": neo4j_status,
        "mem0": "configured" if os.getenv('MEM0_API_KEY') else "missing_key",
        "supermemory": "configured" if os.getenv('SUPERMEMORY_API_KEY') else "missing_key",
        "chromadb": "assumed_running"
    }
    
    # Get SLO status
    slo_dashboard = metrics.get_slo_dashboard()
    overall_health = slo_dashboard['overall_health']
    
    return {
        "status": "ok" if overall_health == "GREEN" else "degraded", 
        "overall_health": overall_health,
        "services": services,
        "slo_violations": len(slo_dashboard['violations']),
        "case_number": "1FDV-23-0001009",
        "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0,
        "memory_providers": ["mem0", "supermemory", "neo4j"]
    }

@app.get("/memory/status")
async def memory_status():
    """Memory system status and statistics"""
    with LatencyTimer('memory_status_latency'):
        stats = await neo4j_client.get_memory_stats() if neo4j_client.driver else {}
        
        return {
            "graph_stats": stats,
            "providers": {
                "mem0": {"enabled": bool(os.getenv('MEM0_API_KEY'))},
                "supermemory": {"enabled": bool(os.getenv('SUPERMEMORY_API_KEY'))},
                "neo4j": {"enabled": bool(neo4j_client.driver)}
            },
            "policy_engine": {"enabled": True},
            "audit_logging": {"enabled": True},
            "classification_support": ["general", "privileged", "evidence", "sensitive"]
        }

# Memory operations with metrics and audit
@app.post("/memory/write")
async def write_memory(request: MemoryWrite):
    """Write memory to all providers with audit logging"""
    with LatencyTimer('memory_write_latency'):
        try:
            result = await memory_aggregator.write_memory(
                request.content,
                request.entity,
                request.classification,
                request.metadata
            )
            
            # Log to audit trail
            log_memory_operation(
                'write_memory',
                request.entity,
                request.classification or 'general',
                {'content_length': len(request.content), 'providers': list(result.get('providers', {}).keys())}
            )
            
            metrics.increment_counter('memory_operations_total')
            return result
        except Exception as e:
            metrics.increment_counter('memory_write_errors_total')
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search")
async def search_memory(request: MemorySearch):
    """Search memories across all providers with audit logging"""
    with LatencyTimer('memory_search_latency'):
        try:
            results = await memory_aggregator.search_memory(
                request.query,
                request.entity,
                request.limit,
                request.filters
            )
            
            # Log to audit trail
            log_memory_operation(
                'search_memory',
                request.entity or 'global_search',
                'search_operation',
                {'query': request.query, 'result_count': len(results)}
            )
            
            metrics.increment_counter('memory_operations_total')
            return {"results": results, "count": len(results)}
        except Exception as e:
            metrics.increment_counter('memory_search_errors_total')
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/forget")
async def forget_memory(request: MemoryForget):
    """Forget memory with tombstone policy and audit trail"""
    with LatencyTimer('memory_forget_latency'):
        try:
            result = await memory_aggregator.forget_memory(
                request.memory_id,
                request.reason
            )
            
            # Log to audit trail  
            log_memory_operation(
                'forget_memory',
                'memory_deletion',
                'compliance_action',
                {'memory_id': request.memory_id, 'reason': request.reason, 'tombstone': True}
            )
            
            metrics.increment_counter('memory_operations_total')
            return result
        except Exception as e:
            metrics.increment_counter('memory_forget_errors_total')
            raise HTTPException(status_code=500, detail=str(e))

# Graph operations with metrics
@app.post("/graph/cypher")
async def run_cypher(request: CypherQuery):
    """Execute Cypher query with performance metrics"""
    with LatencyTimer('graph_query_latency'):
        try:
            result = await neo4j_client.cypher(request.query, request.params)
            metrics.increment_counter('graph_queries_total')
            return result
        except Exception as e:
            metrics.increment_counter('graph_query_errors_total')
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/graph/traverse")
async def traverse_graph(start_entity: str, relationship: str, depth: int = 3):
    """Traverse memory graph with metrics"""
    with LatencyTimer('graph_traversal_latency'):
        try:
            result = await neo4j_client.traverse_graph(start_entity, relationship, depth)
            metrics.increment_counter('graph_traversals_total')
            return result
        except Exception as e:
            metrics.increment_counter('graph_traversal_errors_total')
            raise HTTPException(status_code=500, detail=str(e))

# Metrics and observability endpoints
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics export"""
    return PlainTextResponse(
        metrics.get_prometheus_metrics(),
        media_type="text/plain"
    )

@app.get("/metrics/slo")
async def slo_dashboard():
    """SLO dashboard with violation status and remediation"""
    return metrics.get_slo_dashboard()

@app.post("/ops/remediate")
async def trigger_remediation(violation_type: str):
    """Manually trigger auto-remediation for specific issue"""
    if violation_type not in metrics.runbooks:
        raise HTTPException(status_code=400, detail=f"Unknown violation type: {violation_type}")
    
    try:
        # Create mock violation for manual remediation
        mock_violation = {
            'slo': f'manual_{violation_type}',
            'current_value': 999,
            'threshold': 100,
            'severity': 'high'
        }
        
        remediation_func = metrics.runbooks[violation_type]
        result = await remediation_func(mock_violation)
        
        # Log remediation to audit
        log_memory_operation(
            'manual_remediation',
            'system_ops',
            'operational',
            {'violation_type': violation_type, 'result': result}
        )
        
        return {
            'remediation_triggered': True,
            'type': violation_type,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/env/status")
async def env_status():
    """Environment configuration with security masking"""
    required_vars = [
        'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
        'MEM0_API_KEY', 'SUPERMEMORY_API_KEY'
    ]
    
    status = {}
    for var in required_vars:
        value = os.getenv(var)
        status[var] = {
            "set": bool(value),
            "length": len(value) if value else 0,
            "masked_value": f"{value[:4]}...{value[-4:]}" if value and len(value) > 8 else "[not set]"
        }
    
    return {
        "environment": status,
        "case_number": os.getenv('CASE_NUMBER', '1FDV-23-0001009'),
        "forensic_logging": os.getenv('FORENSIC_LOGGING', 'true'),
        "deployment_timestamp": datetime.utcnow().isoformat(),
        "system_health": metrics.get_slo_dashboard()['overall_health']
    }

@app.get("/migration/status")
async def migration_status():
    """Repository consolidation migration status"""
    # Check if Phase 1 directories exist
    phase1_modules = {
        'core/memory-orchestrator': 'quantum-memory-orchestrator',
        'core/master-grid': 'MCP-MASTER-OMNI-GRID', 
        'core/constellation': 'casey-custom-mcp-constellation',
        'core/quantum-matrix': 'GODMIND-quantum-intelligence-matrix'
    }
    
    migration_status = {}
    for module_path, source_repo in phase1_modules.items():
        module_exists = os.path.exists(module_path)
        has_files = len([f for f in os.listdir(module_path) if os.path.isfile(os.path.join(module_path, f))]) > 0 if module_exists else False
        
        migration_status[source_repo] = {
            'migrated': module_exists and has_files,
            'module_path': module_path,
            'status': 'COMPLETE' if module_exists and has_files else 'PENDING'
        }
    
    completed = sum(1 for status in migration_status.values() if status['migrated'])
    
    return {
        'phase': 'Phase 1 - Critical Memory Core',
        'progress': f'{completed}/{len(phase1_modules)}',
        'completion_percentage': (completed / len(phase1_modules)) * 100,
        'modules': migration_status,
        'next_phase': 'Phase 2 - Graph Memory Systems' if completed == len(phase1_modules) else None
    }

# Background metrics collector task
async def _metrics_collector():
    """Background task for system metrics and auto-remediation"""
    while True:
        try:
            # Update system metrics
            if neo4j_client.driver:
                stats = await neo4j_client.get_memory_stats()
                metrics.set_gauge('memory_count', stats.get('memory_count', 0))
                metrics.set_gauge('entity_count', stats.get('entity_count', 0))
                metrics.set_gauge('custody_events_count', stats.get('custody_events', 0))
            
            # Update ingestion queue metrics
            try:
                from api.routers.ingest import ingest_stats
                metrics.set_gauge('ingestion_queue_depth', ingest_stats['queued'])
                metrics.set_gauge('ingestion_processing', ingest_stats['processing'])
                metrics.set_gauge('ingestion_completed', ingest_stats['completed'])
                metrics.set_gauge('ingestion_failed', ingest_stats['failed'])
            except:
                pass  # Ingestion stats not available yet
            
            # Check for SLO violations and trigger auto-remediation
            violations = metrics.check_slo_violations()
            for violation in violations:
                if violation['severity'] == 'high':
                    remediation_type = violation['remediation']
                    if remediation_type in metrics.runbooks:
                        print(f"🚨 Auto-remediation triggered: {remediation_type}")
                        try:
                            remediation_result = await metrics.runbooks[remediation_type](violation)
                            
                            # Log remediation to audit
                            log_memory_operation(
                                'auto_remediation',
                                'system_ops',
                                'operational',
                                {'violation': violation, 'result': remediation_result}
                            )
                        except Exception as e:
                            print(f"❌ Auto-remediation failed for {remediation_type}: {e}")
            
            # Sleep for next collection cycle
            await asyncio.sleep(30)  # Collect every 30 seconds
            
        except Exception as e:
            print(f"⚠️  Metrics collection error: {e}")
            await asyncio.sleep(60)  # Longer sleep on error

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Launching GlacierEQ Memory Master API Server")
    print("===============================================")
    print(f"📅 Deployment: {datetime.utcnow().isoformat()}Z")
    print(f"🎯 Case Support: 1FDV-23-0001009")
    print(f"🔗 Architecture: Sovereign Memory + Graph Intelligence")
    print(f"🤖 Capabilities: Memory + RAG + Copilots + Audit + Ingestion + Self-Healing")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        log_level="info",
        access_log=True
    )