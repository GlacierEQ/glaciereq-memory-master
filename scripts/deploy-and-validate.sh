#!/usr/bin/env bash
set -euo pipefail

echo "🚀 GLACIEREQ MEMORY MASTER - COMPLETE DEPLOYMENT & VALIDATION"
echo "============================================================="
echo "Started: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status tracking
TOTAL_STEPS=10
CURRENT_STEP=0
FAILED_STEPS=()

log_step() {
    ((CURRENT_STEP++))
    echo -e "\n${BLUE}[${CURRENT_STEP}/${TOTAL_STEPS}]${NC} $1"
    echo "$(date): $1" >> deployment.log
}

log_success() {
    echo -e "  ${GREEN}✅ $1${NC}"
    echo "SUCCESS: $1" >> deployment.log
}

log_warning() {
    echo -e "  ${YELLOW}⚠️  $1${NC}"
    echo "WARNING: $1" >> deployment.log
}

log_error() {
    echo -e "  ${RED}❌ $1${NC}"
    echo "ERROR: $1" >> deployment.log
    FAILED_STEPS+=("$1")
}

# Initialize deployment log
echo "GlacierEQ Memory Master Deployment Log" > deployment.log
echo "Started: $(date)" >> deployment.log
echo "" >> deployment.log

# Step 1: Environment Check
log_step "Environment Prerequisites Check"

if command -v docker &> /dev/null; then
    log_success "Docker found: $(docker --version | head -1)"
else
    log_error "Docker not found - install Docker first"
fi

if command -v docker-compose &> /dev/null; then
    log_success "Docker Compose found: $(docker-compose --version)"
else
    log_error "Docker Compose not found"
fi

if command -v python3 &> /dev/null; then
    log_success "Python 3 found: $(python3 --version)"
else
    log_error "Python 3 not found"
fi

# Step 2: Environment Configuration
log_step "Environment Configuration"

if [ ! -f ".env" ]; then
    log_warning ".env not found - creating from template"
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}📝 REQUIRED: Edit .env file with your API keys:${NC}"
    echo "   MEM0_API_KEY=your_mem0_api_key_here"
    echo "   SUPERMEMORY_API_KEY=your_supermemory_key_here"
    echo ""
    read -p "Press Enter when .env is configured with API keys..."
fi

source .env

# Validate required keys
if [ -n "${MEM0_API_KEY:-}" ] && [ "${MEM0_API_KEY}" != "" ]; then
    log_success "MEM0_API_KEY configured (${#MEM0_API_KEY} chars)"
else
    log_error "MEM0_API_KEY not set in .env"
fi

if [ -n "${SUPERMEMORY_API_KEY:-}" ] && [ "${SUPERMEMORY_API_KEY}" != "" ]; then
    log_success "SUPERMEMORY_API_KEY configured (${#SUPERMEMORY_API_KEY} chars)"
else
    log_error "SUPERMEMORY_API_KEY not set in .env"
fi

# Step 3: Install Python Dependencies
log_step "Installing Python Dependencies"

if pip3 install -q -r requirements.txt; then
    log_success "Python dependencies installed"
else
    log_error "Failed to install Python dependencies"
fi

# Step 4: Start Docker Services
log_step "Starting Docker Services"

if docker-compose up -d; then
    log_success "Docker services started"
else
    log_error "Failed to start Docker services"
fi

# Step 5: Wait for Services
log_step "Waiting for Services to be Ready"

# Wait for Neo4j
echo "  Waiting for Neo4j..."
for i in {1..60}; do
    if nc -z localhost 7687 2>/dev/null; then
        log_success "Neo4j ready on port 7687"
        break
    fi
    if [ $i -eq 60 ]; then
        log_error "Neo4j failed to start within 60 seconds"
    fi
    sleep 2
done

# Wait for ChromaDB
echo "  Waiting for ChromaDB..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
        log_success "ChromaDB ready on port 8000"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "ChromaDB failed to start within 30 seconds"
    fi
    sleep 2
done

# Step 6: Initialize Neo4j
log_step "Initializing Neo4j Constraints"

if docker exec -i $(docker ps -qf name=neo4j) cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" << 'CYPHER'
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT observation_id IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT custody_id IF NOT EXISTS FOR (c:CustodyEvent) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT tombstone_id IF NOT EXISTS FOR (t:Tombstone) REQUIRE t.original_id IS UNIQUE;
CYPHER
then
    log_success "Neo4j constraints created"
else
    log_error "Failed to create Neo4j constraints"
fi

# Step 7: Start API Server
log_step "Starting API Server"

echo "  Starting FastAPI server in background..."
python3 api/server.py &
API_PID=$!
echo $API_PID > api_server.pid

# Wait for API server
echo "  Waiting for API server..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        log_success "API server ready on port 8080 (PID: $API_PID)"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "API server failed to start within 30 seconds"
    fi
    sleep 2
done

# Step 8: Run Health Checks
log_step "Running Comprehensive Health Checks"

if python3 scripts/health-check.py; then
    log_success "Health checks passed"
else
    log_warning "Some health checks failed (check output above)"
fi

# Step 9: Load Demo Data
log_step "Loading Demo Data for Case 1FDV-23-0001009"

if python3 scripts/load-demo-data.py; then
    log_success "Demo data loaded successfully"
else
    log_warning "Demo data loading had issues (check output above)"
fi

# Step 10: Final Validation
log_step "Final System Validation"

echo "  Testing core endpoints..."

# Test health endpoint
if curl -s http://localhost:8080/health | grep '"status":"ok"' >/dev/null; then
    log_success "Health endpoint: OK"
else
    log_error "Health endpoint failed"
fi

# Test memory status
if curl -s http://localhost:8080/memory/status >/dev/null; then
    log_success "Memory status endpoint: OK"
else
    log_error "Memory status endpoint failed"
fi

# Test metrics
if curl -s http://localhost:8080/metrics >/dev/null; then
    log_success "Metrics endpoint: OK"
else
    log_error "Metrics endpoint failed"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🎯 DEPLOYMENT VALIDATION COMPLETE"
echo "═══════════════════════════════════════════════════════════"

if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS OPERATIONAL - MAXIMUM POWER ACHIEVED!${NC}"
    echo ""
    echo "🌐 Access Points:"
    echo "   📊 API Server: http://localhost:8080"
    echo "   🔗 Neo4j Browser: http://localhost:7474 (neo4j/password)"
    echo "   📈 ChromaDB: http://localhost:8000"
    echo "   📡 Audit Stream: http://localhost:8080/audit/stream"
    echo "   📊 Metrics: http://localhost:8080/metrics"
    echo ""
    echo "🧪 Test Commands:"
    echo "   make test-memory    # Test memory operations"
    echo "   make test-rag       # Test Graph-RAG hybrid"
    echo "   make copilot-test   # Test domain copilots"
    echo ""
    echo "🖥️  Sigma Configuration:"
    echo "   Import: ui/sigma/config.json"
    echo "   Workspace: GlacierEQ Memory Ops"
    echo "   Tabs: Memory | Graphs | Intelligence | Ops"
    echo ""
    echo -e "${GREEN}STATUS: 🚀 SOVEREIGN MEMORY ARCHITECTURE OPERATIONAL${NC}"
else
    echo -e "${RED}⚠️  ${#FAILED_STEPS[@]} ISSUES DETECTED:${NC}"
    for failed_step in "${FAILED_STEPS[@]}"; do
        echo -e "  ${RED}❌ $failed_step${NC}"
    done
    echo ""
    echo "📋 Next Actions:"
    echo "   1. Review errors above"
    echo "   2. Check deployment.log for details"
    echo "   3. Run individual make commands to isolate issues"
    echo "   4. Validate .env configuration"
fi

echo ""
echo "📄 Full deployment log: deployment.log"
echo "🔧 API Server PID: $API_PID (saved to api_server.pid)"
echo "⏰ Completed: $(date)"
