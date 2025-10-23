#!/usr/bin/env python3
"""
Demo Data Loader
Loads sample legal case data for immediate testing and demonstration
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Import components
sys.path.append('..')
from core.memory_orchestrator.aggregator_mcp import MemoryAggregator

class DemoDataLoader:
    def __init__(self):
        self.aggregator = MemoryAggregator()
        
        # Demo legal case data for Case 1FDV-23-0001009
        self.demo_data = [
            {
                'content': 'Temporary Restraining Order issued on 2025-10-15 for Case 1FDV-23-0001009 by Hon. Johnson. Order expires on 2025-11-15.',
                'entity': 'Case_1FDV_23_0001009',
                'classification': 'evidence',
                'metadata': {
                    'document_type': 'TRO',
                    'court': 'Family Court',
                    'judge': 'Hon. Johnson',
                    'expiration_date': '2025-11-15'
                }
            },
            {
                'content': 'Motion for Summary Judgment filed by Attorney Smith on behalf of plaintiff. Motion argues that material facts are undisputed.',
                'entity': 'Motion_Summary_Judgment',
                'classification': 'evidence',
                'metadata': {
                    'document_type': 'Motion',
                    'attorney': 'Attorney Smith',
                    'filing_date': '2025-10-20',
                    'motion_type': 'Summary Judgment'
                }
            },
            {
                'content': 'Client interview notes: Client expressed concern about deadline compliance. Reviewed case timeline and next steps.',
                'entity': 'Client_Interview_Oct22',
                'classification': 'privileged',
                'metadata': {
                    'document_type': 'Interview Notes',
                    'attorney_client_privilege': True,
                    'interview_date': '2025-10-22'
                }
            },
            {
                'content': 'Legal research memo: Hawaii family court procedures require 30-day notice for modifications. Relevant statute: HRS §571-46.',
                'entity': 'Research_Memo_Procedures',
                'classification': 'general',
                'metadata': {
                    'document_type': 'Research Memo',
                    'jurisdiction': 'Hawaii',
                    'statute': 'HRS §571-46',
                    'research_date': '2025-10-21'
                }
            },
            {
                'content': 'Evidence inventory: Document A (contract), Document B (correspondence), Document C (financial records). All items logged with chain of custody.',
                'entity': 'Evidence_Inventory',
                'classification': 'evidence',
                'metadata': {
                    'document_type': 'Evidence Inventory',
                    'items_count': 3,
                    'chain_of_custody': True,
                    'inventory_date': '2025-10-19'
                }
            },
            {
                'content': 'System deployment notes: Neo4j graph database configured with constraints. Memory aggregator MCP server operational. All health checks passing.',
                'entity': 'System_Deployment',
                'classification': 'general',
                'metadata': {
                    'document_type': 'System Notes',
                    'deployment_date': '2025-10-22',
                    'services': ['neo4j', 'chromadb', 'mcp_server'],
                    'status': 'operational'
                }
            },
            {
                'content': 'Opposing counsel correspondence: Request for extension of discovery deadline. Proposed new date: December 1, 2025.',
                'entity': 'Opposing_Counsel_Request',
                'classification': 'general',
                'metadata': {
                    'document_type': 'Correspondence',
                    'from': 'Opposing Counsel',
                    'subject': 'Discovery Extension',
                    'proposed_date': '2025-12-01'
                }
            },
            {
                'content': 'Court calendar entry: Hearing scheduled for Case 1FDV-23-0001009 on November 30, 2025 at 2:00 PM in Courtroom B.',
                'entity': 'Court_Hearing_Nov30',
                'classification': 'evidence',
                'metadata': {
                    'document_type': 'Court Calendar',
                    'hearing_date': '2025-11-30T14:00:00Z',
                    'courtroom': 'B',
                    'hearing_type': 'Scheduled Hearing'
                }
            },
            {
                'content': 'Financial analysis: Total case costs to date $15,750. Breakdown: Attorney fees $12,000, Court costs $500, Expert fees $3,250.',
                'entity': 'Financial_Analysis',
                'classification': 'sensitive',
                'metadata': {
                    'document_type': 'Financial Analysis',
                    'total_costs': 15750,
                    'attorney_fees': 12000,
                    'court_costs': 500,
                    'expert_fees': 3250
                }
            },
            {
                'content': 'Expert witness report: Dr. Anderson concludes that technical analysis supports plaintiff position. Report submitted under seal.',
                'entity': 'Expert_Report_Anderson',
                'classification': 'evidence',
                'metadata': {
                    'document_type': 'Expert Report',
                    'expert': 'Dr. Anderson',
                    'sealed': True,
                    'conclusion': 'Supports plaintiff',
                    'report_date': '2025-10-18'
                }
            }
        ]
    
    async def load_all_demo_data(self) -> Dict:
        """Load all demo data into memory system"""
        print("📥 Loading demo data for Case 1FDV-23-0001009...")
        
        results = []
        for i, item in enumerate(self.demo_data):
            print(f"  Loading {i+1}/{len(self.demo_data)}: {item['entity']}")
            
            try:
                result = await self.aggregator.write_memory(
                    item['content'],
                    item['entity'], 
                    item['classification'],
                    item['metadata']
                )
                
                results.append({
                    'entity': item['entity'],
                    'status': 'success',
                    'result': result
                })
                
                print(f"    ✅ {item['entity']} loaded successfully")
                
            except Exception as e:
                results.append({
                    'entity': item['entity'],
                    'status': 'failed', 
                    'error': str(e)
                })
                print(f"    ❌ {item['entity']} failed: {e}")
            
            # Small delay between items
            await asyncio.sleep(0.5)
        
        successful = len([r for r in results if r['status'] == 'success'])
        print(f"\n🏆 Demo data loading complete: {successful}/{len(results)} successful")
        
        return {
            'loaded_items': len(results),
            'successful': successful,
            'failed': len(results) - successful,
            'results': results,
            'case_number': '1FDV-23-0001009'
        }
    
    def get_test_queries(self) -> List[Dict]:
        """Get suggested test queries for demo data"""
        return [
            {
                'name': 'Find TRO Information',
                'query': 'TRO restraining order expiration',
                'entity': 'Case_1FDV_23_0001009',
                'expected_results': 'TRO details with expiration date'
            },
            {
                'name': 'Search Evidence Items',
                'query': 'evidence inventory chain custody',
                'entity': 'Evidence_Inventory',
                'expected_results': 'Evidence list with custody information'
            },
            {
                'name': 'Attorney-Client Privileged',
                'query': 'client interview notes concern',
                'entity': 'Client_Interview_Oct22',
                'expected_results': 'Privileged interview content'
            },
            {
                'name': 'Financial Summary', 
                'query': 'case costs attorney fees breakdown',
                'entity': 'Financial_Analysis',
                'expected_results': 'Cost breakdown and totals'
            },
            {
                'name': 'Court Schedule',
                'query': 'hearing November courtroom',
                'entity': 'Court_Hearing_Nov30',
                'expected_results': 'Hearing details and schedule'
            }
        ]

async def main():
    """Load demo data and run test queries"""
    loader = DemoDataLoader()
    
    # Load demo data
    load_result = await loader.load_all_demo_data()
    
    if load_result['successful'] > 0:
        print(f"\n🧪 Suggested test queries:")
        test_queries = loader.get_test_queries()
        
        for query in test_queries:
            print(f"\n  🔍 {query['name']}:")
            print(f"     Query: '{query['query']}'")
            print(f"     Entity: {query['entity']}")
            print(f"     Expected: {query['expected_results']}")
            print(f"     Test: curl -X POST http://localhost:8080/memory/search -d '{json.dumps({\"query\": query[\"query\"], \"entity\": query[\"entity\"]})}' -H 'Content-Type: application/json'")
        
        print(f"\n🎯 Demo data ready! Test queries with:")
        print(f"  make test-memory")
        print(f"  make test-rag")
        print(f"  make copilot-test")
    
    return load_result

if __name__ == '__main__':
    result = asyncio.run(main())
    print(f"\n✅ Demo data loader complete: {result['successful']} items loaded")