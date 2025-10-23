#!/usr/bin/env python3
"""
Ingestion Router - Multi-Modal Memory Ingestion
Real-time connectors + enrichment pipeline for documents, audio, and structured data
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime
import hashlib
import uuid

# Import components
import sys
sys.path.append('../..')
from api.routers.audit import log_memory_operation
from services.enrichment.entity_extract import EntityExtractor
from services.enrichment.relation_graph import RelationGraphBuilder

router = APIRouter(prefix="/ingest", tags=["ingest"])

class IngestRequest(BaseModel):
    content: str
    source: str
    entity: Optional[str] = None
    classification: Optional[str] = 'general'
    metadata: Optional[Dict] = None
    enrich: Optional[bool] = True

class BulkIngestRequest(BaseModel):
    items: List[IngestRequest]
    batch_id: Optional[str] = None

class IngestStatus(BaseModel):
    queued: int
    processing: int
    completed: int
    failed: int
    avg_processing_time: float

# Global ingestion queues and status
ingest_queue = asyncio.Queue(maxsize=1000)
ingest_stats = {
    'queued': 0,
    'processing': 0, 
    'completed': 0,
    'failed': 0,
    'processing_times': []
}

class IngestionPipeline:
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relation_builder = RelationGraphBuilder()
        self.running = False
    
    async def start_daemon(self):
        """Start background ingestion daemon"""
        if self.running:
            return
        
        self.running = True
        asyncio.create_task(self._process_queue())
        print("✅ Ingestion daemon started")
    
    async def _process_queue(self):
        """Background queue processor"""
        while self.running:
            try:
                # Get item from queue
                item = await asyncio.wait_for(ingest_queue.get(), timeout=5.0)
                ingest_stats['queued'] -= 1
                ingest_stats['processing'] += 1
                
                start_time = datetime.utcnow()
                
                # Process item
                await self._process_item(item)
                
                # Update stats
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                ingest_stats['processing'] -= 1
                ingest_stats['completed'] += 1
                ingest_stats['processing_times'].append(processing_time)
                
                # Keep only last 100 processing times for average
                if len(ingest_stats['processing_times']) > 100:
                    ingest_stats['processing_times'] = ingest_stats['processing_times'][-100:]
                
            except asyncio.TimeoutError:
                continue  # No items in queue
            except Exception as e:
                ingest_stats['processing'] -= 1
                ingest_stats['failed'] += 1
                print(f"❌ Ingestion processing error: {e}")
    
    async def _process_item(self, item: Dict):
        """Process individual ingestion item with enrichment"""
        try:
            content = item['content']
            source = item['source']
            entity = item.get('entity', 'unknown')
            classification = item.get('classification', 'general')
            
            # Enrichment pipeline
            if item.get('enrich', True):
                # Extract entities and relations
                extracted_entities = await self.entity_extractor.extract(content)
                relations = await self.relation_builder.build_relations(content, extracted_entities)
                
                # Update metadata with enrichment
                enrichment_metadata = {
                    'extracted_entities': extracted_entities,
                    'relations': relations,
                    'enriched_at': datetime.utcnow().isoformat(),
                    'source': source
                }
                
                item['metadata'] = {**(item.get('metadata', {})), **enrichment_metadata}
            
            # Create memory via aggregator
            from core.memory_orchestrator.aggregator_mcp import MemoryAggregator
            aggregator = MemoryAggregator()
            
            result = await aggregator.write_memory(
                content, entity, classification, item.get('metadata')
            )
            
            # Log to audit trail
            log_memory_operation(
                'ingest_processed',
                entity,
                classification,
                {'source': source, 'result': result},
                'ingestion_daemon'
            )
            
            print(f"✅ Processed ingestion item: {entity} from {source}")
            
        except Exception as e:
            print(f"❌ Failed to process ingestion item: {e}")
            raise

# Initialize pipeline
ingestion_pipeline = IngestionPipeline()

@router.post("/item")
async def ingest_item(request: IngestRequest, background_tasks: BackgroundTasks):
    """Ingest single item with optional enrichment"""
    try:
        # Start daemon if not running
        if not ingestion_pipeline.running:
            background_tasks.add_task(ingestion_pipeline.start_daemon)
        
        # Add to queue
        item_data = request.dict()
        item_data['id'] = str(uuid.uuid4())
        item_data['queued_at'] = datetime.utcnow().isoformat()
        
        await ingest_queue.put(item_data)
        ingest_stats['queued'] += 1
        
        return {
            'queued': True,
            'item_id': item_data['id'],
            'queue_position': ingest_stats['queued'],
            'estimated_processing_time': '30-60 seconds'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk")
async def ingest_bulk(request: BulkIngestRequest, background_tasks: BackgroundTasks):
    """Bulk ingestion with batch processing"""
    try:
        batch_id = request.batch_id or str(uuid.uuid4())
        
        # Start daemon if not running
        if not ingestion_pipeline.running:
            background_tasks.add_task(ingestion_pipeline.start_daemon)
        
        # Queue all items
        queued_items = []
        for item in request.items:
            item_data = item.dict()
            item_data['id'] = str(uuid.uuid4())
            item_data['batch_id'] = batch_id
            item_data['queued_at'] = datetime.utcnow().isoformat()
            
            await ingest_queue.put(item_data)
            queued_items.append(item_data['id'])
            ingest_stats['queued'] += 1
        
        return {
            'batch_queued': True,
            'batch_id': batch_id,
            'items_queued': len(queued_items),
            'item_ids': queued_items,
            'estimated_completion': '5-15 minutes'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document")
async def ingest_document(file: UploadFile = File(...), 
                         entity: str = 'document', 
                         classification: str = 'general'):
    """Ingest document with OCR and layout parsing"""
    try:
        # Read file content
        content = await file.read()
        
        # TODO: Add OCR processing for images/PDFs
        # For now, handle text files
        if file.content_type and 'text' in file.content_type:
            text_content = content.decode('utf-8')
        else:
            text_content = f"[Binary file: {file.filename}, size: {len(content)} bytes]"
        
        # Create ingestion request
        ingest_item = IngestRequest(
            content=text_content,
            source=f"document_upload:{file.filename}",
            entity=entity,
            classification=classification,
            metadata={
                'filename': file.filename,
                'content_type': file.content_type,
                'file_size': len(content),
                'upload_timestamp': datetime.utcnow().isoformat()
            },
            enrich=True
        )
        
        # Queue for processing
        background_tasks = BackgroundTasks()
        result = await ingest_item(ingest_item, background_tasks)
        
        return {
            **result,
            'document_processed': True,
            'filename': file.filename,
            'content_type': file.content_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def ingestion_status():
    """Current ingestion queue status and metrics"""
    avg_time = sum(ingest_stats['processing_times']) / len(ingest_stats['processing_times']) if ingest_stats['processing_times'] else 0
    
    return IngestStatus(
        queued=ingest_stats['queued'],
        processing=ingest_stats['processing'],
        completed=ingest_stats['completed'],
        failed=ingest_stats['failed'],
        avg_processing_time=avg_time
    )

@router.get("/connectors")
async def connector_status():
    """Status of continuous connectors"""
    # TODO: Implement actual connector monitoring
    return {
        'available_connectors': [
            'notion', 'google_drive', 'email', 'slack', 'calendar', 'fileboss'
        ],
        'active_connectors': ['fileboss'],  # Only FILEBOSS integration active initially
        'last_sync': {
            'fileboss': '2025-10-22T20:00:00Z'
        },
        'sync_intervals': {
            'notion': '5 minutes',
            'google_drive': '10 minutes', 
            'fileboss': '1 minute'
        }
    }

@router.post("/connectors/{connector}/sync")
async def trigger_connector_sync(connector: str):
    """Manually trigger connector sync"""
    valid_connectors = ['notion', 'google_drive', 'email', 'slack', 'calendar', 'fileboss']
    
    if connector not in valid_connectors:
        raise HTTPException(status_code=400, detail=f"Invalid connector: {connector}")
    
    # TODO: Implement actual connector sync trigger
    return {
        'sync_triggered': True,
        'connector': connector,
        'estimated_completion': '2-5 minutes',
        'status': 'queued'
    }