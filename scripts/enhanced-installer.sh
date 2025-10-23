#!/usr/bin/env bash
set -euo pipefail

echo "🚀 GlacierEQ Memory Master - Enhanced Installer"
echo "================================================"

# Check prerequisites
echo "🔍 Checking prerequisites..."
command -v docker >/dev/null || { echo "❌ Docker not found - install Docker first"; exit 1; }
command -v docker-compose >/dev/null || { echo "❌ docker-compose not found"; exit 1; }
command -v python3 >/dev/null || { echo "❌ Python 3 not found"; exit 1; }
echo "✅ Prerequisites satisfied"

# Validate environment
echo "🔧 Validating environment..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found - creating from template"
    cp .env.example .env
    echo "📝 Please edit .env with your API keys before continuing"
    echo "   Required: MEM0_API_KEY, SUPERMEMORY_API_KEY"
    read -p "Press Enter when .env is configured..."
fi

source .env

# Check critical API keys
if [ -z "${MEM0_API_KEY:-}" ]; then
    echo "❌ MEM0_API_KEY not set in .env"
    exit 1
fi

if [ -z "${SUPERMEMORY_API_KEY:-}" ]; then
    echo "❌ SUPERMEMORY_API_KEY not set in .env" 
    exit 1
fi

echo "✅ Environment validated"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -q fastapi uvicorn neo4j requests pyyaml python-multipart || {
    echo "❌ Failed to install Python dependencies"
    exit 1
}
echo "✅ Python dependencies installed"

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for Neo4j
echo "⏳ Waiting for Neo4j to be ready..."
for i in {1..60}; do
    if nc -z localhost 7687 2>/dev/null; then
        echo "✅ Neo4j is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ Neo4j failed to start within 60 seconds"
        exit 1
    fi
    sleep 2
done

# Wait for ChromaDB
echo "⏳ Waiting for ChromaDB to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
        echo "✅ ChromaDB is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ ChromaDB failed to start within 30 seconds"
        exit 1
    fi
    sleep 2
done

# Initialize Neo4j constraints
echo "🏗️  Initializing Neo4j constraints..."
docker exec -i $(docker ps -qf name=neo4j) cypher-shell -u neo4j -p "${NEO4J_PASSWORD}" << 'CYPHER'
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT observation_id IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT custody_id IF NOT EXISTS FOR (c:CustodyEvent) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT tombstone_id IF NOT EXISTS FOR (t:Tombstone) REQUIRE t.original_id IS UNIQUE;
CYPHER

echo "✅ Neo4j constraints created"

# Test API connectivity
echo "🌐 Testing API connectivity..."
echo "  Testing Mem0 API..."
curl -s -H "Authorization: Bearer ${MEM0_API_KEY}" https://api.mem0.ai/v1/memories >/dev/null && echo "  ✅ Mem0 API reachable" || echo "  ⚠️  Mem0 API test failed"

echo "  Testing SuperMemory API..."
curl -s -H "Authorization: Bearer ${SUPERMEMORY_API_KEY}" ${SUPERMEMORY_BASE_URL:-https://api.supermemory.ai}/api/health >/dev/null && echo "  ✅ SuperMemory API reachable" || echo "  ⚠️  SuperMemory API test failed"

# Start API server in background
echo "🚀 Starting Memory Master API server..."
python3 api/server.py &
API_PID=$!
echo "  API server started (PID: $API_PID)"

# Wait for API server
echo "⏳ Waiting for API server..."
for i in {1..15}; do
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        echo "✅ API server is ready"
        break
    fi
    sleep 2
done

# Run comprehensive health check
echo "🏥 Running comprehensive health check..."
python3 scripts/health-check.py

# Migration helper
echo "🚚 Phase 1 Migration Helper Available"
echo "  Run: python3 scripts/migration-helper.py"
echo "  This will migrate the 4 critical repositories with history preservation"

echo ""
echo "🎉 INSTALLATION COMPLETE!"
echo "======================================"
echo "📊 Services Status:"
echo "  Neo4j Browser: http://localhost:7474 (neo4j/password)"
echo "  API Server: http://localhost:8080"
echo "  ChromaDB: http://localhost:8000"
echo ""
echo "🎯 Next Steps:"
echo "  1. Run Phase 1 migration: python3 scripts/migration-helper.py"
echo "  2. Configure Sigma File Manager 2 with ui/sigma/config.json"
echo "  3. Test memory operations via /memory/write, /memory/search"
echo "  4. Monitor via /health and /memory/status endpoints"
echo ""
echo "🧠 Memory Master is LIVE and ready for sovereign operation!"

# Keep API server running
echo "📡 API server running in background (PID: $API_PID)"
echo "   To stop: kill $API_PID"
echo "   Logs: tail -f nohup.out"