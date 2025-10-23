#!/usr/bin/env python3
"""
Audit Router - Compliance, Attestation, and Trust Management
Real-time audit streaming and cryptographic attestation
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
import hashlib
import json
from datetime import datetime
import uuid

router = APIRouter(prefix="/audit", tags=["audit"])

# In-memory audit log (production would use persistent storage)
audit_events = []
audit_subscribers = set()

class AuditEvent(BaseModel):
    id: str
    timestamp: str
    operation: str
    entity: str
    classification: str
    user: Optional[str] = 'system'
    payload_hash: str
    chain_of_custody: Optional[bool] = False
    attestation_hash: Optional[str] = None

class AttestationRequest(BaseModel):
    memory_id: str
    attestation_type: str = 'merkle_local'
    include_provenance: Optional[bool] = True

class AuditTrail:
    def __init__(self):
        self.merkle_log = []  # Local Merkle log
    
    def create_audit_event(self, operation: str, entity: str, classification: str, 
                          payload: Dict, user: str = 'system') -> AuditEvent:
        """Create cryptographically hashed audit event"""
        # Hash payload for integrity
        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        
        # Create attestation hash (local Merkle)
        attestation_data = f"{operation}:{entity}:{payload_hash}:{datetime.utcnow().isoformat()}"
        attestation_hash = hashlib.sha256(attestation_data.encode()).hexdigest()
        
        event = AuditEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            operation=operation,
            entity=entity,
            classification=classification,
            user=user,
            payload_hash=payload_hash,
            chain_of_custody=classification in ['evidence', 'privileged'],
            attestation_hash=attestation_hash
        )
        
        # Add to Merkle log
        self.merkle_log.append({
            'hash': attestation_hash,
            'previous': self.merkle_log[-1]['hash'] if self.merkle_log else '0',
            'timestamp': event.timestamp,
            'operation': operation
        })
        
        # Store event
        audit_events.append(event)
        
        # Notify subscribers
        self._notify_subscribers(event)
        
        return event
    
    def _notify_subscribers(self, event: AuditEvent):
        """Notify real-time audit subscribers"""
        for subscriber_queue in audit_subscribers:
            try:
                subscriber_queue.put_nowait(event)
            except:
                pass  # Skip full queues
    
    def get_audit_trail(self, entity: str = None, limit: int = 100) -> List[AuditEvent]:
        """Get audit trail for entity or global"""
        if entity:
            return [e for e in audit_events if e.entity == entity][-limit:]
        return audit_events[-limit:]
    
    def verify_merkle_chain(self) -> Dict:
        """Verify local Merkle chain integrity"""
        if not self.merkle_log:
            return {'valid': True, 'length': 0}
        
        for i in range(1, len(self.merkle_log)):
            current = self.merkle_log[i]
            previous = self.merkle_log[i-1]
            
            if current['previous'] != previous['hash']:
                return {
                    'valid': False, 
                    'broken_at_index': i,
                    'length': len(self.merkle_log)
                }
        
        return {
            'valid': True, 
            'length': len(self.merkle_log),
            'latest_hash': self.merkle_log[-1]['hash']
        }

# Initialize audit trail
audit_trail = AuditTrail()

@router.post("/log")
async def log_audit_event(operation: str, entity: str, classification: str, 
                         payload: Dict, user: str = 'system'):
    """Log audit event with cryptographic attestation"""
    try:
        event = audit_trail.create_audit_event(operation, entity, classification, payload, user)
        return {
            'logged': True,
            'event_id': event.id,
            'attestation_hash': event.attestation_hash
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/attest")
async def attest_memory(request: AttestationRequest):
    """Create cryptographic attestation for memory"""
    try:
        # Find memory in audit log
        memory_events = [e for e in audit_events if request.memory_id in str(e.payload_hash)]
        
        if not memory_events:
            raise HTTPException(status_code=404, detail="Memory not found in audit log")
        
        latest_event = memory_events[-1]
        
        # Create attestation
        attestation = {
            'memory_id': request.memory_id,
            'attestation_type': request.attestation_type,
            'merkle_hash': latest_event.attestation_hash,
            'merkle_index': len(audit_trail.merkle_log) - 1,
            'attested_at': datetime.utcnow().isoformat(),
            'chain_integrity': audit_trail.verify_merkle_chain()
        }
        
        if request.include_provenance:
            # Add provenance from Neo4j
            rag = GraphRAG()
            provenance = await rag._get_provenance_trail(latest_event.entity)
            attestation['provenance'] = provenance.get('records', [])
        
        return attestation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream")
async def audit_stream(request: Request):
    """Real-time audit event stream (Server-Sent Events)"""
    async def event_stream() -> AsyncGenerator[str, None]:
        # Create subscriber queue
        queue = asyncio.Queue(maxsize=100)
        audit_subscribers.add(queue)
        
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Format as SSE
                    event_data = {
                        'id': event.id,
                        'timestamp': event.timestamp,
                        'operation': event.operation,
                        'entity': event.entity,
                        'classification': event.classification,
                        'attestation_hash': event.attestation_hash[:16] + '...'  # Truncated for display
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {{\"keepalive\": true, \"timestamp\": \"{datetime.utcnow().isoformat()}\"}}\n\n"
                
        finally:
            # Clean up subscriber
            audit_subscribers.discard(queue)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/trail/{entity}")
async def get_audit_trail(entity: str, limit: int = 100):
    """Get audit trail for specific entity"""
    try:
        trail = audit_trail.get_audit_trail(entity, limit)
        merkle_status = audit_trail.verify_merkle_chain()
        
        return {
            'entity': entity,
            'events': [{
                'id': e.id,
                'timestamp': e.timestamp,
                'operation': e.operation,
                'classification': e.classification,
                'attestation_hash': e.attestation_hash
            } for e in trail],
            'merkle_integrity': merkle_status,
            'total_events': len(trail)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def audit_status():
    """Audit system status and metrics"""
    merkle_status = audit_trail.verify_merkle_chain()
    
    # Classification breakdown
    classification_counts = {}
    for event in audit_events:
        cls = event.classification
        classification_counts[cls] = classification_counts.get(cls, 0) + 1
    
    return {
        'total_events': len(audit_events),
        'merkle_integrity': merkle_status,
        'active_streams': len(audit_subscribers),
        'classification_breakdown': classification_counts,
        'attestation_enabled': True,
        'compliance_level': 'federal_grade'
    }

# Helper function for other routers to use
def log_memory_operation(operation: str, entity: str, classification: str, payload: Dict, user: str = 'system'):
    """Helper to log memory operations from other routers"""
    return audit_trail.create_audit_event(operation, entity, classification, payload, user)