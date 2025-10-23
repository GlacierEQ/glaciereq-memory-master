#!/usr/bin/env python3
import os, sys, requests

print("==> Health Check")

neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
print(f"Neo4j URI: {neo4j_uri}")

for env in ["SUPERMEMORY_API_KEY","MEM0_API_KEY"]:
    print(f"{env} set: {bool(os.getenv(env))}")

print("Checks complete.")
