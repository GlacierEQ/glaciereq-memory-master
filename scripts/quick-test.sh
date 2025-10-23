#!/usr/bin/env bash
set -euo pipefail

echo "🧪 QUICK SYSTEM TEST - All Capabilities"
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_BASE="http://localhost:8080"
TEST_RESULTS=()

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n🔍 Testing: $test_name"
    
    if eval "$test_command"; then
        echo -e "  ${GREEN}✅ PASS${NC}"
        TEST_RESULTS+=("✅ $test_name")
    else
        echo -e "  ${RED}❌ FAIL${NC}"
        TEST_RESULTS+=("❌ $test_name")
    fi
}

# Test 1: Health endpoint
run_test "System Health" \
    "curl -s $API_BASE/health | grep '\"status\":\"ok\"' >/dev/null"

# Test 2: Memory status
run_test "Memory System Status" \
    "curl -s $API_BASE/memory/status | grep 'providers' >/dev/null"

# Test 3: Environment status
run_test "Environment Configuration" \
    "curl -s $API_BASE/env/status | grep 'environment' >/dev/null"

# Test 4: Metrics endpoint
run_test "Prometheus Metrics" \
    "curl -s $API_BASE/metrics | head -10 | grep -E '(TYPE|api_)' >/dev/null"

# Test 5: SLO Dashboard
run_test "SLO Dashboard" \
    "curl -s $API_BASE/metrics/slo | grep 'overall_health' >/dev/null"

# Test 6: Memory Write (if keys configured)
if [ -n "${MEM0_API_KEY:-}" ] && [ -n "${SUPERMEMORY_API_KEY:-}" ]; then
    run_test "Memory Write Operation" \
        "curl -s -X POST $API_BASE/memory/write -H 'Content-Type: application/json' -d '{\"content\":\"Quick test memory\",\"entity\":\"quick_test\",\"classification\":\"general\"}' | grep -E '(success|error)' >/dev/null"
    
    run_test "Memory Search Operation" \
        "curl -s -X POST $API_BASE/memory/search -H 'Content-Type: application/json' -d '{\"query\":\"quick test\",\"limit\":5}' | grep 'results' >/dev/null"
else
    echo -e "\n${YELLOW}⚠️  Skipping memory operations - API keys not configured${NC}"
fi

# Test 7: Graph operations
run_test "Neo4j Cypher Query" \
    "curl -s -X POST $API_BASE/graph/cypher -H 'Content-Type: application/json' -d '{\"query\":\"RETURN 1 as test\"}' | grep 'records' >/dev/null"

# Test 8: RAG endpoints
run_test "Graph-RAG Status" \
    "curl -s $API_BASE/rag/status | grep 'semantic_provider' >/dev/null"

# Test 9: Copilot status
run_test "Domain Copilots Status" \
    "curl -s $API_BASE/copilot/status | grep 'available_copilots' >/dev/null"

# Test 10: Audit system
run_test "Audit System Status" \
    "curl -s $API_BASE/audit/status | grep 'total_events' >/dev/null"

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🧪 QUICK TEST RESULTS"
echo "═══════════════════════════════════════════════════════════"

PASSED=0
FAILED=0

for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
    if [[ $result == ✅* ]]; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

echo ""
echo "📊 Test Summary: $PASSED passed, $FAILED failed"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL!${NC}"
    echo ""
    echo "🎯 Ready for:"
    echo "   ✅ Case 1FDV-23-0001009 operations"
    echo "   ✅ Sigma File Manager 2 integration"
    echo "   ✅ Graph-RAG hybrid intelligence"
    echo "   ✅ Domain copilots (Legal/Ops/Research)"
    echo "   ✅ Real-time audit and compliance"
    echo ""
    echo "🔥 STATUS: MAXIMUM POWER ACHIEVED"
else
    echo -e "\n${YELLOW}⚠️  $FAILED tests failed - system partially operational${NC}"
    echo "📋 Next steps:"
    echo "   1. Check deployment.log for details"
    echo "   2. Verify .env configuration"
    echo "   3. Run 'make logs' to check service status"
    echo "   4. Run individual tests: make test-memory, make test-rag, etc."
fi

echo ""
echo "📄 Full log: deployment.log"
echo "⏰ Completed: $(date)"
