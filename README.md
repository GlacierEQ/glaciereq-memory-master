# 🚀 glaciereq-memory-master

Sovereign memory master for GlacierEQ.

## Quickstart

```bash
docker-compose up -d
cp .env.example .env
# fill in API keys
```

## Modules
- core/memory-orchestrator
- core/master-grid
- core/constellation
- core/quantum-matrix
- graph/mem0-integration
- graph/neo4j-providers
- graph/supermemory-bridge
- graph/vector-operations
- orchestration/mcp-hub
- connectors/{google-drive, notion-engine, perplexity-bridge}
- specialized/{desktop-commander, deadline-tracker, forensic-master, docket-automation}
- api-bridges/{fileboss-bridge, omni-engine-bridge, case-matrix-bridge}

## Health
- GET /health
- GET /graph/status
- GET /memory/status
