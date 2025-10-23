# GlacierEQ Memory Master - Operations Makefile

.PHONY: help up down logs install migrate-phase1 health lint test backup restore copilot-test

help:
	@echo "🚀 GlacierEQ Memory Master - Available Commands"
	@echo "================================================"
	@echo "📦 Setup & Installation:"
	@echo "  make install        - Run enhanced installer (Docker + API + validation)"
	@echo "  make up             - Start all services (Docker Compose)"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View service logs"
	@echo ""
	@echo "🔄 Migration & Consolidation:"
	@echo "  make migrate-phase1 - Migrate 4 critical repositories"
	@echo "  make migrate-phase2 - Migrate graph memory systems (next)"
	@echo ""
	@echo "🏥 Health & Monitoring:"
	@echo "  make health         - Comprehensive system health check"
	@echo "  make test-memory    - Test memory operations (write/search/forget)"
	@echo "  make test-graph     - Test graph operations (Cypher/traverse)"
	@echo "  make test-rag       - Test Graph-RAG hybrid retrieval"
	@echo ""
	@echo "🤖 Copilots & Intelligence:"
	@echo "  make copilot-test   - Test legal/ops/research copilots"
	@echo "  make ingest-demo    - Load demo data for testing"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make lint           - Run code linting (black + flake8)"
	@echo "  make test           - Run test suite"
	@echo "  make backup         - Backup Neo4j data"
	@echo "  make restore        - Restore Neo4j from backup"

up:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo "✅ Services started"
	@echo "📊 Access points:"
	@echo "   Neo4j Browser: http://localhost:7474"
	@echo "   API Server: http://localhost:8080"
	@echo "   ChromaDB: http://localhost:8000"

down:
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ Services stopped"

logs:
	@echo "📊 Service logs (Ctrl+C to exit):"
	docker-compose logs -f

install:
	@echo "🎯 Running enhanced installer..."
	bash scripts/enhanced-installer.sh

migrate-phase1:
	@echo "🚚 Migrating Phase 1 repositories..."
	python3 scripts/migration-helper.py

health:
	@echo "🏥 Running comprehensive health check..."
	python3 scripts/health-check.py

test-memory:
	@echo "🧠 Testing memory operations..."
	@curl -X POST http://localhost:8080/memory/write -H "Content-Type: application/json" \
		-d '{"content":"Test memory operation","entity":"test_entity","classification":"general"}'
	@curl -X POST http://localhost:8080/memory/search -H "Content-Type: application/json" \
		-d '{"query":"test memory","limit":5}'

test-graph:
	@echo "🔗 Testing graph operations..."
	@curl -X POST http://localhost:8080/graph/cypher -H "Content-Type: application/json" \
		-d '{"query":"MATCH (m:Memory) RETURN count(m) as memory_count"}'

test-rag:
	@echo "🎯 Testing Graph-RAG hybrid retrieval..."
	@curl -X POST http://localhost:8080/rag/hybrid -H "Content-Type: application/json" \
		-d '{"query":"Case 1FDV-23-0001009 evidence","entity":"legal_case","include_provenance":true}'

copilot-test:
	@echo "🤖 Testing domain copilots..."
	@curl -X POST http://localhost:8080/copilot/legal -H "Content-Type: application/json" \
		-d '{"task":"Draft motion summary","case":"1FDV-23-0001009","context":"TRO expiration approaching"}'

ingest-demo:
	@echo "📥 Loading demo data..."
	python3 scripts/load-demo-data.py

lint:
	@echo "🔍 Running code linting..."
	black --check . || (echo "❌ Code formatting issues found. Run: black ." && exit 1)
	flake8 . || (echo "❌ Code linting issues found" && exit 1)
	yamllint policies/ || (echo "❌ YAML linting issues found" && exit 1)
	@echo "✅ Linting passed"

test:
	@echo "🧪 Running test suite..."
	pytest tests/ -v

backup:
	@echo "💾 Backing up Neo4j data..."
	bash scripts/backup-neo4j.sh

restore:
	@echo "🔄 Restoring Neo4j from backup..."
	bash scripts/restore-neo4j.sh

# Quick deployment
deploy: install migrate-phase1 health test-memory
	@echo "🎉 DEPLOYMENT COMPLETE - System ready for operation!"
