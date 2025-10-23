#!/usr/bin/env python3
"""
Entity Extraction Service
Extracts entities, relations, and metadata from content
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

class EntityExtractor:
    def __init__(self):
        # Entity patterns for legal domain
        self.entity_patterns = {
            'case_number': r'\b\d+[A-Z]+[- ]?\d+[- ]?\d+\b',  # 1FDV-23-0001009
            'court': r'\b(?:Court|Judge|Hon\.|Justice)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            'attorney': r'\b(?:Attorney|Counsel|Esq\.|Mr\.|Ms\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', 
            'date': r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b',
            'money': r'\$[\d,]+(?:\.\d{2})?\b',
            'phone': r'\b\d{3}[- ]?\d{3}[- ]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'address': r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct)\b',
            'person': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Simple first/last name
            'organization': r'\b[A-Z][A-Za-z\s&,]+(?:Inc|LLC|Corp|Company|Foundation|Trust)\b'
        }
        
        # Legal-specific patterns
        self.legal_patterns = {
            'motion_type': r'\b(?:Motion to|Motion for)\s+([A-Za-z\s]+)\b',
            'deadline': r'\b(?:due|deadline|expires?)\s+(?:on\s+)?([\w\s,]+)\b',
            'statute': r'\b(?:§|Section)\s*\d+(?:\.\d+)*\b',
            'citation': r'\b\d+\s+[A-Za-z\.]+\s+\d+\b',  # Legal citations
            'docket_entry': r'\b(?:Doc|Docket)\s*#?\s*\d+\b'
        }
    
    async def extract(self, content: str, content_type: str = 'text') -> Dict[str, List[Dict]]:
        """Extract entities from content with confidence scores"""
        extracted = {
            'entities': [],
            'legal_terms': [],
            'metadata': {
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'content_hash': hashlib.md5(content.encode()).hexdigest(),
                'content_length': len(content)
            }
        }
        
        # Extract general entities
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                extracted['entities'].append({
                    'type': entity_type,
                    'value': match.group(),
                    'position': [match.start(), match.end()],
                    'confidence': 0.8,  # Pattern-based confidence
                    'context': content[max(0, match.start()-50):match.end()+50]
                })
        
        # Extract legal-specific terms
        for legal_type, pattern in self.legal_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                extracted['legal_terms'].append({
                    'type': legal_type,
                    'value': match.group(),
                    'position': [match.start(), match.end()],
                    'confidence': 0.9,  # Legal patterns are high confidence
                    'context': content[max(0, match.start()-30):match.end()+30]
                })
        
        # Deduplicate and score
        extracted['entities'] = self._deduplicate_entities(extracted['entities'])
        extracted['legal_terms'] = self._deduplicate_entities(extracted['legal_terms'])
        
        # Add trust scoring
        extracted['trust_score'] = self._calculate_trust_score(content, extracted)
        
        return extracted
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities and boost confidence"""
        entity_map = {}
        
        for entity in entities:
            key = f"{entity['type']}:{entity['value'].lower()}"
            if key in entity_map:
                # Boost confidence for duplicates
                entity_map[key]['confidence'] = min(1.0, entity_map[key]['confidence'] + 0.1)
                entity_map[key]['occurrences'] = entity_map[key].get('occurrences', 1) + 1
            else:
                entity['occurrences'] = 1
                entity_map[key] = entity
        
        return list(entity_map.values())
    
    def _calculate_trust_score(self, content: str, extracted: Dict) -> float:
        """Calculate trust score based on content and extraction quality"""
        base_score = 0.5
        
        # Boost for legal entities
        if extracted['legal_terms']:
            base_score += 0.2
        
        # Boost for structured content
        if len(extracted['entities']) > 3:
            base_score += 0.1
        
        # Boost for case numbers or official references
        if any(e['type'] == 'case_number' for e in extracted['entities']):
            base_score += 0.2
        
        return min(1.0, base_score)

# Initialize extractor
entity_extractor = EntityExtractor()

async def _process_ingest_item(item: Dict):
    """Process queued ingestion item"""
    try:
        ingest_stats['processing'] += 1
        start_time = datetime.utcnow()
        
        # Extract entities if enrichment enabled
        if item.get('enrich', True):
            extraction_result = await entity_extractor.extract(item['content'])
            item['metadata'] = {**(item.get('metadata', {})), **extraction_result}
        
        # Write to memory system
        from core.memory_orchestrator.aggregator_mcp import MemoryAggregator
        aggregator = MemoryAggregator()
        
        memory_result = await aggregator.write_memory(
            item['content'],
            item.get('entity', 'unknown'),
            item.get('classification', 'general'),
            item.get('metadata')
        )
        
        # Update stats
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        ingest_stats['processing'] -= 1
        ingest_stats['completed'] += 1
        ingest_stats['processing_times'].append(processing_time)
        
        print(f"✅ Processed ingestion: {item.get('entity')} in {processing_time:.2f}s")
        
    except Exception as e:
        ingest_stats['processing'] -= 1
        ingest_stats['failed'] += 1
        print(f"❌ Ingestion failed: {e}")