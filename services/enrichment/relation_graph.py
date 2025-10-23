#!/usr/bin/env python3
"""
Relation Graph Builder
Builds entity relationships and updates memory graph
"""

from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

class RelationGraphBuilder:
    def __init__(self):
        # Relationship patterns for legal domain
        self.relation_patterns = {
            'represents': [r'(\w+(?:\s+\w+)*?)\s+represents\s+(\w+(?:\s+\w+)*?)', r'attorney for (\w+(?:\s+\w+)*?)'],
            'vs': [r'(\w+(?:\s+\w+)*?)\s+v\.?\s+(\w+(?:\s+\w+)*?)', r'(\w+(?:\s+\w+)*?)\s+versus\s+(\w+(?:\s+\w+)*?)'],
            'filed_by': [r'filed by (\w+(?:\s+\w+)*?)'],
            'assigned_to': [r'assigned to (\w+(?:\s+\w+)*?)', r'Hon\. (\w+(?:\s+\w+)*?)'],
            'related_to': [r'related to (\w+(?:\s+\w+)*?)', r'in connection with (\w+(?:\s+\w+)*?)'],
            'deadline': [r'(\w+(?:\s+\w+)*?)\s+(?:due|expires?)\s+(.+?)(?:[,.]|$)'],
            'owns': [r'(\w+(?:\s+\w+)*?)\s+owns\s+(\w+(?:\s+\w+)*?)'],
            'works_for': [r'(\w+(?:\s+\w+)*?)\s+(?:works for|employed by)\s+(\w+(?:\s+\w+)*?)'],
            'located_at': [r'(\w+(?:\s+\w+)*?)\s+(?:at|located at)\s+(.+?)(?:[,.]|$)']
        }
        
        # Entity type inference
        self.entity_type_hints = {
            'person': [r'\b(?:Mr|Ms|Dr|Hon|Justice|Judge|Attorney|Counsel)\.?\s+\w+'],
            'organization': [r'\b\w+(?:\s+\w+)*\s+(?:Inc|LLC|Corp|Company|Foundation|Trust)\b'],
            'court': [r'\b(?:Court|Tribunal|Commission)\s+\w+'],
            'case': [r'\b\d+[A-Z]+[- ]?\d+[- ]?\d+\b'],
            'document': [r'\b(?:Motion|Order|Brief|Complaint|Answer|Reply)\b']
        }
    
    async def build_relations(self, content: str, extracted_entities: List[Dict]) -> List[Dict]:
        """Build relationship graph from content and entities"""
        relations = []
        
        # Extract relationships using patterns
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        source_entity = groups[0].strip()
                        target_entity = groups[1].strip()
                        
                        relations.append({
                            'type': relation_type,
                            'source': source_entity,
                            'target': target_entity,
                            'confidence': 0.7,
                            'context': match.group(),
                            'position': [match.start(), match.end()],
                            'extracted_at': datetime.utcnow().isoformat()
                        })
        
        # Infer entity types
        entity_types = self._infer_entity_types(content)
        
        # Add entity type information to relations
        for relation in relations:
            relation['source_type'] = entity_types.get(relation['source'], 'unknown')
            relation['target_type'] = entity_types.get(relation['target'], 'unknown')
        
        # Add temporal relationships
        temporal_relations = self._extract_temporal_relations(content, extracted_entities)
        relations.extend(temporal_relations)
        
        return self._deduplicate_relations(relations)
    
    def _infer_entity_types(self, content: str) -> Dict[str, str]:
        """Infer entity types from content patterns"""
        entity_types = {}
        
        for entity_type, patterns in self.entity_type_hints.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Extract the actual entity name (usually the last capitalized word)
                    words = match.group().split()
                    if words:
                        entity_name = ' '.join([w for w in words if w[0].isupper() and not w.endswith('.')])
                        if entity_name:
                            entity_types[entity_name] = entity_type
        
        return entity_types
    
    def _extract_temporal_relations(self, content: str, entities: List[Dict]) -> List[Dict]:
        """Extract temporal relationships (before, after, during)"""
        temporal_relations = []
        
        # Find temporal indicators
        temporal_patterns = {
            'before': [r'before\s+(\w+(?:\s+\w+)*?)', r'prior to\s+(\w+(?:\s+\w+)*?)'],
            'after': [r'after\s+(\w+(?:\s+\w+)*?)', r'following\s+(\w+(?:\s+\w+)*?)'],
            'during': [r'during\s+(\w+(?:\s+\w+)*?)', r'while\s+(\w+(?:\s+\w+)*?)']
        }
        
        for relation_type, patterns in temporal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    temporal_entity = match.group(1).strip()
                    
                    # Find nearby entities to create relationships
                    for entity in entities:
                        entity_value = entity.get('value', '')
                        if entity_value and entity_value != temporal_entity:
                            # Check if entities are close in the text
                            entity_pos = content.find(entity_value)
                            match_pos = match.start()
                            
                            if abs(entity_pos - match_pos) < 100:  # Within 100 characters
                                temporal_relations.append({
                                    'type': f'temporal_{relation_type}',
                                    'source': entity_value,
                                    'target': temporal_entity,
                                    'confidence': 0.6,
                                    'context': match.group(),
                                    'extracted_at': datetime.utcnow().isoformat()
                                })
        
        return temporal_relations
    
    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """Remove duplicate relations and boost confidence"""
        relation_map = {}
        
        for relation in relations:
            # Create unique key for relation
            key = f"{relation['type']}:{relation['source']}:{relation['target']}"
            key_hash = hashlib.md5(key.encode()).hexdigest()[:8]
            
            if key_hash in relation_map:
                # Boost confidence for duplicates
                relation_map[key_hash]['confidence'] = min(1.0, relation_map[key_hash]['confidence'] + 0.1)
                relation_map[key_hash]['occurrences'] = relation_map[key_hash].get('occurrences', 1) + 1
            else:
                relation['occurrences'] = 1
                relation['id'] = key_hash
                relation_map[key_hash] = relation
        
        return list(relation_map.values())
    
    async def create_graph_relations(self, relations: List[Dict], neo4j_client) -> Dict:
        """Create relationships in Neo4j graph"""
        if not neo4j_client or not relations:
            return {'created': 0, 'errors': []}
        
        created_count = 0
        errors = []
        
        for relation in relations:
            try:
                # Create Cypher query for relationship
                cypher = f"""
                MERGE (s:Entity {{name: $source, type: $source_type}})
                MERGE (t:Entity {{name: $target, type: $target_type}})
                CREATE (s)-[r:{relation['type'].upper().replace(' ', '_')} {{
                    confidence: $confidence,
                    context: $context,
                    created_at: datetime(),
                    extraction_id: $extraction_id
                }}]->(t)
                RETURN r
                """
                
                params = {
                    'source': relation['source'],
                    'target': relation['target'],
                    'source_type': relation.get('source_type', 'unknown'),
                    'target_type': relation.get('target_type', 'unknown'),
                    'confidence': relation['confidence'],
                    'context': relation.get('context', ''),
                    'extraction_id': relation.get('id', '')
                }
                
                result = await neo4j_client.cypher(cypher, params)
                if result.get('records'):
                    created_count += 1
                
            except Exception as e:
                errors.append(f"Relation {relation['type']}: {str(e)}")
        
        return {
            'created': created_count,
            'total_attempted': len(relations),
            'errors': errors
        }

if __name__ == '__main__':
    # Test entity extraction
    extractor = EntityExtractor()
    builder = RelationGraphBuilder()
    
    test_content = """
    Motion for Summary Judgment filed by Attorney Smith on behalf of GlacierEQ LLC
    in Case 1FDV-23-0001009 before Hon. Johnson. The motion is due on 11/15/2025.
    Contact: legal@glaciereq.com or 808-555-1234.
    """
    
    print("Testing entity extraction...")
    result = asyncio.run(extractor.extract(test_content))
    print(f"Extracted {len(result['entities'])} entities and {len(result['legal_terms'])} legal terms")
    
    relations = asyncio.run(builder.build_relations(test_content, result['entities']))
    print(f"Built {len(relations)} relationships")