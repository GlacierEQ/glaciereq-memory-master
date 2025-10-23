#!/usr/bin/env bash
set -euo pipefail

echo "==> Checking prerequisites"
command -v docker >/dev/null || { echo "Docker not found"; exit 1; }
command -v docker-compose >/dev/null || { echo "docker-compose not found"; exit 1; }

echo "==> Bringing up services"
docker-compose up -d

echo "==> Waiting for Neo4j"
for i in {1..30}; do
  nc -z localhost 7687 && break || sleep 2
done

echo "==> Seeding Neo4j constraints"
docker exec -i $(docker ps -qf name=neo4j) cypher-shell -u neo4j -p password "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;"
docker exec -i $(docker ps -qf name=neo4j) cypher-shell -u neo4j -p password "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;"
docker exec -i $(docker ps -qf name=neo4j) cypher-shell -u neo4j -p password "CREATE CONSTRAINT observation_id IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE;"

echo "==> Health checks"
python3 scripts/health-check.py || true

echo "✅ Installer complete"
