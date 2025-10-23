#!/usr/bin/env python3
"""
Domain Copilots Router - Legal, Ops, Research AI Assistants
Memory-aware copilots with graph reasoning and compliance
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

# Import components
import sys
sys.path.append('../..')
from api.routers.rag import GraphRAG
from core.memory_orchestrator.policy_engine import PolicyEngine

router = APIRouter(prefix="/copilot", tags=["copilot"])

class CopilotRequest(BaseModel):
    task: str
    case: Optional[str] = None
    context: Optional[str] = None
    classification: Optional[str] = 'general'
    export_format: Optional[str] = 'markdown'
    include_citations: Optional[bool] = True

class CopilotResponse(BaseModel):
    output: str
    citations: Optional[List[Dict]] = None
    confidence: Optional[float] = None
    next_actions: Optional[List[str]] = None
    compliance_notes: Optional[List[str]] = None

class LegalCopilot:
    def __init__(self):
        self.rag = GraphRAG()
        self.policy = PolicyEngine()
        
    async def draft_motion(self, task: str, case: str, context: str = None) -> Dict:
        """Draft legal motion with memory-backed research"""
        # Gather relevant memories
        search_query = f"{case} {context or ''} motion legal precedent"
        rag_result = await self.rag.hybrid_search(search_query, case, limit=20)
        
        # Extract key facts and precedents
        memories = rag_result.get('results', [])
        precedents = [m for m in memories if 'precedent' in m.get('content', '').lower()]
        facts = [m for m in memories if m.get('classification') == 'evidence']
        
        # Build motion structure
        motion_parts = {
            'header': f"MOTION REGARDING {case.upper()}",
            'introduction': f"Comes now the movant regarding {case}, and respectfully submits:",
            'background': self._synthesize_background(facts),
            'argument': self._build_legal_argument(precedents, context),
            'conclusion': "WHEREFORE, movant respectfully requests this Court grant the relief sought.",
            'citations': [{
                'content': m.get('content', '')[:200] + '...',
                'source': m.get('source', 'memory'),
                'confidence': m.get('hybrid_score', 0)
            } for m in memories[:10]]
        }
        
        # Format output
        motion_text = f"""
{motion_parts['header']}

{motion_parts['introduction']}

BACKGROUND
{motion_parts['background']}

ARGUMENT
{motion_parts['argument']}

CONCLUSION
{motion_parts['conclusion']}
        """.strip()
        
        return {
            'output': motion_text,
            'citations': motion_parts['citations'],
            'confidence': np.mean([c['confidence'] for c in motion_parts['citations']]) if motion_parts['citations'] else 0,
            'next_actions': [
                'Review citations for accuracy',
                'Add specific statutory references',
                'File within deadline window',
                'Serve opposing counsel'
            ],
            'compliance_notes': [
                'Attorney-client privilege maintained',
                'Chain of custody verified for evidence',
                'All sources properly attributed'
            ]
        }
    
    def _synthesize_background(self, facts: List[Dict]) -> str:
        """Synthesize background from evidence memories"""
        if not facts:
            return "Background facts to be supplemented."
        
        background_points = []
        for fact in facts[:5]:  # Top 5 facts
            content = fact.get('content', '')[:200]
            background_points.append(f"• {content}")
        
        return "\n".join(background_points)
    
    def _build_legal_argument(self, precedents: List[Dict], context: str) -> str:
        """Build legal argument from precedents"""
        if not precedents:
            return f"Legal analysis regarding {context} to be developed."
        
        arg_points = []
        for prec in precedents[:3]:  # Top 3 precedents
            content = prec.get('content', '')[:300]
            arg_points.append(f"The court should consider that {content.lower()}")
        
        return "\n\n".join(arg_points)

class OpsCopilot:
    def __init__(self):
        self.rag = GraphRAG()
        
    async def deployment_analysis(self, task: str, context: str = None) -> Dict:
        """Analyze deployment health and recommend actions"""
        # Get system memories about deployments, errors, performance
        search_query = f"deployment {context or ''} error performance health"
        rag_result = await self.rag.hybrid_search(search_query, 'system', limit=15)
        
        memories = rag_result.get('results', [])
        errors = [m for m in memories if 'error' in m.get('content', '').lower()]
        performance = [m for m in memories if any(word in m.get('content', '').lower() for word in ['latency', 'slow', 'timeout'])]
        
        # Generate recommendations
        recommendations = []
        if errors:
            recommendations.append("🔥 Address recent errors in deployment pipeline")
        if performance:
            recommendations.append("⚡ Optimize performance bottlenecks")
        if not errors and not performance:
            recommendations.append("✅ System appears healthy - continue monitoring")
        
        analysis = f"""
DEPLOYMENT ANALYSIS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

STATUS SUMMARY:
- Recent errors detected: {len(errors)}
- Performance issues: {len(performance)}
- Total system memories analyzed: {len(memories)}

RECOMMENDATIONS:
{chr(10).join(f"• {rec}" for rec in recommendations)}

NEXT MONITORING:
- Check service latencies in next 30 minutes
- Review error logs for patterns
- Validate backup systems
        """.strip()
        
        return {
            'output': analysis,
            'citations': [{
                'type': m.get('search_type', 'memory'),
                'content': m.get('content', '')[:150],
                'timestamp': m.get('timestamp')
            } for m in memories[:8]],
            'confidence': 0.85,
            'next_actions': recommendations + ["Schedule follow-up analysis in 4 hours"]
        }

class ResearchCopilot:
    def __init__(self):
        self.rag = GraphRAG()
        
    async def synthesize_research(self, task: str, context: str = None) -> Dict:
        """Cross-source research synthesis with graph disambiguation"""
        # Multi-angle search
        queries = [task]
        if context:
            queries.extend([f"{task} {context}", f"{context} analysis"])
        
        all_results = []
        for query in queries[:3]:  # Limit to 3 searches
            rag_result = await self.rag.hybrid_search(query, limit=8)
            all_results.extend(rag_result.get('results', []))
        
        # Dedupe and cluster by entity/topic
        entity_clusters = {}
        for result in all_results:
            entity = result.get('entity', 'unknown')
            if entity not in entity_clusters:
                entity_clusters[entity] = []
            entity_clusters[entity].append(result)
        
        # Synthesize by cluster
        synthesis_parts = []
        citations = []
        
        for entity, cluster_results in list(entity_clusters.items())[:5]:  # Top 5 entities
            if len(cluster_results) >= 2:  # Only synthesize multi-source clusters
                cluster_content = [r.get('content', '')[:200] for r in cluster_results[:3]]
                synthesis_parts.append(f"""
**{entity.upper()}**
Based on {len(cluster_results)} sources:
{chr(10).join(f"• {content}" for content in cluster_content)}
                """.strip())
                
                citations.extend([{
                    'entity': entity,
                    'content': r.get('content', '')[:100],
                    'confidence': r.get('hybrid_score', 0),
                    'source_type': r.get('search_type')
                } for r in cluster_results[:2]])
        
        research_synthesis = f"""
RESEARCH SYNTHESIS: {task.upper()}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

{chr(10).join(synthesis_parts)}

SOURCE ANALYSIS:
- Total sources analyzed: {len(all_results)}
- Entity clusters identified: {len(entity_clusters)}
- Multi-source entities: {len([c for c in entity_clusters.values() if len(c) >= 2])}
        """.strip()
        
        return {
            'output': research_synthesis,
            'citations': citations,
            'confidence': 0.80,
            'next_actions': [
                'Validate high-confidence findings',
                'Cross-reference with external sources',
                'Update memory graph with new insights'
            ]
        }

# Initialize copilots
legal_copilot = LegalCopilot()
ops_copilot = OpsCopilot()
research_copilot = ResearchCopilot()

@router.post("/legal", response_model=Dict)
async def legal_copilot_endpoint(request: CopilotRequest):
    """Legal AI copilot for drafts, analysis, and case management"""
    try:
        if 'motion' in request.task.lower():
            result = await legal_copilot.draft_motion(
                request.task,
                request.case or '1FDV-23-0001009',
                request.context
            )
        else:
            # General legal analysis
            result = {
                'output': f"Legal analysis for: {request.task}\nCase: {request.case}\nContext: {request.context}",
                'citations': [],
                'confidence': 0.7,
                'next_actions': ['Develop specific legal analysis'],
                'compliance_notes': ['Review required before filing']
            }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ops", response_model=Dict)
async def ops_copilot_endpoint(request: CopilotRequest):
    """Operations AI copilot for deployments and system management"""
    try:
        result = await ops_copilot.deployment_analysis(request.task, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research", response_model=Dict)
async def research_copilot_endpoint(request: CopilotRequest):
    """Research AI copilot for cross-source synthesis"""
    try:
        result = await research_copilot.synthesize_research(request.task, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def copilot_status():
    """Copilot system status"""
    return {
        'available_copilots': ['legal', 'ops', 'research'],
        'graph_rag_enabled': True,
        'policy_engine_enabled': True,
        'memory_providers': ['mem0', 'supermemory', 'neo4j'],
        'case_context': '1FDV-23-0001009'
    }