#!/usr/bin/env python3
"""
Policy Engine - TTL, Tombstone, and Redaction Management
Handles memory lifecycle and compliance policies
"""

import os
import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class PolicyEngine:
    def __init__(self, config_path: str = 'policies/memory.yaml'):
        self.config = self._load_config(config_path)
        self.ttl_policy = self.config.get('ttl_policy', {})
        self.tombstone_policy = self.config.get('tombstone_policy', {})
        self.redaction_policy = self.config.get('redaction_policy', {})
        self.access_control = self.config.get('access_control', {})
        
    def _load_config(self, path: str) -> Dict:
        """Load policy configuration"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Failed to load policy config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default policy configuration"""
        return {
            'ttl_policy': {'privileged': None, 'general': 365},
            'tombstone_policy': {'enabled': True, 'require_reason': True},
            'redaction_policy': {'enabled': True, 'patterns': []},
            'access_control': {'general_access': True}
        }
    
    def check_ttl_expired(self, memory: Dict) -> bool:
        """Check if memory has expired based on TTL policy"""
        classification = memory.get('classification', 'general')
        ttl_days = self.ttl_policy.get(classification)
        
        if ttl_days is None:
            return False  # No expiration for privileged/evidence
        
        created_at = datetime.fromisoformat(memory.get('timestamp', ''))
        expiry_date = created_at + timedelta(days=ttl_days)
        
        return datetime.utcnow() > expiry_date
    
    def create_tombstone(self, memory_id: str, reason: str, user: str = 'system') -> Dict:
        """Create tombstone record for deleted memory"""
        if not self.tombstone_policy.get('enabled', True):
            return {'tombstone': False}
        
        if self.tombstone_policy.get('require_reason', True) and not reason:
            raise ValueError("Reason required for tombstone creation")
        
        tombstone = {
            'original_id': memory_id,
            'deleted_at': datetime.utcnow().isoformat(),
            'deleted_by': user,
            'reason': reason,
            'tombstone': True,
            'audit_trail': self.tombstone_policy.get('audit_trail', True)
        }
        
        return tombstone
    
    def apply_redaction(self, content: str) -> Dict:
        """Apply redaction patterns to content"""
        if not self.redaction_policy.get('enabled', True):
            return {'content': content, 'redacted': False}
        
        redacted_content = content
        redactions = []
        
        for pattern_config in self.redaction_policy.get('patterns', []):
            pattern = pattern_config['pattern']
            replacement = pattern_config['replacement']
            
            matches = re.findall(pattern, redacted_content, re.IGNORECASE)
            if matches:
                redacted_content = re.sub(pattern, replacement, redacted_content, flags=re.IGNORECASE)
                redactions.append({
                    'pattern': pattern,
                    'matches': len(matches),
                    'replacement': replacement
                })
        
        return {
            'content': redacted_content,
            'redacted': len(redactions) > 0,
            'redactions': redactions
        }
    
    def check_access_permission(self, classification: str, user_role: str) -> bool:
        """Check if user role has access to memory classification"""
        if classification == 'privileged':
            return user_role in self.access_control.get('privileged_roles', [])
        elif classification == 'evidence':
            return user_role in self.access_control.get('evidence_roles', [])
        else:
            return self.access_control.get('general_access', True)
    
    def should_chain_custody(self, classification: str) -> bool:
        """Check if classification requires chain of custody"""
        required = self.config.get('forensic_logging', {}).get('chain_of_custody_required', [])
        return classification in required
    
    async def apply_lifecycle_policies(self, memories: List[Dict]) -> List[Dict]:
        """Apply TTL and lifecycle policies to memory list"""
        active_memories = []
        expired_count = 0
        
        for memory in memories:
            if self.check_ttl_expired(memory):
                # Auto-expire with tombstone
                tombstone = self.create_tombstone(
                    memory.get('id', ''),
                    'ttl_expired',
                    'policy_engine'
                )
                expired_count += 1
            else:
                # Apply redaction if needed
                if memory.get('classification') in ['sensitive', 'general']:
                    redacted = self.apply_redaction(memory.get('content', ''))
                    memory['content'] = redacted['content']
                    memory['redacted'] = redacted['redacted']
                
                active_memories.append(memory)
        
        return {
            'active_memories': active_memories,
            'expired_count': expired_count,
            'total_processed': len(memories)
        }

if __name__ == '__main__':
    # Test policy engine
    engine = PolicyEngine()
    print("Testing policy engine...")
    
    # Test memory with different classifications
    test_memories = [
        {'id': '1', 'classification': 'privileged', 'timestamp': '2025-01-01T00:00:00Z'},
        {'id': '2', 'classification': 'general', 'timestamp': '2024-01-01T00:00:00Z'},
        {'id': '3', 'classification': 'temporary', 'timestamp': '2025-10-15T00:00:00Z'}
    ]
    
    for memory in test_memories:
        expired = engine.check_ttl_expired(memory)
        print(f"Memory {memory['id']} ({memory['classification']}): {'EXPIRED' if expired else 'ACTIVE'}")